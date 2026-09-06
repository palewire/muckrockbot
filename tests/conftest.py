"""Keep command and client tests independent of real services and credentials."""

import pytest
import requests


@pytest.fixture(autouse=True)
def isolate_external_services(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove real credentials and block unmocked HTTP requests.

    Args:
        monkeypatch: Pytest helper for restoring patched objects and environment.

    Returns:
        None. Each test must supply synthetic credentials and HTTP responses.

    Example:
        Pytest applies this fixture automatically to every test.
    """

    def fail_outbound_request(*args: object, **kwargs: object) -> requests.Response:
        """Reject an unmocked HTTP operation.

        Args:
            *args: Positional transport arguments.
            **kwargs: Keyword transport arguments.

        Returns:
            This function does not return.

        Raises:
            AssertionError: Always, to prevent access to external services.

        Example:
            An unmocked ``requests.get(url)`` fails rather than accessing the API.
        """
        raise AssertionError("Tests must explicitly mock HTTP requests.")

    monkeypatch.delenv("MUCKROCK_API_TOKEN", raising=False)
    monkeypatch.delenv("MUCKROCK_PUBLIC_FEED_APPROVED", raising=False)
    monkeypatch.setattr(requests, "get", fail_outbound_request)
    monkeypatch.setattr(requests.sessions.Session, "send", fail_outbound_request)
