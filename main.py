import json
import pathlib
import re
from typing import Iterator, Optional

import bs4
import requests
import typer
from requests.adapters import HTTPAdapter
from urllib3.util import create_urllib3_context

from bandcamp_sync.album import AlbumInfo
from bandcamp_sync.downloader import Downloader
from bandcamp_sync.page import BandcampPage

cli = typer.Typer()


def get_identifier(page_url: str, sep: str = "__") -> Optional[str]:
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


def resolve_bandcamp_url(url: str, downloader: Downloader) -> Optional[str]:
    """Resolve a URL to the bandcamp.com page behind it.

    Bandcamp Pro releases are served under custom domains (e.g.
    https://shop.silentseason.com/album/...). These don't HTTP-redirect, but
    the page embeds the canonical bandcamp.com URL in its ``og:url`` meta tag.
    Returns the bandcamp.com URL, or ``None`` when there is no bandcamp page
    behind the custom domain.
    """
    if "bandcamp.com" in url:
        return url

    content = downloader.download_page(url)
    if content is None:
        print(f"Warning: could not fetch {url}, skipping")
        return None

    soup = bs4.BeautifulSoup(content, "html.parser")
    og_url = soup.find("meta", {"property": "og:url"})
    resolved = og_url.get("content") if og_url else None

    if not resolved or "bandcamp.com" not in resolved:
        print(f"Warning: no bandcamp page behind {url}, skipping")
        return None

    print(f"Resolved custom domain {url} -> {resolved}")
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

    url = resolve_bandcamp_url(url, downloader)
    if not url:
        return

    content = downloader.download_page(url)
    if content is None:
        print(f"Could not download page for {url}, skipping")
        return

    info = BandcampPage.parse_content(content)
    album_info = AlbumInfo.from_bandcamp_page(info=info, url=url)
    identifier = get_identifier(url)

    downloader.download_album_to_directory(
        album_info=album_info,
        directory=pathlib.Path(output_directory) / identifier,
    )


def read_additional_urls(path: Optional[str]) -> Iterator[str]:
    """Yield bandcamp URLs from ``path``, one per line.

    Streams the file line by line so a large list never lands in memory at
    once. Blank lines and ``#`` comments are skipped. A missing file warns and
    yields nothing.
    """
    if not path:
        return

    file = pathlib.Path(path)
    if not file.exists():
        print(f"Warning: {path} does not exist, skipping additional URLs")
        return

    with open(file, "r") as fp:
        for line in fp:
            url = line.strip()
            if url and not url.startswith("#"):
                yield url


def url_iterator(
    downloader: Downloader,
    fan_id: int,
    additional_url_file: Optional[str],
) -> Iterator[str]:
    """Lazily yield item URLs from the wishlist, then from the extra file."""
    for wishlist_item in downloader.wishlist_iterator(fan_id=fan_id):
        yield wishlist_item.get("item_url")
    yield from read_additional_urls(additional_url_file)


def process_url(
    item_url: Optional[str],
    downloader: Downloader,
    destination_folder: str,
) -> None:
    item_url = resolve_bandcamp_url(item_url, downloader)
    if not item_url:
        return

    identifier = get_identifier(item_url)
    if not identifier:
        print(f"Could not parse identifier from {item_url}, skipping")
        return

    directory_path = pathlib.Path(destination_folder) / identifier
    bandcamp_page_path = directory_path / "bandcamp_page.json"

    directory_path.mkdir(parents=True, exist_ok=True)

    bandcamp_page = None
    downloaded = False
    print(f"Downloading page metadata for {identifier} - {item_url=}")
    if bandcamp_page_path.exists():
        with open(bandcamp_page_path, "r") as fp:
            bandcamp_page = json.loads(fp.read())

    if not bandcamp_page:
        content = downloader.download_page(item_url)
        if content is None:
            print(f"Could not download page for {identifier}, skipping")
            return
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
            print(
                f"Directory {directory_path} exists, and tracks downloaded skipping..."
            )
            return

    if not downloaded:
        content = downloader.download_page(item_url)
        if content is None:
            print(f"Could not download page for {identifier}, skipping")
            return
        bandcamp_page = BandcampPage.parse_content(content)

    downloader.download_album_to_directory(
        album_info=album_info,
        directory=pathlib.Path(destination_folder) / identifier,
    )


@cli.command()
def sync(
    fan_id: int,
    destination_folder: str = "bandcamp-sync",
    additional_bandcamp_url_file: Optional[str] = typer.Option(
        None,
        help="Path to a file with extra bandcamp URLs to sync, one per line.",
    ),
) -> None:
    downloader = Downloader(session=get_session())

    for item_url in url_iterator(
        downloader, fan_id, additional_bandcamp_url_file
    ):
        process_url(item_url, downloader, destination_folder)


if __name__ == "__main__":
    cli()
