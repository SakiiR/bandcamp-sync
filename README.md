# Bandcamp Sync

Bandcamp Sync is a command-line program. It downloads albums from Bandcamp to a
local folder. It keeps the local folder the same as one or more Bandcamp
wishlists or collections.

## Who is this for

This program is for the amateur DJ. You buy or save your music on Bandcamp. You
want a clean copy of that music on your computer.

The program keeps your Bandcamp library in one local folder. Then you import
that folder into your DJ program. The program writes the correct metadata, so
rekordbox, Serato, Traktor or another DJ program reads the track information
without a problem.

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

You need the `uv` package manager. See
[docs/installation.md](docs/installation.md) to install `uv`.

With `uv`, you run the program with one command. You do not install the program
first. Run this command:

```
uvx --from git+https://github.com/SakiiR/bandcamp-sync.git bandcamp-sync --help
```

`uvx` downloads the program, runs it and then removes it. The examples below use
the short command `bandcamp-sync`. Put the `uvx --from ...` part before it each
time.

## Quick start

To download one album, run this command:

```
bandcamp-sync download https://your-artist.bandcamp.com/album/your-album
```

To sync a wishlist, you need the fan ID. Do these steps:

1. Get the fan ID for your fan page:

```
bandcamp-sync fan-id --url https://bandcamp.com/your-name
```

2. Sync the wishlist with that fan ID:

```
bandcamp-sync sync --fan-id-wishlist 123456
```

The program writes the albums to the `bandcamp-sync` folder. Then you import
this folder into your DJ program.

## Commands

| Command | Function |
| --- | --- |
| `download` | Download one album from a URL. |
| `sync` | Sync wishlists, collections and a URL file. |
| `fan-id` | Print the numeric fan ID for a fan page. |

To see all options for a command, add `--help`:

```
bandcamp-sync sync --help
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
