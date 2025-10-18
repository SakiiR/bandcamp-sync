import slugify


def slugify_presets(text: str) -> str:
    return slugify.slugify(
        text,
        lowercase=False,
        allow_unicode=True,
        replacements=[("-", " ")],
    )
