import pytest

from bandcamp_sync.slugify import slugify_presets


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        # Plain titles are left untouched.
        ("Simple Title", "Simple Title"),
        # Parentheses, dots and spaces are preserved (unlike a URL slugifier).
        ("Song (feat. X)", "Song (feat. X)"),
        # Illegal path characters are stripped.
        ("AC/DC", "ACDC"),
        ("Intro / Outro", "Intro Outro"),
        ('He said "hi"', "He said hi"),
        ("a:b*c?d|e<f>g\\h", "abcdefgh"),
        # Control characters are removed.
        ("tab\there", "tab here"),
        ("null\x00byte", "nullbyte"),
        # Whitespace runs collapse to a single space.
        ("too    many     spaces", "too many spaces"),
        ("new\nline", "new line"),
        # Leading/trailing dots and spaces are trimmed (Windows rejects them).
        ("  padded  ", "padded"),
        ("trailing dot.", "trailing dot"),
        (".hidden", "hidden"),
        # Unicode letters are preserved.
        ("Café Tacvba", "Café Tacvba"),
        ("日本語タイトル", "日本語タイトル"),
    ],
)
def test_slugify_presets(title: str, expected: str) -> None:
    assert slugify_presets(title) == expected


def test_result_contains_no_illegal_characters() -> None:
    messy = 'a/b\\c:d*e?f"g<h>i|j\x01k'
    result = slugify_presets(messy)
    assert not any(c in result for c in '<>:"/\\|?*')


def test_unicode_is_nfc_normalized() -> None:
    # "e" + combining acute accent (NFD) normalizes to the single "é" (NFC).
    decomposed = "café"
    assert slugify_presets(decomposed) == "café"
