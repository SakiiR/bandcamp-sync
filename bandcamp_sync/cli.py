import asyncio
import json
import pathlib
import re
import shutil
import ssl
from collections.abc import AsyncIterator, Iterator

import bs4
import httpx
import typer
from rich.progress import Progress

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


def get_fan_id(content: str | bytes) -> int | None:
    """Extract the numeric fan id embedded in a Bandcamp fan page.

    Fan pages carry their state in the ``#pagedata`` div's ``data-blob`` JSON;
    the id lives at ``fan_data.fan_id``. Returns ``None`` when the page has no
    such id (e.g. it is not a fan page).
    """
    soup = bs4.BeautifulSoup(content, "html.parser")
    pagedata = soup.find("div", {"id": "pagedata"})
    if not isinstance(pagedata, bs4.Tag):
        return None

    blob = pagedata.get("data-blob")
    if not isinstance(blob, str):
        return None

    try:
        data = json.loads(blob)
    except json.JSONDecodeError:
        return None

    fan_data = data.get("fan_data") or {}
    fan_id = fan_data.get("fan_id")
    return fan_id if isinstance(fan_id, int) else None


async def resolve_bandcamp_url(url: str, downloader: Downloader) -> str | None:
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
    content = await downloader.download_page(url)

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


# Bandcamp custom-domain hosts (Cloudflare / WAF) fingerprint the TLS
# handshake; pinning this cipher order makes us look like a normal browser so
# they don't answer with blanket 429s.
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


def build_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.set_ciphers(DEFAULT_CIPHERS)
    return ctx


def get_client() -> httpx.AsyncClient:
    # follow_redirects mirrors requests' default; the generous read timeout
    # keeps large track downloads from tripping httpx's 5s default.
    return httpx.AsyncClient(
        verify=build_ssl_context(),
        follow_redirects=True,
        timeout=httpx.Timeout(60.0, connect=15.0),
    )


@cli.command()
def download(url: str, output_directory: str = "bandcamp-sync") -> None:
    asyncio.run(_download(url, output_directory))


async def _download(url: str, output_directory: str) -> None:
    async with get_client() as client:
        downloader = Downloader(session=client)

        try:
            resolved = await resolve_bandcamp_url(url, downloader)
            if not resolved:
                return

            content = await downloader.download_page(resolved)
            info = BandcampPage.parse_content(content)
            album_info = AlbumInfo.from_bandcamp_page(info=info, url=resolved)
            identifier = get_identifier(resolved)
            if not identifier:
                logger.warning(
                    "Could not parse identifier from %s, skipping", resolved
                )
                return

            with make_progress() as progress:
                await downloader.download_album_to_directory(
                    album_info=album_info,
                    directory=pathlib.Path(output_directory) / identifier,
                    progress=progress,
                )
        except PageDownloadError as e:
            logger.warning("Skipping %s: %s", url, e)


@cli.command(name="fan-id")
def fan_id(
    url: str = typer.Option(
        ...,
        "--url",
        help="A Bandcamp fan page URL, e.g. https://bandcamp.com/adampits",
    ),
) -> None:
    """Print the numeric fan id for a Bandcamp fan page URL.

    Only the id is written to stdout, so it can be captured directly, e.g.
    ``--fan-id-collection "$(uv run main.py fan-id --url ...)"``.
    """
    asyncio.run(_fan_id(url))


async def _fan_id(url: str) -> None:
    async with get_client() as client:
        downloader = Downloader(session=client)
        try:
            content = await downloader.download_page(url)
        except PageDownloadError as e:
            logger.warning("Could not fetch %s: %s", url, e)
            raise typer.Exit(code=1) from e

    resolved_fan_id = get_fan_id(content)
    if resolved_fan_id is None:
        logger.warning(
            "Could not find a fan id on %s (is it a Bandcamp fan page?)", url
        )
        raise typer.Exit(code=1)

    print(resolved_fan_id)


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


async def url_iterator(
    downloader: Downloader,
    wishlist_fan_ids: list[int],
    collection_fan_ids: list[int],
    additional_url_file: str | None,
) -> AsyncIterator[str | None]:
    """Lazily yield item URLs from each requested source.

    Order: every ``--fan-id-wishlist`` wishlist, then every
    ``--fan-id-collection`` collection, then the extra URL file. Duplicates
    (the same album across several fans/sources) are yielded here and deduped
    by the caller.
    """
    for fan_id in wishlist_fan_ids:
        logger.debug("Collecting wishlist for fan_id %s", fan_id)
        async for item in downloader.wishlist_iterator(fan_id=fan_id):
            yield item.get("item_url")
    for fan_id in collection_fan_ids:
        logger.debug("Collecting collection for fan_id %s", fan_id)
        async for item in downloader.collection_iterator(fan_id=fan_id):
            yield item.get("item_url")
    for url in read_additional_urls(additional_url_file):
        yield url


async def process_url(
    item_url: str | None,
    downloader: Downloader,
    destination_folder: str,
    progress: Progress,
) -> str | None:
    """Download the album at ``item_url`` and return its on-disk identifier.

    The identifier is the name of the album's directory under
    ``destination_folder``. It is returned whenever it could be determined
    (even if the album was already fully downloaded and skipped), so callers
    can tell which directories are still "live"; ``None`` is returned when the
    URL yields no bandcamp album to sync.
    """
    if not item_url:
        return None

    item_url = await resolve_bandcamp_url(item_url, downloader)
    if not item_url:
        return None

    identifier = get_identifier(item_url)
    if not identifier:
        logger.warning("Could not parse identifier from %s, skipping", item_url)
        return None

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
        content = await downloader.download_page(item_url)
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
            return identifier

    if not downloaded:
        content = await downloader.download_page(item_url)
        bandcamp_page = BandcampPage.parse_content(content)

    await downloader.download_album_to_directory(
        album_info=album_info,
        directory=pathlib.Path(destination_folder) / identifier,
        progress=progress,
    )
    return identifier


def prune_orphan_albums(
    destination_folder: str,
    live_identifiers: set[str],
) -> None:
    """Delete album directories that no longer belong to any synced source.

    ``live_identifiers`` is the set of album directory names produced by this
    run. Any direct subdirectory of ``destination_folder`` not in that set is
    an orphan (e.g. a collection whose fan id was dropped from the command)
    and is removed.
    """
    base = pathlib.Path(destination_folder)
    if not base.exists():
        return

    for child in sorted(base.iterdir()):
        if not child.is_dir() or child.name in live_identifiers:
            continue
        logger.warning(
            "Removing orphan album %s (no longer in any provided source)",
            child,
        )
        shutil.rmtree(child)


@cli.command()
def sync(
    fan_id_wishlist: list[int] = typer.Option(
        [],
        "--fan-id-wishlist",
        help="Fan id whose wishlist to sync. Repeat for several fans.",
    ),
    fan_id_collection: list[int] = typer.Option(
        [],
        "--fan-id-collection",
        help="Fan id whose collection (purchased items) to sync. Repeat for "
        "several fans.",
    ),
    remove_orphan_albums: bool = typer.Option(
        False,
        "--remove-orphan-albums",
        help="After syncing, delete locally downloaded albums that are no "
        "longer part of any provided wishlist/collection. Skipped if any item "
        "failed this run, to avoid deleting albums when a source was only "
        "partially fetched.",
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
    max_concurrency: int = typer.Option(
        4,
        help="How many albums to download in parallel. Higher is faster but "
        "more likely to trip Bandcamp's rate limiting (HTTP 429).",
    ),
) -> None:
    if not (fan_id_wishlist or fan_id_collection or additional_bandcamp_url_file):
        logger.warning(
            "Nothing to sync: pass at least one --fan-id-wishlist, "
            "--fan-id-collection or --additional-bandcamp-url-file."
        )
        raise typer.Exit(code=1)

    asyncio.run(
        _sync(
            fan_id_wishlist=fan_id_wishlist,
            fan_id_collection=fan_id_collection,
            remove_orphan_albums=remove_orphan_albums,
            destination_folder=destination_folder,
            additional_bandcamp_url_file=additional_bandcamp_url_file,
            rate_limit_wait=rate_limit_wait,
            max_rate_limit_retries=max_rate_limit_retries,
            max_concurrency=max_concurrency,
        )
    )


async def _sync(
    fan_id_wishlist: list[int],
    fan_id_collection: list[int],
    remove_orphan_albums: bool,
    destination_folder: str,
    additional_bandcamp_url_file: str | None,
    rate_limit_wait: float,
    max_rate_limit_retries: int,
    max_concurrency: int,
) -> None:
    async with get_client() as client:
        downloader = Downloader(
            session=client,
            rate_limit_wait=rate_limit_wait,
            max_rate_limit_retries=max_rate_limit_retries,
        )

        # Album directories that still belong to a source this run; used to
        # prune orphans. Failures are counted so we can refuse to prune when
        # the source list may be incomplete. The event loop is single-threaded,
        # so these shared mutations across concurrent workers need no locking.
        live_identifiers: set[str] = set()
        failures = 0

        with make_progress() as progress:
            # Enumerate every source first so the overall bar has a real album
            # count and percentage. The total still grows while we are
            # discovering: start indeterminate, then lock it in once collected.
            overall = progress.add_task(
                "[bold]Collecting sources…", total=None, show_count=True
            )
            urls: list[str] = []
            seen: set[str] = set()
            async for url in url_iterator(
                downloader,
                fan_id_wishlist,
                fan_id_collection,
                additional_bandcamp_url_file,
            ):
                # The same album can appear in several fans'
                # wishlists/collections; collect (and later download) it once.
                if not url or url in seen:
                    continue
                seen.add(url)
                urls.append(url)
                progress.update(overall, total=len(urls))
            progress.update(overall, description="[bold]Syncing", total=len(urls))

            if not urls:
                logger.warning(
                    "Nothing to sync: the requested wishlist(s)/collection(s) "
                    "are empty (and no additional URLs were given). "
                    "Double-check the fan ids."
                )
                return

            # Bound how many albums download at once: the request rate — not
            # Python — is what Bandcamp throttles, so more than a handful in
            # flight just trips 429s.
            semaphore = asyncio.Semaphore(max_concurrency)

            async def worker(item_url: str) -> None:
                nonlocal failures
                async with semaphore:
                    try:
                        identifier = await process_url(
                            item_url,
                            downloader,
                            destination_folder,
                            progress=progress,
                        )
                        if identifier:
                            live_identifiers.add(identifier)
                    except PageDownloadError as e:
                        # Expected, recoverable: a page wouldn't download. Skip.
                        failures += 1
                        logger.warning("Skipping %s: %s", item_url, e)
                    except Exception as e:
                        # Anything else unexpected (malformed metadata, I/O
                        # errors, ...) still must not abort the rest of the run.
                        failures += 1
                        logger.warning("Failed to process %s: %s", item_url, e)
                    finally:
                        progress.advance(overall)

            await asyncio.gather(*(worker(item_url) for item_url in urls))

    if remove_orphan_albums:
        if failures:
            logger.warning(
                "Skipping orphan removal: %d item(s) failed this run, so the "
                "live album list may be incomplete and pruning could delete "
                "albums that are still wanted.",
                failures,
            )
        else:
            prune_orphan_albums(destination_folder, live_identifiers)


if __name__ == "__main__":
    cli()
