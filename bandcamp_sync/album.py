from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import List, Optional

from bandcamp_sync.typing import BandcampPageInfo, TrackinfoJson


@dataclass
class TrackInfo:
    duration: float
    number: int
    title: str
    url: Optional[str]

    @classmethod
    def from_track_info_json(cls, info: TrackinfoJson) -> TrackInfo:
        url = None
        file_info = info.get("file")
        if file_info and "mp3-128" in file_info:
            mp3_128 = file_info["mp3-128"]
            if "https" in mp3_128:
                url = mp3_128
            else:
                url = "http:" + mp3_128

        return cls(
            duration=info.get("duration"),
            number=info.get("track_num"),
            title=info.get("title"),
            url=url,
        )


@dataclass
class AlbumInfo:
    title: str
    artist: str
    art: str
    release_date: str
    label: Optional[str]
    all_tracks_available: bool
    genres: List[str]
    tracks: List[TrackInfo]

    @classmethod
    def get_album_release_date(cls, info: BandcampPageInfo) -> str:
        def fmt(date_str: str) -> Optional[str]:
            return str(
                datetime.datetime.strptime(date_str, "%d %b %Y %H:%M:%S GMT").year
            )

        album_release = info["album_release_date"]
        if album_release is not None:
            return fmt(album_release)
        album_release = info["current"]["release_date"]
        if album_release is not None:
            return fmt(album_release)
        album_release = info["embed_info"]["item_public"]
        return fmt(album_release)

    @classmethod
    def get_album_title(cls, info: BandcampPageInfo) -> str:
        try:
            return info["current"]["title"]
        except KeyError:
            return info["trackinfo"][0]["title"]

    @classmethod
    def get_album_label(cls, info: BandcampPageInfo) -> Optional[str]:
        try:
            return info["item_sellers"][str(info["current"]["selling_band_id"])]["name"]
        except KeyError:
            return None

    @classmethod
    def from_bandcamp_page(cls, info: BandcampPageInfo, url: str) -> AlbumInfo:
        tracks_json = info.get("trackinfo")
        artist = info.get("artist")
        art = info.get("image")
        genres = info.get("keywords", [])
        label = cls.get_album_label(info=info)

        all_tracks_available = all(map(lambda x: bool(x["file"]), tracks_json))

        tracks = [
            TrackInfo.from_track_info_json(info=track_info)
            for track_info in tracks_json
        ]

        for track in tracks:
            track.title = track.title.replace(f"{artist} - ", "", 1)

        return cls(
            title=cls.get_album_title(info=info),
            label=label,
            release_date=cls.get_album_release_date(info=info),
            artist=artist,
            art=art,
            all_tracks_available=all_tracks_available,
            genres=genres,
            tracks=tracks,
        )
