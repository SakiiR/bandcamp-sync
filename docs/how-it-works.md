# How it works

This page describes how Bandcamp Sync works.

## The sync steps

The `sync` command does these steps:

1. It collects the album URLs from each source. The order is the wishlists,
   then the collections, then the URL file.
2. It removes the duplicate URLs. The same album can be in more than one
   source. The program downloads the album one time.
3. It downloads the albums. It downloads several albums at the same time.
4. It removes the orphan albums. This step is optional.

## The album folder

The program writes each album to its own folder. The folder name is an
identifier. The program makes the identifier from the URL. The identifier has
the artist name, the page type and the album name.

Each album folder has these files:

- The MP3 file for each track.
- The cover art image.
- A `bandcamp_page.json` file with the page metadata.

The program writes the metadata into each MP3 file. The metadata includes the
title, the artist, the album, the date, the genres and the cover art.

The MP3 file name has the track number and the track title. The program makes
the track title safe for a file name. It removes the characters that a file
system does not allow.

## The cache

The program keeps a cache to make the sync incremental. The cache is the set of
album folders on disk.

For each album, the program does this check:

- It counts the MP3 files in the album folder.
- It counts the tracks that are available on the page.
- It skips the album when the two numbers are the same.

The program downloads only the new albums or the albums that are not complete.
The `bandcamp_page.json` file holds the saved metadata, so the program does not
download the page again when the album is already present.

## Custom domains

Some Bandcamp Pro releases use a custom domain. An example is
`https://shop.example.com/album/...`. A custom domain does not send an HTTP
redirect to Bandcamp.

The program reads the page from the custom domain. The page has the Bandcamp
URL in the `og:url` meta tag. The program uses this URL to find the Bandcamp
page.

The program gives a warning and skips the URL when it does not find a Bandcamp
page behind the custom domain.

## Rate limit control

Bandcamp limits the request rate. The server answers with the HTTP 429 status
when you send too many requests.

The program controls the rate in these ways:

- It limits the number of parallel downloads. The `--max-concurrency` option
  sets this number.
- It waits after an HTTP 429 response. The wait becomes longer after each try.
  This method is a backoff.
- It uses the `Retry-After` header when the server sends one. If not, it uses
  the `--rate-limit-wait` value.
- It tries a request again up to the `--max-rate-limit-retries` number. Then it
  stops for that request.

The program also sets a browser-like TLS cipher order. Some custom-domain hosts
examine the TLS handshake. This cipher order helps to prevent an immediate 429.

## Orphan albums

An orphan album is a local album that is no longer in a source. An example is a
collection that you removed from the command.

The `--remove-orphan-albums` option removes the orphan albums after the sync.
The program compares the local folders with the albums from this run. It deletes
each folder that is not in this run.

The program does not remove orphan albums when one or more items failed in the
run. A failure can mean an incomplete source list. The program keeps the
albums to prevent the loss of wanted albums.

## Errors

The program raises a `PageDownloadError` when a page does not download. The
program catches this error for each item. It gives a warning and continues with
the next item. One failed item does not stop the full run.
