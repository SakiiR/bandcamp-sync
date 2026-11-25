import re
import unicodedata

# Characters that are illegal in filenames on Windows, macOS or Linux, plus
# ASCII control characters.
_ILLEGAL = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def slugify_presets(text: str) -> str:
    """Turn a track title into a filesystem-safe filename component.

    Keeps the title as close to the original as possible: it only drops
    characters that are illegal in a path, collapses runs of whitespace and
    trims trailing dots/spaces (which Windows rejects).
    """
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s+", " ", text)  # fold tabs/newlines into spaces first
    text = _ILLEGAL.sub("", text)
    text = re.sub(r"\s+", " ", text)  # collapse gaps left by removed characters
    return text.strip(" .")
