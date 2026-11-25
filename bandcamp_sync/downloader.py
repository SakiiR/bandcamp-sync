import pathlib
import time
from collections.abc import Generator
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any

import requests
from mutagen import id3, mp3
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    Task,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.table import Column
from rich.text import Text

from bandcamp_sync.album import AlbumInfo, TrackInfo
from bandcamp_sync.exceptions import PageDownloadError
from bandcamp_sync.log import console, get_logger
from bandcamp_sync.slugify import slugify_presets
from bandcamp_sync.typing import BandcampWishlistItem

logger = get_logger(__name__)

# Maximum attempts for a single track before we give up and move on.
MAX_TRACK_RETRIES = 3

# Fixed-width description column: long URLs/titles are truncated with an
# ellipsis so the bar and the numbers to its right stay put instead of
# jittering every time the current item changes.
_DESC_COLUMN = Column(width=48, no_wrap=True, overflow="ellipsis")


class _AlbumCountColumn(MofNCompleteColumn):
    """``completed/total`` count, but only for tasks that opt in.

    Rendered for the album-level bars (where the count means "albums"), and
    blank for per-track byte bars whose raw byte counts would otherwise churn
    every chunk and shift the columns to the right.
    """

    def render(self, task: Task) -> Text:
        if not task.fields.get("show_count"):
            return Text("")
        return super().render(task)

# A real browser User-Agent. Bandcamp custom-domain hosts (Cloudflare / WAF)
# answer unknown/placeholder agents with blanket HTTP 429s, so identify as a
# normal browser.
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def make_progress() -> Progress:
    """A Rich progress display shared across the whole run.

    Using one instance (and one shared console) keeps the overall sync bar,
    the per-album bar and the per-track byte bar in a single live display.
    """
    return Progress(
        SpinnerColumn(),
        TextColumn(
            "[progress.description]{task.description}",
            table_column=_DESC_COLUMN,
        ),
        BarColumn(bar_width=30),
        TaskProgressColumn(table_column=Column(justify="right", width=4)),
        _AlbumCountColumn(table_column=Column(justify="right", width=9)),
        TimeRemainingColumn(),
        console=console,
    )


class Downloader:
    _session: requests.Session
    _headers: dict[str, str]
    _chunk_size: int

    def __init__(
        self,
        session: requests.Session | None = None,
        rate_limit_wait: float = 30.0,
        max_rate_limit_retries: int = 5,
    ):
        self._session = session or requests.Session()
        self._headers = {"User-Agent": DEFAULT_USER_AGENT}
        self._chunk_size = 1024
        # Rate-limit (HTTP 429) handling: base back-off used when the server
        # gives no ``Retry-After``, and how many times to retry a single
        # request before giving up on it.
        self._rate_limit_wait = rate_limit_wait
        self._max_rate_limit_retries = max_rate_limit_retries

    def _backoff_seconds(self, response: requests.Response, attempt: int) -> float:
        """How long to wait before retry ``attempt`` (1-based) of a 429.

        Starts from the server's ``Retry-After`` (or ``rate_limit_wait`` when
        absent) and grows exponentially per attempt, so a host that keeps
        replying with the same small ``Retry-After`` gets progressively more
        breathing room instead of being hammered every few seconds.
        """
        return self._retry_after_seconds(response) * (2 ** (attempt - 1))

    def _rate_limit_details(self, response: requests.Response) -> str:
        """A compact string of whatever the server told us about the 429."""
        parts = []
        for header in ("Retry-After", "X-RateLimit-Remaining", "X-RateLimit-Reset"):
            value = response.headers.get(header)
            if value:
                parts.append(f"{header}={value}")
        body = (response.text or "").strip()
        if body:
            parts.append(f"body={body[:200]!r}")
        return "; ".join(parts) if parts else "no details in response"

    def _retry_after_seconds(self, response: requests.Response) -> float:
        """Seconds to wait, honoring ``Retry-After`` (secs or HTTP-date)."""
        retry_after = response.headers.get("Retry-After")
        if retry_after:
            try:
                return max(0.0, float(retry_after))
            except ValueError:
                try:
                    when = parsedate_to_datetime(retry_after)
                    return max(
                        0.0,
                        (when - datetime.now(UTC)).total_seconds(),
                    )
                except (TypeError, ValueError):
                    pass
        return self._rate_limit_wait

    def _fancollection_items_request(
        self,
        endpoint: str,
        fan_id: int,
        count: int = 200,
        older_than_token: str | None = None,
    ) -> dict[str, Any] | None:
        """One page of a fan's wishlist or collection.

        ``endpoint`` is the fancollection resource (``wishlist_items`` or
        ``collection_items``); both take the same POST body and return the same
        ``items``/``more_available``/``last_token`` shape.
        """
        label = endpoint.removesuffix("_items")
        try:
            response = self._session.post(
                f"https://bandcamp.com/api/fancollection/1/{endpoint}",
                json={
                    "count": count,
                    "fan_id": fan_id,
                    "older_than_token": older_than_token or "99999999999:a:b::",
                },
                headers=self._headers,
            )

            if response.status_code == 429:
                wait = self._retry_after_seconds(response)
                logger.warning(
                    "%s request rate-limited (HTTP 429, %s); "
                    "waiting %.0fs before retrying",
                    label.capitalize(),
                    self._rate_limit_details(response),
                    wait,
                )
                time.sleep(wait)
                return None
            if response.status_code != 200:
                logger.warning(
                    "%s request failed with unexpected HTTP %s, skipping "
                    "this batch",
                    label.capitalize(),
                    response.status_code,
                )
                return None
            return response.json()
        except requests.RequestException as e:
            logger.warning("Request error while fetching %s: %s", label, e)
            return None

    def _fancollection_iterator(
        self,
        endpoint: str,
        fan_id: int,
        count: int = 200,
    ) -> Generator[BandcampWishlistItem]:
        label = endpoint.removesuffix("_items")
        more_available = True
        older_than_token = None
        failures = 0

        while more_available:
            json_data = self._fancollection_items_request(
                endpoint=endpoint,
                fan_id=fan_id,
                count=count,
                older_than_token=older_than_token,
            )
            if not json_data:
                failures += 1
                if failures >= self._max_rate_limit_retries:
                    logger.warning(
                        "Giving up on the %s after %d failed requests",
                        label,
                        failures,
                    )
                    return
                logger.debug(
                    "Empty/failed %s response, retrying in 5s (%d/%d)...",
                    label,
                    failures,
                    self._max_rate_limit_retries,
                )
                time.sleep(5)
                continue

            failures = 0
            more_available = json_data.get("more_available") or False
            older_than_token = json_data.get("last_token") or None

            yield from json_data.get("items") or []

    def wishlist_iterator(
        self,
        fan_id: int,
        count: int = 200,
    ) -> Generator[BandcampWishlistItem]:
        yield from self._fancollection_iterator(
            endpoint="wishlist_items", fan_id=fan_id, count=count
        )

    def collection_iterator(
        self,
        fan_id: int,
        count: int = 200,
    ) -> Generator[BandcampWishlistItem]:
        yield from self._fancollection_iterator(
            endpoint="collection_items", fan_id=fan_id, count=count
        )

    def download_page(self, url: str) -> bytes:
        """Fetch ``url`` and return its body.

        Raises :class:`PageDownloadError` (never returns empty) for any
        abnormal outcome — redirect loops, HTTP/transport errors, exhausted
        rate-limit retries or an empty response body — so callers can warn and
        skip instead of silently carrying on with nothing.
        """
        for attempt in range(1, self._max_rate_limit_retries + 1):
            try:
                response = self._session.get(url, headers=self._headers)
            except requests.exceptions.TooManyRedirects as e:
                raise PageDownloadError(f"too many redirects for {url}") from e
            except requests.RequestException as e:
                raise PageDownloadError(
                    f"request error for {url}: {e}"
                ) from e

            if response.status_code == 429:
                wait = self._backoff_seconds(response, attempt)
                logger.warning(
                    "Rate-limited fetching %s (HTTP 429, %s); waiting %.0fs "
                    "(attempt %d/%d)",
                    url,
                    self._rate_limit_details(response),
                    wait,
                    attempt,
                    self._max_rate_limit_retries,
                )
                time.sleep(wait)
                continue

            if not response.content:
                raise PageDownloadError(
                    f"empty response body for {url} "
                    f"(HTTP {response.status_code})"
                )
            return response.content

        raise PageDownloadError(
            f"gave up on {url} after {self._max_rate_limit_retries} "
            f"rate-limit retries (HTTP 429)"
        )

    def _download_art(self, art_url: str, directory: pathlib.Path) -> None:
        response = self._session.get(url=art_url, headers=self._headers)

        with open(directory, "wb") as fp:
            fp.write(response.content)

        logger.debug("Downloaded art to %s", directory)

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
        progress: Progress,
        directory: pathlib.Path,
        album_info: AlbumInfo,
        track_info: TrackInfo,
        art_path: pathlib.Path,
        attempt: int = 1,
    ) -> None:
        if track_info.url is None:
            # Callers already filter these out; guard anyway for type safety.
            return

        mp3_filename = (
            f"{track_info.number or 1:03d} - {slugify_presets(track_info.title)}.mp3"
        )
        track_outdir = directory / mp3_filename

        logger.debug("Downloading track %s", mp3_filename)

        response = self._session.get(
            track_info.url, headers=self._headers, stream=True
        )
        content_type = response.headers.get("content-type") or "unknown"
        if "text/html" in content_type:
            logger.warning(
                "Track '%s' is not available for download: server returned an "
                "HTML page (content-type %s) instead of audio, skipping",
                track_info.title,
                content_type,
            )
            return

        total = int(response.headers.get("content-length") or 0)
        task = progress.add_task(
            f"  [green]{mp3_filename}", total=total or None
        )
        try:
            with open(track_outdir, "wb+") as fp:
                for chunk in response.iter_content(chunk_size=self._chunk_size):
                    fp.write(chunk)
                    progress.advance(task, len(chunk))
        finally:
            progress.remove_task(task)

        if total and (
            not track_outdir.exists() or track_outdir.stat().st_size != total
        ):
            if attempt >= MAX_TRACK_RETRIES:
                logger.warning(
                    "Giving up on track '%s': download still incomplete "
                    "(%d/%d bytes) after %d attempts",
                    track_info.title,
                    track_outdir.stat().st_size if track_outdir.exists() else 0,
                    total,
                    attempt,
                )
                return
            logger.warning(
                "Incomplete download for '%s' (got %d/%d bytes), retrying in "
                "5s (attempt %d/%d)...",
                track_info.title,
                track_outdir.stat().st_size if track_outdir.exists() else 0,
                total,
                attempt,
                MAX_TRACK_RETRIES,
            )
            time.sleep(5)
            self._download_track(
                progress=progress,
                directory=directory,
                album_info=album_info,
                track_info=track_info,
                art_path=art_path,
                attempt=attempt + 1,
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
        progress: Progress,
        album_task: TaskID,
        album_info: AlbumInfo,
        directory: pathlib.Path,
        art_path: pathlib.Path,
    ) -> None:
        for track_info in album_info.tracks:
            if not track_info.url:
                continue
            try:
                self._download_track(
                    progress=progress,
                    directory=directory,
                    album_info=album_info,
                    track_info=track_info,
                    art_path=art_path,
                )
            except Exception as e:
                # A single bad track (HTTP error, redirect loop, broken
                # metadata, ...) must never abort the whole album.
                logger.warning(
                    "Failed to download track '%s': %s", track_info.title, e
                )
            finally:
                progress.advance(album_task)

    def download_album_to_directory(
        self,
        album_info: AlbumInfo,
        directory: pathlib.Path,
        progress: Progress,
    ) -> None:
        logger.debug(
            "Downloading %s - %s to %s",
            album_info.artist,
            album_info.title,
            directory,
        )
        directory.mkdir(parents=True, exist_ok=True)

        art_path = directory / "cover.jpg"
        try:
            self._download_art(album_info.art, directory=art_path)
        except Exception as e:
            logger.warning(
                "Could not download cover art for '%s': %s", album_info.title, e
            )

        downloadable = [track for track in album_info.tracks if track.url]

        album_task = progress.add_task(
            f"[cyan]{album_info.artist} - {album_info.title}",
            total=len(downloadable),
            show_count=True,
        )
        try:
            self._download_tracks(
                progress=progress,
                album_task=album_task,
                album_info=album_info,
                directory=directory,
                art_path=art_path,
            )
        finally:
            progress.remove_task(album_task)
