import json
from typing import Any, cast

import bs4

from bandcamp_sync.log import get_logger
from bandcamp_sync.typing import BandcampPageInfo

logger = get_logger(__name__)


class BandcampPage:
    @staticmethod
    def parse_content(content: str | bytes) -> BandcampPageInfo:
        soup = bs4.BeautifulSoup(content, "html.parser")

        page_data: dict[str, Any] = {}

        try:
            pagedata = soup.find("div", {"id": "pagedata"})
            if isinstance(pagedata, bs4.Tag):
                blob = pagedata.get("data-blob")
                if isinstance(blob, str):
                    page_data = {**page_data, **json.loads(blob)}

            ld_json = soup.find("script", {"type": "application/ld+json"})
            if isinstance(ld_json, bs4.Tag) and ld_json.string:
                page_data = {**page_data, **json.loads(ld_json.string)}

            key = "data-tralbum"
            for item in soup.find_all("script"):
                json_data = item.get(key) if isinstance(item, bs4.Tag) else None
                if isinstance(json_data, str):
                    page_data = {**page_data, **json.loads(json_data)}
        except Exception as e:
            logger.warning(
                "Failed to extract some bandcamp page data (%s); returning the "
                "partial data parsed so far",
                e,
            )

        return cast(BandcampPageInfo, page_data)
