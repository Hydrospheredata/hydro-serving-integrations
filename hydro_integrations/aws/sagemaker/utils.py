import urllib.parse


def validate_non_empty_uri(
        uri: str,
        require_schema: bool,
        require_netloc: bool,
        require_path: bool
):
    """ Validate uri for non-empty schema/netloc/path. """
    parse = urllib.parse.urlparse(uri)
    if require_schema:
        assert parse.scheme, f"Schema should be provided for {uri}"
    if require_netloc:
        assert parse.netloc, f"Netloc should be provided for {uri}"
    if require_path:
        assert parse.path.strip("/"), f"Path should be provided for {uri}"
