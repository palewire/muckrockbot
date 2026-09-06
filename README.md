A Fediverse robot account that posts the latest public records requests filed and completed at muckrock.com at [mastodon.palewi.re/@muckrockbot](https://mastodon.palewi.re/@muckrockbot).

## Development

This project uses Python 3.11 or newer and [uv](https://docs.astral.sh/uv/) for
dependencies.

```sh
make install-dev
make check
make test
```

Use `make fix` to apply safe lint and formatting changes. The scheduled
workflow uses `make download`, `make transform`, and `make toot`.

## MuckRock API migration

The current download command uses MuckRock's retired v1 client interface. A
production move to API v2 is intentionally paused: v2 requires a bot account
with JWT authentication and does not provide the public author name or
`noindex` visibility information that this bot needs to preserve its existing
posts and public-only feed. Do not update `python-muckrock` beyond `0.1.1` or
enable v2 downloads until MuckRock provides supported access to those fields.

Tests use fake API responses and temporary data directories. They never call
MuckRock or post to social accounts.
