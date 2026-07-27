"""Shared, memory-only OAuth2 client for official PISTE APIs."""

from __future__ import annotations

from dataclasses import dataclass
import json
import time
from typing import Any, Callable
import urllib.error
import urllib.parse
import urllib.request


DEFAULT_OAUTH_URL = "https://oauth.piste.gouv.fr/api/oauth/token"


class PisteOAuthError(RuntimeError):
    def __init__(self, status: str, message: str, http_status: int | None = None) -> None:
        self.status = status
        self.http_status = http_status
        super().__init__(message)


@dataclass(frozen=True)
class PisteCredentials:
    client_id: str | None
    client_secret: str | None
    oauth_url: str = DEFAULT_OAUTH_URL
    scope: str = "openid"
    timeout_seconds: int = 20
    source: str | None = None

    @property
    def configured(self) -> bool:
        return bool(self.client_id and self.client_secret)


class PisteOAuthClient:
    """Acquire and renew a client-credentials token without persisting it."""

    def __init__(
        self,
        credentials: PisteCredentials,
        *,
        opener: Callable[..., Any] = urllib.request.urlopen,
        clock: Callable[[], float] = time.time,
        retry_count: int = 1,
    ) -> None:
        self.credentials = credentials
        self._opener = opener
        self._clock = clock
        self._retry_count = max(0, min(retry_count, 2))
        self._token: dict[str, Any] | None = None

    def token(self, force_refresh: bool = False) -> dict[str, Any]:
        if not self.credentials.configured:
            raise PisteOAuthError("not_configured", "Identifiants PISTE absents.")
        if not force_refresh and self._token and self._valid(self._token):
            return {**self._token, "from_cache": True}

        attempts = self._retry_count + 1
        for attempt in range(attempts):
            try:
                token = self._request_token()
                self._token = token
                return {**token, "from_cache": False}
            except PisteOAuthError as exc:
                retryable = exc.status in {"timeout", "network_error", "unavailable"}
                if not retryable or attempt + 1 >= attempts:
                    raise
        raise PisteOAuthError("unavailable", "OAuth PISTE indisponible.")

    def diagnostic(self) -> dict[str, Any]:
        token = self.token()
        return {
            "ok": True,
            "status": "available",
            "token_type": token.get("token_type", "Bearer"),
            "expires_in": token.get("expires_in"),
            "from_cache": bool(token.get("from_cache")),
        }

    def _valid(self, token: dict[str, Any]) -> bool:
        return float(token.get("expires_at", 0)) > self._clock() + 60

    def _request_token(self) -> dict[str, Any]:
        form = {
            "grant_type": "client_credentials",
            "client_id": self.credentials.client_id or "",
            "client_secret": self.credentials.client_secret or "",
            "scope": self.credentials.scope,
        }
        request = urllib.request.Request(
            self.credentials.oauth_url,
            data=urllib.parse.urlencode(form).encode("utf-8"),
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with self._opener(request, timeout=self.credentials.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            status = {
                400: "authentication_failed",
                401: "authentication_failed",
                403: "forbidden",
                429: "quota_exceeded",
            }.get(exc.code, "unavailable" if exc.code >= 500 else "invalid_response")
            raise PisteOAuthError(status, f"OAuth PISTE refuse: HTTP {exc.code}.", exc.code) from exc
        except TimeoutError as exc:
            raise PisteOAuthError("timeout", "OAuth PISTE: délai dépassé.") from exc
        except urllib.error.URLError as exc:
            reason = getattr(exc, "reason", None)
            status = "timeout" if isinstance(reason, TimeoutError) else "network_error"
            raise PisteOAuthError(status, f"OAuth PISTE indisponible: {type(reason).__name__}.") from exc
        except (json.JSONDecodeError, UnicodeDecodeError, TypeError) as exc:
            raise PisteOAuthError("invalid_response", "OAuth PISTE: réponse invalide.") from exc

        access_token = payload.get("access_token") if isinstance(payload, dict) else None
        if not access_token:
            raise PisteOAuthError("invalid_response", "OAuth PISTE: access_token absent.")
        try:
            expires_in = max(60, int(payload.get("expires_in") or 3600))
        except (TypeError, ValueError):
            expires_in = 3600
        return {
            "access_token": str(access_token),
            "token_type": str(payload.get("token_type") or "Bearer"),
            "expires_in": expires_in,
            "expires_at": self._clock() + expires_in,
        }
