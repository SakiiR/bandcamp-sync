import pathlib
import time
from typing import Any, Dict, Generator, Optional

import requests
from mutagen import id3, mp3
from tqdm import tqdm

from bandcamp_sync.album import AlbumInfo, TrackInfo
from bandcamp_sync.slugify import slugify_presets
from bandcamp_sync.typing import BandcampWishlistItem


class Downloader:
    _session = requests.Session
    _headers: Dict[str, str]
    _chunk_size: int

    def __init__(self, session: Optional[requests.Session] = None):
        self._session = session or requests.Session()
        self._headers = {"User-Agent": "..."}
        self._chunk_size = 1024

    def _wishlist_items_request_httpx(
        self,
        fan_id: int,
        count: int = 200,
        older_than_token: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        try:
            response = self._session.post(
                "https://bandcamp.com/api/fancollection/1/wishlist_items",
                json={
                    "count": count,
                    "fan_id": fan_id,
                    "older_than_token": older_than_token or "99999999999:a:b::",
                },
                headers=self._headers,
            )

            if response.status_code != 200:
                return None
            return response.json()
        except requests.RequestException as e:
            print(f"Request error: {e}")
            return None

    def wishlist_iterator(
        self,
        fan_id: int,
        count: int = 200,
    ) -> Generator[BandcampWishlistItem, None, None]:

        more_available = True
        older_than_token = None

        while more_available:
            json_data = self._wishlist_items_request_httpx(
                fan_id=fan_id,
                count=count,
                older_than_token=older_than_token,
            )
            if not json_data:
                print("Retrying...")
                time.sleep(5)
                continue

            more_available = json_data.get("more_available") or False
            older_than_token = json_data.get("last_token") or None

            for item in json_data.get("items") or []:
                yield item
        return None

    def download_page(self, url: str) -> Optional[bytes]:
        try:
            return self._session.get(url, headers=self._headers).content
        except requests.exceptions.TooManyRedirects:
            print(f"Too many redirects for {url}, skipping")
            return None
        except requests.RequestException as e:
            print(f"Request error for {url}: {e}, skipping")
            return None

    def _download_art(self, art_url: str, directory: pathlib.Path) -> None:
        response = self._session.get(url=art_url, headers=self._headers)

        with open(directory, "wb") as fp:
            fp.write(response.content)

        print(f"Downloaded art to {directory}")

    def _write_mp3_meta(
        self,
        track_outdir: pathlib.Path,
        album_info: AlbumInfo,
        track_info: TrackInfo,
        art_path: pathlib.Path,
    ) -> None:
        track_absolute_path = track_outdir.absolute()

        audio = mp3.MP3(track_absolute_path)
        audio.delete()
        audio["TIT2"] = id3._frames.TIT2(encoding=3, text=["title"])
        audio.save(filename=None, v1=2)

        audio = mp3.MP3(track_absolute_path)

        audio["TIT1"] = id3._frames.TIT1(encoding=3, text=album_info.label)

        with open(art_path, "rb") as art_fp:
            cover_bytes = art_fp.read()
            audio["APIC"] = id3._frames.APIC(
                encoding=3,
                mime="image/jpeg",
                type=3,
                desc="Cover",
                data=cover_bytes,
            )
        audio["TCON"] = id3._frames.TCON(encoding=3, text=album_info.genres)
        audio.save()

        audio = mp3.EasyMP3(track_absolute_path)

        audio["tracknumber"] = str(track_info.number)
        audio["artist"] = album_info.artist
        audio["title"] = track_info.title
        audio["albumartist"] = album_info.artist
        audio["album"] = album_info.title
        audio["date"] = album_info.release_date
        audio.save()

    def _download_track(
        self,
        directory: pathlib.Path,
        album_info: AlbumInfo,
        track_info: TrackInfo,
        art_path: pathlib.Path,
    ) -> None:
        mp3_filename = (
            f"{track_info.number or 1:03d} - {slugify_presets(track_info.title)}.mp3"
        )
        track_outdir = directory / mp3_filename

        print(f"Downloading track {mp3_filename}")

        with tqdm(total=None, unit="B", unit_scale=True) as progress_bar:
            fp = open(track_outdir, "wb+")
            response = self._session.get(
                track_info.url, headers=self._headers, stream=True
            )
            if "text/html" in response.headers.get("content-type"):
                print(f"File not available : {response.content}")
                return None
            total = int(response.headers["content-length"])
            progress_bar.total = total
            for chunk in response.iter_content(chunk_size=self._chunk_size):
                progress_bar.update(len(chunk))
                fp.write(chunk)
            fp.close()

            if not track_outdir.exists() or not track_outdir.stat().st_size == total:
                print("Failure, retrying in 5sec...")
                time.sleep(5)
                self._download_track(
                    directory=directory,
                    album_info=album_info,
                    track_info=track_info,
                    art_path=art_path,
                )
                return

        self._write_mp3_meta(
            track_outdir=track_outdir,
            album_info=album_info,
            track_info=track_info,
            art_path=art_path,
        )

    def _download_tracks(
        self,
        album_info: AlbumInfo,
        directory: pathlib.Path,
        art_path: pathlib.Path,
    ) -> None:
        for track_info in album_info.tracks:
            if not track_info.url:
                continue
            self._download_track(
                directory=directory,
                album_info=album_info,
                track_info=track_info,
                art_path=art_path,
            )

    def download_album_to_directory(
        self,
        album_info: AlbumInfo,
        directory: pathlib.Path,
    ) -> None:
        print(f"Downloading {album_info.artist} - {album_info.title} to {directory}")
        directory.mkdir(parents=True, exist_ok=True)
        art_path = directory / "cover.jpg"
        self._download_art(
            album_info.art,
            directory=art_path,
        )
        self._download_tracks(
            album_info=album_info,
            directory=directory,
            art_path=art_path,
        )
