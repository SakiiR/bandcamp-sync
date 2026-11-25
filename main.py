import json
import pathlib
import re
from collections.abc import Iterator

import bs4
import requests
import typer
from requests.adapters import HTTPAdapter
from rich.progress import Progress
from urllib3.util import create_urllib3_context

from bandcamp_sync.album import AlbumInfo
from bandcamp_sync.downloader import Downloader, make_progress
from bandcamp_sync.exceptions import PageDownloadError
from bandcamp_sync.log import get_logger, setup_logging
from bandcamp_sync.page import BandcampPage

cli = typer.Typer()

logger = get_logger(__name__)


@cli.callback()
def main(
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable maximum (DEBUG) logging. Without it, only warnings, "
        "errors and the progress bar are shown.",
    ),
) -> None:
    setup_logging(debug=debug)


def get_identifier(page_url: str, sep: str = "__") -> str | None:
    regex = (
        r"https:\/\/([\w\-]+)\.bandcamp\.com\/(album|track)\/([\w\-]+)"
        if "bandcamp.com" in page_url
        else r"https:\/\/([\w\-]+)\.\w+\/(album|track)\/([\w\-]+)"
    )

    matches = re.findall(
        regex,
        page_url,
    )
    if not matches:
        return None

    name, page_type, object = matches[0]

    return sep.join([name, page_type, object])


def resolve_bandcamp_url(url: str, downloader: Downloader) -> str | None:
    """Resolve a URL to the bandcamp.com page behind it.

    Bandcamp Pro releases are served under custom domains (e.g.
    https://shop.silentseason.com/album/...). These don't HTTP-redirect, but
    the page embeds the canonical bandcamp.com URL in its ``og:url`` meta tag.
    Returns the bandcamp.com URL, or ``None`` when there is no bandcamp page
    behind the custom domain.
    """
    if "bandcamp.com" in url:
        return url

    # download_page raises PageDownloadError on any abnormal outcome; let it
    # propagate to the per-item boundary (sync loop / download command).
    content = downloader.download_page(url)

    soup = bs4.BeautifulSoup(content, "html.parser")
    og_url = soup.find("meta", {"property": "og:url"})
    resolved = og_url.get("content") if isinstance(og_url, bs4.Tag) else None

    if not isinstance(resolved, str) or "bandcamp.com" not in resolved:
        logger.warning(
            "No bandcamp.com og:url found on %s (custom domain has no bandcamp "
            "page behind it), skipping",
            url,
        )
        return None

    logger.debug("Resolved custom domain %s -> %s", url, resolved)
    return resolved


class SSLAdapter(HTTPAdapter):
    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs["ssl_context"] = self.ssl_context
        return super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        kwargs["ssl_context"] = self.ssl_context
        return super().proxy_manager_for(*args, **kwargs)


# Create the SSL context with the custom ciphers
ctx = create_urllib3_context()
ctx.load_default_certs()

DEFAULT_CIPHERS = ":".join(
    [
        "ECDHE+AESGCM",
        "ECDHE+CHACHA20",
        "DHE+AESGCM",
        "DHE+CHACHA20",
        "ECDH+AESGCM",
        "DH+AESGCM",
        "ECDH+AES",
        "DH+AES",
        "RSA+AESGCM",
        "RSA+AES",
        "!aNULL",
        "!eNULL",
        "!MD5",
        "!DSS",
        "!AESCCM",
    ]
)
ctx.set_ciphers(DEFAULT_CIPHERS)


def get_session() -> requests.Session:
    session = requests.Session()
    adapter = SSLAdapter(ssl_context=ctx)
    session.mount("https://", adapter)
    return session


@cli.command()
def download(url: str, output_directory: str = "bandcamp-sync") -> None:
    downloader = Downloader(session=get_session())

    try:
        resolved = resolve_bandcamp_url(url, downloader)
        if not resolved:
            return

        content = downloader.download_page(resolved)
        info = BandcampPage.parse_content(content)
        album_info = AlbumInfo.from_bandcamp_page(info=info, url=resolved)
        identifier = get_identifier(resolved)
        if not identifier:
            logger.warning("Could not parse identifier from %s, skipping", resolved)
            return

        with make_progress() as progress:
            downloader.download_album_to_directory(
                album_info=album_info,
                directory=pathlib.Path(output_directory) / identifier,
                progress=progress,
            )
    except PageDownloadError as e:
        logger.warning("Skipping %s: %s", url, e)


def read_additional_urls(path: str | None) -> Iterator[str]:
    """Yield bandcamp URLs from ``path``, one per line.

    Streams the file line by line so a large list never lands in memory at
    once. Blank lines and ``#`` comments are skipped. A missing file warns and
    yields nothing.
    """
    if not path:
        return

    file = pathlib.Path(path)
    if not file.exists():
        logger.warning("%s does not exist, skipping additional URLs", path)
        return

    with open(file) as fp:
        for line in fp:
            url = line.strip()
            if url and not url.startswith("#"):
                yield url


def url_iterator(
    downloader: Downloader,
    fan_ids: list[int],
    additional_url_file: str | None,
) -> Iterator[str]:
    """Lazily yield item URLs from each fan's wishlist, then the extra file."""
    for fan_id in fan_ids:
        logger.debug("Collecting wishlist for fan_id %s", fan_id)
        for wishlist_item in downloader.wishlist_iterator(fan_id=fan_id):
            yield wishlist_item.get("item_url")
    yield from read_additional_urls(additional_url_file)


def process_url(
    item_url: str | None,
    downloader: Downloader,
    destination_folder: str,
    progress: Progress,
) -> None:
    if not item_url:
        return

    item_url = resolve_bandcamp_url(item_url, downloader)
    if not item_url:
        return

    identifier = get_identifier(item_url)
    if not identifier:
        logger.warning("Could not parse identifier from %s, skipping", item_url)
        return

    directory_path = pathlib.Path(destination_folder) / identifier
    bandcamp_page_path = directory_path / "bandcamp_page.json"

    directory_path.mkdir(parents=True, exist_ok=True)

    bandcamp_page = None
    downloaded = False
    logger.debug("Downloading page metadata for %s - %s", identifier, item_url)
    if bandcamp_page_path.exists():
        with open(bandcamp_page_path) as fp:
            bandcamp_page = json.loads(fp.read())

    if not bandcamp_page:
        content = downloader.download_page(item_url)
        bandcamp_page = BandcampPage.parse_content(content)
        with open(bandcamp_page_path, "w") as fp:
            fp.write(json.dumps(bandcamp_page))
        downloaded = True

    album_info = AlbumInfo.from_bandcamp_page(
        info=bandcamp_page,
        url=item_url,
    )

    if directory_path.exists():
        downloaded_tracks_count = len(list(directory_path.glob("*.mp3")))
        actual_available_track_count = len(
            list(filter(lambda track: track.url, album_info.tracks))
        )
        if downloaded_tracks_count == actual_available_track_count:
            logger.debug(
                "Directory %s exists and all tracks downloaded, skipping",
                directory_path,
            )
            return

    if not downloaded:
        content = downloader.download_page(item_url)
        bandcamp_page = BandcampPage.parse_content(content)

    downloader.download_album_to_directory(
        album_info=album_info,
        directory=pathlib.Path(destination_folder) / identifier,
        progress=progress,
    )


@cli.command()
def sync(
    fan_ids: list[int] = typer.Argument(
        ...,
        help="One or more Bandcamp fan ids whose wishlists to sync.",
    ),
    destination_folder: str = "bandcamp-sync",
    additional_bandcamp_url_file: str | None = typer.Option(
        None,
        help="Path to a file with extra bandcamp URLs to sync, one per line.",
    ),
    rate_limit_wait: float = typer.Option(
        30.0,
        help="Seconds to back off on HTTP 429 when the server sends no "
        "Retry-After header.",
    ),
    max_rate_limit_retries: int = typer.Option(
        5,
        help="How many times to retry a single rate-limited (429) request "
        "before giving up on it.",
    ),
) -> None:
    downloader = Downloader(
        session=get_session(),
        rate_limit_wait=rate_limit_wait,
        max_rate_limit_retries=max_rate_limit_retries,
    )

    with make_progress() as progress:
        # Enumerate the wishlist (+ extra URLs) first so the overall bar has a
        # real album count and percentage. The total still grows while we are
        # discovering: start indeterminate, then lock it in once collected.
        overall = progress.add_task(
            "[bold]Collecting wishlist…", total=None, show_count=True
        )
        urls: list[str] = []
        seen: set[str] = set()
        for url in url_iterator(downloader, fan_ids, additional_bandcamp_url_file):
            # An album wished by several of the given fans appears once per
            # fan; collect it a single time.
            if url in seen:
                continue
            seen.add(url)
            urls.append(url)
            progress.update(overall, total=len(urls))
        progress.update(
            overall, description="[bold]Syncing wishlist", total=len(urls)
        )

        if not urls:
            logger.warning(
                "Nothing to sync for fan_ids %s: the wishlist(s) are empty (and "
                "no additional URLs were given). Double-check the fan ids.",
                fan_ids,
            )
            return

        for item_url in urls:
            progress.update(overall, description=f"[bold]Syncing {item_url}")
            try:
                process_url(
                    item_url, downloader, destination_folder, progress=progress
                )
            except PageDownloadError as e:
                # Expected, recoverable: a page wouldn't download. Skip it.
                logger.warning("Skipping %s: %s", item_url, e)
            except Exception as e:
                # Anything else unexpected (malformed metadata, I/O errors, ...)
                # still must not abort the rest of the wishlist.
                logger.warning("Failed to process %s: %s", item_url, e)
            finally:
                progress.advance(overall)


if __name__ == "__main__":
    cli()
