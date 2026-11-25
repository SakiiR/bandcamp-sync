# Usage

This page tells you how to use each command. The examples use the
`bandcamp-sync` command.

You run the `bandcamp-sync` command in one of these ways:

- Install the command with `uv tool install bandcamp-sync`. Then run
  `bandcamp-sync` directly.
- Run the command with `uvx`. You write `uvx bandcamp-sync` before the
  arguments.
- From the source code, you replace `bandcamp-sync` with `uv run main.py`. See
  [Development](development.md).

See [Installation](installation.md) for more information.

## Global option

The `--debug` option turns on the maximum log level. Put the option before the
command name.

```
bandcamp-sync --debug sync --fan-id-wishlist 123456
```

Without `--debug`, the program shows only the progress bar, the warnings and
the errors.

## The download command

The `download` command downloads one album from a URL.

Syntax:

```
bandcamp-sync download URL [OUTPUT_DIRECTORY]
```

Arguments:

| Argument | Required | Default | Function |
| --- | --- | --- | --- |
| `URL` | Yes | — | The album or track URL on Bandcamp. |
| `OUTPUT_DIRECTORY` | No | `bandcamp-sync` | The folder for the album. |

Example:

```
bandcamp-sync download https://your-artist.bandcamp.com/album/your-album
```

The command accepts a custom domain URL. The program finds the Bandcamp page
behind the custom domain. See [How it works](how-it-works.md).

## The fan-id command

The `fan-id` command prints the numeric fan ID for a Bandcamp fan page. You
need the fan ID for the `sync` command.

Syntax:

```
bandcamp-sync fan-id --url URL
```

Example:

```
bandcamp-sync fan-id --url https://bandcamp.com/your-name
```

The command writes only the number to the output. You can put the number
directly into another command:

```
bandcamp-sync sync --fan-id-collection "$(bandcamp-sync fan-id --url https://bandcamp.com/your-name)"
```

## The sync command

The `sync` command downloads albums from one or more sources. It keeps the
local folder the same as those sources.

Syntax:

```
bandcamp-sync sync [OPTIONS] [DESTINATION_FOLDER]
```

You must give at least one source. A source is a wishlist, a collection or a
URL file.

### Options

| Option | Default | Function |
| --- | --- | --- |
| `--fan-id-wishlist` | — | Sync the wishlist for this fan ID. Repeat the option for more fans. |
| `--fan-id-collection` | — | Sync the collection for this fan ID. Repeat the option for more fans. |
| `--additional-bandcamp-url-file` | — | The path to a file with extra album URLs. |
| `--remove-orphan-albums` | off | Remove local albums that are no longer in a source. |
| `--rate-limit-wait` | `30.0` | The wait in seconds after an HTTP 429 with no `Retry-After` header. |
| `--max-rate-limit-retries` | `5` | The number of retries for one rate-limited request. |
| `--max-concurrency` | `4` | The number of albums to download at the same time. |
| `DESTINATION_FOLDER` | `bandcamp-sync` | The folder for the albums. |

### Examples

Sync one wishlist:

```
bandcamp-sync sync --fan-id-wishlist 123456
```

Sync two wishlists and one collection:

```
bandcamp-sync sync --fan-id-wishlist 123456 --fan-id-wishlist 654321 --fan-id-collection 123456
```

Sync a wishlist and remove old albums:

```
bandcamp-sync sync --fan-id-wishlist 123456 --remove-orphan-albums
```

### The URL file

The URL file has one Bandcamp URL on each line. The program reads the file line
by line. The program ignores a blank line. The program ignores a line that
starts with `#`.

Example file:

```
# My extra albums
https://artist-one.bandcamp.com/album/first-album
https://artist-two.bandcamp.com/album/second-album
```

Use the file with this option:

```
bandcamp-sync sync --additional-bandcamp-url-file urls.txt
```

### A note on concurrency

The `--max-concurrency` option sets the number of parallel downloads. A high
number is faster. A high number also causes more HTTP 429 errors from Bandcamp.
Keep the number low when you get many 429 errors.

## Get help for a command

Add `--help` to any command:

```
bandcamp-sync download --help
```
