import json
import pathlib
import re
from typing import Optional

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

    name, page_type, object = re.findall(
        regex,
        page_url,
    )[0]

    return sep.join([name, page_type, object])


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

    info = BandcampPage.parse_content(downloader.download_page(url))
    album_info = AlbumInfo.from_bandcamp_page(info=info, url=url)
    identifier = get_identifier(url)

    downloader.download_album_to_directory(
        album_info=album_info,
        directory=pathlib.Path(output_directory) / identifier,
    )


@cli.command()
def sync(
    fan_id: int,
    destination_folder: str = "bandcamp-sync",
) -> None:
    downloader = Downloader(session=get_session())

    for wishlist_item in downloader.wishlist_iterator(fan_id=fan_id):
        item_url = wishlist_item.get("item_url")
        identifier = get_identifier(item_url)
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
            bandcamp_page = BandcampPage.parse_content(
                downloader.download_page(item_url)
            )
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
                continue

        if not downloaded:
            bandcamp_page = BandcampPage.parse_content(
                downloader.download_page(item_url)
            )

        downloader.download_album_to_directory(
            album_info=album_info,
            directory=pathlib.Path(destination_folder) / identifier,
        )


if __name__ == "__main__":
    cli()
