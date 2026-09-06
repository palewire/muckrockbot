"""Authenticated, public-only downloads through MuckRock's v1 client."""

from datetime import datetime
from typing import ClassVar
from urllib.parse import urlsplit

import requests
from muckrock import FoiaEndpoint

RequestRecord = dict[str, object]


class DownloadError(ValueError):
    """A download failed without producing a usable snapshot."""


class PublicFoiaClient(FoiaEndpoint):
    """Keep legacy query encoding while validating HTTP responses and records."""

    USER_AGENT = "muckrockbot (https://github.com/palewire/muckrockbot)"
    SNAPSHOT_FIELDS: ClassVar[tuple[str, ...]] = (
        "id",
        "title",
        "username",
        "absolute_url",
        "user",
        "agency",
        "slug",
        "status",
        "embargo_status",
        "datetime_submitted",
        "datetime_done",
        "datetime_updated",
        "date_due",
        "date_embargo",
        "date_followup",
        "days_until_due",
        "disable_autofollowups",
        "price",
        "tracking_id",
        "tags",
        "communications",
    )

    def __init__(self, token: str) -> None:
        """Create a client using a legacy API token.

        Args:
            token: Token supplied through the MUCKROCK_API_TOKEN environment variable.

        Returns:
            None.

        Raises:
            DownloadError: The token is empty or contains invalid header characters.

        Example:
            ``client = PublicFoiaClient(token_from_environment)``
        """
        if not token.strip() or any(character in token for character in "\r\n"):
            raise DownloadError("Set MUCKROCK_API_TOKEN to a valid legacy API token.")
        super().__init__(token=token.strip())

    def submitted(self) -> list[RequestRecord]:
        """Fetch the first page of submitted public requests.

        Args:
            None.

        Returns:
            At most 50 JSON-compatible requests, newest first.

        Raises:
            DownloadError: The download or response validation fails.

        Example:
            ``submitted = client.submitted()``
        """
        return self.filter(ordering="-datetime_submitted", has_datetime_submitted=True)

    def completed(self) -> list[RequestRecord]:
        """Fetch the first page of successfully completed public requests.

        Args:
            None.

        Returns:
            At most 50 JSON-compatible requests with status ``done``, newest first.

        Raises:
            DownloadError: The download or response validation fails.

        Example:
            ``completed = client.completed()``
        """
        return self.filter(
            ordering="-datetime_done", has_datetime_done=True, status="done"
        )

    def _get_request(
        self,
        url: str,
        params: dict[str, str | int] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, list[RequestRecord]]:
        """Replace the legacy transport's unchecked JSON response.

        Args:
            url: Legacy endpoint URL supplied by FoiaEndpoint.
            params: Query parameters already encoded by the legacy client.
            headers: Additional HTTP headers supplied by the legacy client.

        Returns:
            A results envelope containing validated snapshot records.

        Raises:
            DownloadError: Authentication, HTTP, JSON, or record validation fails.

        Example:
            ``client.submitted()`` calls this transport through ``filter()``.
        """
        query = {**(params or {}), "embargo_status": "public", "page_size": 50}
        request_headers = {
            **(headers or {}),
            "Authorization": f"Token {self.token}",
            "User-Agent": self.USER_AGENT,
            "Accept": "application/json",
        }
        try:
            response = requests.get(
                url, params=query, headers=request_headers, timeout=20
            )
            response.raise_for_status()
        except requests.HTTPError as error:
            status = error.response.status_code if error.response is not None else None
            if status in (401, 403):
                raise DownloadError(
                    "MuckRock rejected access. Check MUCKROCK_API_TOKEN; "
                    "if it is valid, contact MuckRock about the access restriction."
                ) from None
            if status == 429:
                raise DownloadError(
                    "MuckRock's rate limit was reached. Wait before trying again."
                ) from None
            raise DownloadError(f"MuckRock returned HTTP {status}.") from None
        except requests.RequestException:
            raise DownloadError(
                "Could not reach MuckRock within the request timeout. Try again later."
            ) from None

        try:
            payload = response.json()
        except ValueError:
            raise DownloadError(
                "MuckRock returned invalid JSON, not a results page."
            ) from None
        if not isinstance(payload, dict) or not isinstance(
            payload.get("results"), list
        ):
            raise DownloadError("MuckRock's response is missing a results list.")
        if len(payload["results"]) > 50:
            raise DownloadError("MuckRock returned more than the requested 50 records.")

        date_field = (
            "datetime_done"
            if query.get("ordering") == "-datetime_done"
            else "datetime_submitted"
        )
        records = [
            self._validate_record(item, date_field) for item in payload["results"]
        ]
        ids = [record["id"] for record in records]
        if len(set(ids)) != len(ids):
            raise DownloadError("MuckRock returned duplicate request IDs.")
        return {"results": records}

    def _validate_record(self, item: object, date_field: str) -> RequestRecord:
        """Validate a public request and exclude authenticated-only metadata.

        Args:
            item: A decoded JSON result.
            date_field: Timestamp required for the requested feed.

        Returns:
            The request's existing snapshot fields, without private account metadata.

        Raises:
            DownloadError: A required field, public status, date, or link is invalid.

        Example:
            ``client._validate_record(api_row, "datetime_submitted")``
        """
        if not isinstance(item, dict):
            raise DownloadError("MuckRock returned a request that is not an object.")
        if type(item.get("id")) is not int or item["id"] <= 0:
            raise DownloadError(
                "MuckRock returned a request without a valid integer ID."
            )
        for field in ("title", "username", "absolute_url", "status", date_field):
            value = item.get(field)
            if not isinstance(value, str) or not value.strip():
                raise DownloadError(
                    f"MuckRock returned a request without a valid {field}."
                )
        if item.get("embargo_status") != "public":
            raise DownloadError(
                "MuckRock returned a non-public request. No files were written."
            )
        if date_field == "datetime_done" and item["status"] != "done":
            raise DownloadError(
                "MuckRock returned a completed request without status done."
            )

        try:
            datetime.fromisoformat(item[date_field])
            link = urlsplit(item["absolute_url"])
        except ValueError:
            raise DownloadError(
                "MuckRock returned an invalid request date or URL."
            ) from None
        if (
            link.scheme != "https"
            or link.netloc != "www.muckrock.com"
            or not link.path.startswith("/foi/")
        ):
            raise DownloadError(
                "MuckRock returned a request URL outside its public site."
            )

        # Staff and owner responses can contain fields that must never reach git.
        return {field: item[field] for field in self.SNAPSHOT_FIELDS if field in item}
