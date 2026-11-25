# Bandcamp Sync

Bandcamp Sync is a command-line program. It downloads albums from Bandcamp to a
local folder. It keeps the local folder the same as one or more Bandcamp
wishlists or collections.

The program writes each album to its own folder. It adds the cover art and the
track metadata to each MP3 file.

The program keeps a cache. On the next run, it downloads only the new albums. It
does not download an album again when the album is already complete on disk.

## What the program does

- It downloads one album from a URL.
- It downloads all albums in a fan wishlist.
- It downloads all albums in a fan collection.
- It reads extra album URLs from a file.
- It removes local albums that are no longer in a source. This step is optional.
- It finds the numeric fan ID for a Bandcamp fan page.

## Requirements

- Python 3.13 or higher.
- The `uv` package manager. See [docs/installation.md](docs/installation.md).

## Installation

1. Install `uv`.
2. Open a terminal in the project folder.
3. Run this command:

```
uv sync
```

The command installs all dependencies.

## Quick start

To download one album, run this command:

```
uv run main.py download https://your-artist.bandcamp.com/album/your-album
```

To sync a wishlist, you need the fan ID. Do these steps:

1. Get the fan ID for your fan page:

```
uv run main.py fan-id --url https://bandcamp.com/your-name
```

2. Sync the wishlist with that fan ID:

```
uv run main.py sync --fan-id-wishlist 123456
```

The program writes the albums to the `bandcamp-sync` folder.

## Commands

| Command | Function |
| --- | --- |
| `download` | Download one album from a URL. |
| `sync` | Sync wishlists, collections and a URL file. |
| `fan-id` | Print the numeric fan ID for a fan page. |

To see all options for a command, add `--help`:

```
uv run main.py sync --help
```

## Documentation

The `docs` folder has more information:

- [docs/index.md](docs/index.md) — the documentation index.
- [docs/installation.md](docs/installation.md) — how to install the program.
- [docs/usage.md](docs/usage.md) — how to use each command.
- [docs/how-it-works.md](docs/how-it-works.md) — how the program works.
- [docs/development.md](docs/development.md) — how to work on the code.

## Development

Run the program from the source code:

```
uv run main.py --help
```

For the full developer information, see
[docs/development.md](docs/development.md).

---

The documentation uses ASD-STE100 Simplified Technical English.
