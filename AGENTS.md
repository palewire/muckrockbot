# Working on MuckRock Bot

## Project layout

- `muckrockbot/` contains the Click commands that download, compare, and post
  public-records requests.
- `tests/` contains command-level tests.
- `data/` contains the bot's checked-in working data. Do not delete or rewrite
  historical data unless the change specifically requires it.
- `.github/workflows/etl.yaml` runs the scheduled bot workflow.

## Development

Use Python 3.11 or newer and uv. Install developer tools with:

```sh
make install-dev
```

Run the full local quality check with `make check`, and run the test suite with
`make test`. Use `make fix` to apply Ruff's safe lint and formatting fixes.
Run individual bot commands with `make download`, `make transform`, `make tweet`,
or `make toot`.

Keep dependencies in `pyproject.toml` and refresh `uv.lock` with `uv lock` when
they change. Do not add Pipenv files.

## Safe changes

- Keep the existing package layout; this is an application, not a published
  library.
- Treat API credentials as GitHub Actions secrets or environment variables.
  Never add them to tracked files.
- Test changes to the scheduled workflow locally where possible. Do not create
  releases, tags, deployments, or external posts without explicit approval.
- Work only in the current worktree and preserve unrelated user changes.
