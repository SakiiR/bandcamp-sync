import json
import logging

import bs4

from src.typing import BandcampPageInfo

logger = logging.getLogger()


class BandcampPage:
    @staticmethod
    def parse_content(content: str) -> BandcampPageInfo:
        soup = bs4.BeautifulSoup(content, "html.parser")

        page_data = {}

        try:
            page_data = {
                **page_data,
                **json.loads(soup.find("div", {"id": "pagedata"})["data-blob"]),
            }

            page_data = {
                **page_data,
                **json.loads(
                    soup.find("script", {"type": "application/ld+json"}).string
                ),
            }

            key = "data-tralbum"
            for item in filter(lambda x: x.get(key), soup.find_all("script")):
                json_data = item.get(key)
                page_data = {**page_data, **json.loads(json_data)}
        except Exception as e:
            print(e)
            return page_data

        return page_data
