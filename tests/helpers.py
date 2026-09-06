"""Synthetic MuckRock responses shared by offline tests."""

import json

import requests


def make_response(
    payload: object, status_code: int = 200, raw_content: bytes | None = None
) -> requests.Response:
    """Build an in-memory HTTP response.

    Args:
        payload: JSON value used when no raw content is supplied.
        status_code: HTTP status attached to the response.
        raw_content: Optional raw response bytes, such as invalid JSON.

    Returns:
        A response that supports normal Requests status and JSON handling.

    Example:
        ``make_response({"results": []})``.
    """
    response = requests.Response()
    response.status_code = status_code
    response.url = "https://www.muckrock.com/api_v1/foia"
    response.headers["Content-Type"] = "application/json"
    response._content = (
        raw_content if raw_content is not None else json.dumps(payload).encode()
    )
    return response


def request_row(
    request_id: int, *, completed: bool = False, **overrides: object
) -> dict[str, object]:
    """Build a public request fixture.

    Args:
        request_id: Positive request identifier.
        completed: Whether to create a completed request.
        **overrides: Values that replace standard fixture fields.

    Returns:
        A JSON-compatible public request record.

    Example:
        ``request_row(7, completed=True)``.
    """
    row: dict[str, object] = {
        "id": request_id,
        "title": "Request title",
        "username": "public-requester",
        "absolute_url": f"https://www.muckrock.com/foi/example/request-{request_id}/",
        "status": "done" if completed else "submitted",
        "embargo_status": "public",
        "datetime_submitted": "2026-09-01T12:00:00+00:00",
    }
    if completed:
        row["datetime_done"] = "2026-09-02T12:00:00+00:00"
    row.update(overrides)
    return row
