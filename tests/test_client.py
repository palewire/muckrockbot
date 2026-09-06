"""Offline regression tests for authenticated MuckRock v1 downloads."""

import pytest
import requests

from muckrockbot import client
from tests.helpers import make_response, request_row


@pytest.mark.parametrize(
    ("method", "expected_params"),
    [
        (
            "submitted",
            {
                "ordering": "-datetime_submitted",
                "has_datetime_submitted": 2,
                "has_datetime_done": 1,
                "embargo_status": "public",
                "page_size": 50,
            },
        ),
        (
            "completed",
            {
                "ordering": "-datetime_done",
                "has_datetime_submitted": 1,
                "has_datetime_done": 2,
                "status": "done",
                "embargo_status": "public",
                "page_size": 50,
            },
        ),
    ],
)
def test_legacy_filter_encodes_public_feed_queries(
    method: str, expected_params: dict[str, str | int], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Use the inherited filter encoding with the hardened v1 transport.

    Args:
        method: Public feed method to call.
        expected_params: Exact query encoding expected from the legacy filter.
        monkeypatch: Pytest helper for replacing the request seam.

    Returns:
        None. Assertions confirm query, headers, and timeout values.

    Example:
        Run with ``pytest tests/test_client.py::test_legacy_filter_encodes_public_feed_queries``.
    """
    calls: list[tuple[str, dict[str, object]]] = []
    completed = method == "completed"

    def capture_get(url: str, **kwargs: object) -> requests.Response:
        """Capture one expected legacy request and return a valid page.

        Args:
            url: Requested endpoint URL.
            **kwargs: Request arguments passed by the client.

        Returns:
            A synthetic one-record response.

        Example:
            ``capture_get("https://www.muckrock.com/api_v1/foia")``.
        """
        calls.append((url, kwargs))
        return make_response({"results": [request_row(1, completed=completed)]})

    monkeypatch.setattr(client.requests, "get", capture_get)

    records = getattr(client.PublicFoiaClient("test-token"), method)()

    assert records[0]["id"] == 1
    assert calls == [
        (
            "https://www.muckrock.com/api_v1/foia",
            {
                "params": expected_params,
                "headers": {
                    "Authorization": "Token test-token",
                    "User-Agent": client.PublicFoiaClient.USER_AGENT,
                    "Accept": "application/json",
                },
                "timeout": 20,
            },
        )
    ]


@pytest.mark.parametrize("records", [[], [request_row(1)]])
def test_client_accepts_empty_and_short_public_pages(
    records: list[dict[str, object]], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Accept valid first pages that contain fewer than the requested 50 records.

    Args:
        records: Valid result rows for the synthetic page.
        monkeypatch: Pytest helper for replacing the request seam.

    Returns:
        None. Assertions confirm valid responses are returned unchanged.

    Example:
        Run with ``pytest tests/test_client.py::test_client_accepts_empty_and_short_public_pages``.
    """
    monkeypatch.setattr(
        client.requests,
        "get",
        lambda *args, **kwargs: make_response({"results": records}),
    )

    assert client.PublicFoiaClient("test-token").submitted() == records


def test_client_ignores_next_page_link(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Download only the initial 50-record page even when a next link is supplied.

    Args:
        monkeypatch: Pytest helper for replacing the request seam.

    Returns:
        None. Assertions confirm no second request is issued.

    Example:
        Run with ``pytest tests/test_client.py::test_client_ignores_next_page_link``.
    """
    calls = 0
    rows = [request_row(index) for index in range(50, 0, -1)]

    def page_with_next(url: str, **kwargs: object) -> requests.Response:
        """Return one page that advertises a next URL.

        Args:
            url: Requested endpoint URL.
            **kwargs: Request arguments passed by the client.

        Returns:
            A synthetic response containing a ``next`` link.

        Example:
            ``page_with_next("https://www.muckrock.com/api_v1/foia")``.
        """
        nonlocal calls
        calls += 1
        return make_response(
            {
                "next": "https://www.muckrock.com/api_v1/foia?page=2",
                "results": rows,
            }
        )

    monkeypatch.setattr(client.requests, "get", page_with_next)

    assert client.PublicFoiaClient("test-token").submitted() == rows
    assert calls == 1


@pytest.mark.parametrize(
    ("payload", "raw_content", "expected_message"),
    [
        ({}, None, "missing a results list"),
        ({"results": {}}, None, "missing a results list"),
        (None, b"<html>login page</html>", "invalid JSON"),
    ],
)
def test_client_rejects_invalid_response_envelopes(
    payload: object,
    raw_content: bytes | None,
    expected_message: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject missing results lists and non-JSON response bodies safely.

    Args:
        payload: JSON payload for the response.
        raw_content: Optional invalid response content.
        expected_message: Safe error text expected from the client.
        monkeypatch: Pytest helper for replacing the request seam.

    Returns:
        None. Assertions confirm response bodies are not exposed.

    Example:
        Run with ``pytest tests/test_client.py::test_client_rejects_invalid_response_envelopes``.
    """
    monkeypatch.setattr(
        client.requests,
        "get",
        lambda *args, **kwargs: make_response(payload, raw_content=raw_content),
    )

    with pytest.raises(client.DownloadError, match=expected_message) as error:
        client.PublicFoiaClient("test-token").submitted()

    assert "login page" not in str(error.value)


@pytest.mark.parametrize(
    ("status_code", "expected_message"),
    [
        (401, "rejected access"),
        (403, "rejected access"),
        (404, "HTTP 404"),
        (429, "rate limit"),
        (500, "HTTP 500"),
    ],
)
def test_client_reports_safe_http_errors(
    status_code: int, expected_message: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Convert API HTTP failures into messages that expose no response details.

    Args:
        status_code: Synthetic HTTP response status.
        expected_message: Safe error text expected from the client.
        monkeypatch: Pytest helper for replacing the request seam.

    Returns:
        None. Assertions confirm status-specific safe errors are raised.

    Example:
        Run with ``pytest tests/test_client.py::test_client_reports_safe_http_errors``.
    """
    monkeypatch.setattr(
        client.requests,
        "get",
        lambda *args, **kwargs: make_response(
            {"detail": "token-secret and response body must not be shown"}, status_code
        ),
    )

    with pytest.raises(client.DownloadError, match=expected_message) as error:
        client.PublicFoiaClient("test-token").submitted()

    assert "token-secret" not in str(error.value)


def test_client_reports_timeout_without_network_details(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Convert transport failures to a generic actionable download error.

    Args:
        monkeypatch: Pytest helper for replacing the request seam.

    Returns:
        None. Assertions confirm timeout internals are not exposed.

    Example:
        Run with ``pytest tests/test_client.py::test_client_reports_timeout_without_network_details``.
    """

    def raise_timeout(*args: object, **kwargs: object) -> requests.Response:
        """Raise a synthetic timeout from the request seam.

        Args:
            *args: Positional arguments passed to ``requests.get``.
            **kwargs: Keyword arguments passed to ``requests.get``.

        Returns:
            This function does not return.

        Raises:
            requests.Timeout: Always.

        Example:
            ``raise_timeout()``.
        """
        raise requests.Timeout("private connection detail")

    monkeypatch.setattr(client.requests, "get", raise_timeout)

    with pytest.raises(client.DownloadError, match="Could not reach MuckRock") as error:
        client.PublicFoiaClient("test-token").submitted()

    assert "private connection detail" not in str(error.value)


def test_client_rejects_pages_larger_than_fifty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject a response that violates the one-page record limit.

    Args:
        monkeypatch: Pytest helper for replacing the request seam.

    Returns:
        None. Assertions confirm oversized pages are not accepted.

    Example:
        Run with ``pytest tests/test_client.py::test_client_rejects_pages_larger_than_fifty``.
    """
    rows = [request_row(index) for index in range(1, 52)]
    monkeypatch.setattr(
        client.requests, "get", lambda *args, **kwargs: make_response({"results": rows})
    )

    with pytest.raises(client.DownloadError, match="more than the requested 50"):
        client.PublicFoiaClient("test-token").submitted()


@pytest.mark.parametrize(
    "field", ["title", "username", "absolute_url", "status", "datetime_submitted"]
)
def test_client_rejects_missing_required_submitted_fields(
    field: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reject submitted rows that omit a required public snapshot field.

    Args:
        field: Required field removed from the valid fixture.
        monkeypatch: Pytest helper for replacing the request seam.

    Returns:
        None. Assertions confirm the field-specific validation failure.

    Example:
        Run with ``pytest tests/test_client.py::test_client_rejects_missing_required_submitted_fields``.
    """
    row = request_row(1)
    row.pop(field)
    monkeypatch.setattr(
        client.requests,
        "get",
        lambda *args, **kwargs: make_response({"results": [row]}),
    )

    with pytest.raises(client.DownloadError, match=f"valid {field}"):
        client.PublicFoiaClient("test-token").submitted()


@pytest.mark.parametrize(
    ("row", "method", "expected_message"),
    [
        ("not a request object", "submitted", "not an object"),
        (request_row(1, id=True), "submitted", "valid integer ID"),
        (request_row(1, id="1"), "submitted", "valid integer ID"),
        (request_row(0), "submitted", "valid integer ID"),
        (request_row(1, username=" "), "submitted", "valid username"),
        (request_row(1, embargo_status="private"), "submitted", "non-public"),
        (request_row(1, embargo_status=None), "submitted", "non-public"),
        (
            request_row(1, datetime_submitted=None),
            "submitted",
            "valid datetime_submitted",
        ),
        (
            request_row(1, datetime_submitted="yesterday"),
            "submitted",
            "invalid request date or URL",
        ),
        (
            request_row(1, absolute_url="https://example.com/foi/request"),
            "submitted",
            "outside its public site",
        ),
        (
            request_row(1, completed=True, status="processing"),
            "completed",
            "status done",
        ),
        (
            request_row(1, completed=True, datetime_done=None),
            "completed",
            "valid datetime_done",
        ),
    ],
)
def test_client_rejects_malformed_or_nonpublic_records(
    row: object,
    method: str,
    expected_message: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject malformed IDs, public status violations, invalid links, and bad dates.

    Args:
        row: Synthetic invalid result row.
        method: Feed method through which to validate the row.
        expected_message: Validation text expected from the client.
        monkeypatch: Pytest helper for replacing the request seam.

    Returns:
        None. Assertions confirm invalid rows cannot become snapshots.

    Example:
        Run with ``pytest tests/test_client.py::test_client_rejects_malformed_or_nonpublic_records``.
    """
    monkeypatch.setattr(
        client.requests,
        "get",
        lambda *args, **kwargs: make_response({"results": [row]}),
    )

    with pytest.raises(client.DownloadError, match=expected_message):
        getattr(client.PublicFoiaClient("test-token"), method)()


def test_client_rejects_duplicate_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reject a first page containing the same request identifier twice.

    Args:
        monkeypatch: Pytest helper for replacing the request seam.

    Returns:
        None. Assertions confirm duplicate records are not returned.

    Example:
        Run with ``pytest tests/test_client.py::test_client_rejects_duplicate_ids``.
    """
    monkeypatch.setattr(
        client.requests,
        "get",
        lambda *args, **kwargs: make_response(
            {"results": [request_row(1), request_row(1, title="Repeated")]}
        ),
    )

    with pytest.raises(client.DownloadError, match="duplicate request IDs"):
        client.PublicFoiaClient("test-token").submitted()


def test_client_drops_authenticated_only_top_level_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keep existing snapshot fields while removing account-only response metadata.

    Args:
        monkeypatch: Pytest helper for replacing the request seam.

    Returns:
        None. Assertions confirm private top-level fields never leave the client.

    Example:
        Run with ``pytest tests/test_client.py::test_client_drops_authenticated_only_top_level_fields``.
    """
    row = request_row(
        1,
        agency="Example agency",
        tags=["transparency"],
        notes="private note",
        email="private@example.com",
        mail_id=3,
        read_collaborators=["staff"],
        edit_collaborators=["staff"],
    )
    monkeypatch.setattr(
        client.requests,
        "get",
        lambda *args, **kwargs: make_response({"results": [row]}),
    )

    records = client.PublicFoiaClient("test-token").submitted()

    assert records == [
        {
            key: value
            for key, value in row.items()
            if key
            not in {
                "notes",
                "email",
                "mail_id",
                "read_collaborators",
                "edit_collaborators",
            }
        }
    ]
