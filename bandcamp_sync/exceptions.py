class BandcampSyncError(Exception):
    """Base class for expected, recoverable bandcamp-sync failures.

    These are raised for conditions we know how to skip over (a page that
    won't download, an empty response, ...) so callers can catch them and warn
    instead of crashing the whole run.
    """


class PageDownloadError(BandcampSyncError):
    """A page could not be downloaded or came back with no usable content.

    Covers redirect loops, HTTP errors, exhausted rate-limit retries and empty
    response bodies. The message describes the concrete reason.
    """
