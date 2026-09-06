A Fediverse robot account that posts the latest public records requests filed
at muckrock.com at [mastodon.palewi.re/@muckrockbot](https://mastodon.palewi.re/@muckrockbot).
It also saves completed-request snapshots, but does not post them.

## Development

This project uses Python 3.11 or newer and [uv](https://docs.astral.sh/uv/) for
dependencies.

```sh
make install-dev
make check
make test
```

Use `make fix` to apply safe lint and formatting changes. Tests use fake API
responses and temporary data directories. They never call MuckRock or post to
social accounts.

## Restore authenticated downloads

API v1 remains available with a legacy API token. The bot intentionally uses
`python-muckrock==0.1.1` to preserve its request filters, author credits and
links. Obtain your token from MuckRock through a secure channel and save it
as the `MUCKROCK_API_TOKEN` GitHub Actions secret. Do not put tokens in files,
command arguments, logs or commits.

For local use, supply the same environment variable through your secret
manager. Then check authentication and both response shapes without saving
anything or posting:

```sh
uv run python -m muckrockbot.download --check
```

Downloads request one page of up to 50 public records per feed, ordered newest
first. Submitted requests must have a submission date. Completed requests must
have a completion date and status `done`. Both feeds are validated before any
snapshots are written; invalid credentials, HTTP failures and malformed
responses fail the command rather than replacing good data with an error.
This is not a historical download or recovery system: requests outside the
latest 50 can be missed between runs.

### Public-record approval and restarting posts

Authentication changes which records the API can return. The bot explicitly
requests and checks `embargo_status=public` and excludes authenticated-only
account fields from snapshots. However, v1 does not identify public records
marked `noindex`, which were excluded from the previous anonymous feed.
Token access alone does **not** resolve that difference.

Until you approve including all records marked public, or MuckRock provides
a supported way to preserve the old exclusions, leave the repository variable
`MUCKROCK_PUBLIC_FEED_APPROVED` unset. Scheduled runs will only perform the
read-only check: no snapshots, commits, transformations or social posts.

If you explicitly approve the broader public feed, restart in this order:

1. Run the **Extract, transform and alert** workflow manually with `baseline`
   selected. This acknowledges the visibility difference, saves a current
   snapshot, and never sends posts. It avoids announcing the entire newest
   page after the bot's downtime. Wait for that run to finish successfully.
2. Set the GitHub Actions **repository variable** `MUCKROCK_PUBLIC_FEED_APPROVED`
   to the exact value `true`. Subsequent scheduled runs download, compare,
   post to Mastodon and commit snapshots. Twitter remains disabled.

Unset that variable to return to read-only checks. If preserving the old
`noindex` exclusions is required, do not select `baseline` or enable the
variable; resolve the API limitation with the maintainer first.

Local snapshot writing also requires explicit approval:

```sh
uv run python -m muckrockbot.download --allow-public-feed --data-dir /tmp/muckrockbot
```

This saves data but does not post. Use a fresh temporary directory for manual
experiments rather than changing the checked-in snapshots.

## Later API v2 migration

A production move to API v2 remains separate: v2 requires a bot account
with JWT authentication and does not provide the public author name or
`noindex` visibility information that this bot needs to preserve its existing
posts and public-only feed. Do not update `python-muckrock` beyond `0.1.1` or
enable v2 downloads until MuckRock provides supported access to those fields.
