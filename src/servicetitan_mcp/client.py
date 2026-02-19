"""
ServiceTitan API client with OAuth2 authentication and automatic token refresh.

ServiceTitan API conventions:
- Base URL: https://api.servicetitan.io (prod) or https://api-integration.servicetitan.io (sandbox)
- Auth URL: https://auth.servicetitan.io/connect/token (prod) or https://auth-integration.servicetitan.io/connect/token (sandbox)
- URL pattern: /{module}/v2/tenant/{tenant_id}/{endpoint}
- Auth: OAuth2 client_credentials grant
- Headers: Authorization: Bearer {token}, ST-App-Key: {app_key}
- Pagination: ?page=1&pageSize=50, response has { data: [...], page, pageSize, totalCount, hasMore }
"""

from __future__ import annotations

import time
from typing import Any, Optional

import httpx

from .models.types import ServiceTitanConfig


class ServiceTitanError(Exception):
    """Base exception for ServiceTitan API errors."""

    def __init__(self, message: str, status_code: int | None = None, response_body: str | None = None):
        self.status_code = status_code
        self.response_body = response_body
        super().__init__(message)


class ServiceTitanAuthError(ServiceTitanError):
    """Authentication/token errors."""
    pass


class ServiceTitanAPIError(ServiceTitanError):
    """API request errors (4xx/5xx)."""
    pass


class ServiceTitanClient:
    """Async HTTP client for the ServiceTitan REST API.

    Handles OAuth2 client_credentials authentication with automatic
    token caching and refresh. All API calls include the required
    ST-App-Key header.

    Usage:
        async with ServiceTitanClient(config) as client:
            customers = await client.get("crm", "customers", params={"name": "Smith"})
    """

    _AUTH_URLS = {
        "integration": "https://auth-integration.servicetitan.io/connect/token",
        "production": "https://auth.servicetitan.io/connect/token",
    }
    _BASE_URLS = {
        "integration": "https://api-integration.servicetitan.io",
        "production": "https://api.servicetitan.io",
    }

    def __init__(self, config: ServiceTitanConfig) -> None:
        self.config = config
        env = config.environment.lower()
        if env not in self._AUTH_URLS:
            raise ValueError(f"environment must be 'integration' or 'production', got '{env}'")

        self.auth_url = self._AUTH_URLS[env]
        self.base_url = self._BASE_URLS[env]
        self.tenant_id = config.tenant_id

        self._access_token: str | None = None
        self._token_expiry: float = 0.0
        self._http: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "ServiceTitanClient":
        self._http = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
        return self

    async def __aexit__(self, *exc: Any) -> None:
        if self._http:
            await self._http.aclose()
            self._http = None

    @property
    def http(self) -> httpx.AsyncClient:
        if self._http is None:
            raise RuntimeError("Client not initialized. Use 'async with ServiceTitanClient(config) as client:'")
        return self._http

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------
    async def _refresh_token(self) -> None:
        """Fetch a new OAuth2 access token using client_credentials grant."""
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            resp = await self.http.post(self.auth_url, data=payload, headers=headers)
        except httpx.HTTPError as exc:
            raise ServiceTitanAuthError(f"Failed to connect to auth server: {exc}") from exc

        if resp.status_code != 200:
            raise ServiceTitanAuthError(
                f"Authentication failed ({resp.status_code}): {resp.text}",
                status_code=resp.status_code,
                response_body=resp.text,
            )

        token_data = resp.json()
        self._access_token = token_data.get("access_token")
        if not self._access_token:
            raise ServiceTitanAuthError("Auth response missing access_token")

        expires_in = token_data.get("expires_in", 900)
        self._token_expiry = time.time() + float(expires_in)

    async def _get_token(self) -> str:
        """Return a valid access token, refreshing if needed (60s buffer)."""
        if not self._access_token or time.time() >= (self._token_expiry - 60):
            await self._refresh_token()
        assert self._access_token is not None
        return self._access_token

    # ------------------------------------------------------------------
    # URL building
    # ------------------------------------------------------------------
    def _build_url(self, module: str, endpoint: str, version: int = 2) -> str:
        """Build full API URL: {base}/{module}/v{version}/tenant/{tenant}/{endpoint}"""
        return f"{self.base_url}/{module}/v{version}/tenant/{self.tenant_id}/{endpoint}"

    # ------------------------------------------------------------------
    # HTTP methods
    # ------------------------------------------------------------------
    async def _request(
        self,
        method: str,
        module: str,
        endpoint: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any | None = None,
        version: int = 2,
    ) -> Any:
        """Execute an authenticated API request.

        Returns parsed JSON on success. Raises ServiceTitanAPIError on failure.
        """
        url = self._build_url(module, endpoint, version)
        token = await self._get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "ST-App-Key": self.config.app_key,
        }

        try:
            resp = await self.http.request(method, url, params=params, json=json_body, headers=headers)
        except httpx.HTTPError as exc:
            raise ServiceTitanAPIError(f"Request to {url} failed: {exc}") from exc

        if resp.status_code >= 400:
            error_text = resp.text
            try:
                error_text = str(resp.json())
            except Exception:
                pass
            raise ServiceTitanAPIError(
                f"{resp.status_code} error for {method} {url}: {error_text}",
                status_code=resp.status_code,
                response_body=resp.text,
            )

        if resp.status_code == 204:
            return None

        content_type = resp.headers.get("content-type", "")
        if "application/json" in content_type:
            return resp.json()
        return resp.text

    async def get(
        self,
        module: str,
        endpoint: str,
        *,
        params: dict[str, Any] | None = None,
        version: int = 2,
    ) -> Any:
        """GET request."""
        return await self._request("GET", module, endpoint, params=params, version=version)

    async def post(
        self,
        module: str,
        endpoint: str,
        *,
        json_body: Any | None = None,
        params: dict[str, Any] | None = None,
        version: int = 2,
    ) -> Any:
        """POST request."""
        return await self._request("POST", module, endpoint, json_body=json_body, params=params, version=version)

    async def put(
        self,
        module: str,
        endpoint: str,
        *,
        json_body: Any | None = None,
        params: dict[str, Any] | None = None,
        version: int = 2,
    ) -> Any:
        """PUT request."""
        return await self._request("PUT", module, endpoint, json_body=json_body, params=params, version=version)

    async def patch(
        self,
        module: str,
        endpoint: str,
        *,
        json_body: Any | None = None,
        params: dict[str, Any] | None = None,
        version: int = 2,
    ) -> Any:
        """PATCH request."""
        return await self._request("PATCH", module, endpoint, json_body=json_body, params=params, version=version)

    async def get_all(
        self,
        module: str,
        endpoint: str,
        *,
        params: dict[str, Any] | None = None,
        version: int = 2,
        max_pages: int = 20,
    ) -> list[Any]:
        """Paginate through all results. Returns flattened list of data items."""
        all_data: list[Any] = []
        page_params = dict(params or {})
        page_params.setdefault("pageSize", 50)
        page = 1

        for _ in range(max_pages):
            page_params["page"] = page
            resp = await self.get(module, endpoint, params=page_params, version=version)
            if not isinstance(resp, dict):
                break
            data = resp.get("data", [])
            all_data.extend(data)
            if not resp.get("hasMore", False):
                break
            page += 1

        return all_data


# Singleton-ish client instance managed by the server
_client: ServiceTitanClient | None = None


def get_client() -> ServiceTitanClient:
    """Get the global ServiceTitan client instance. Must be initialized first."""
    if _client is None:
        raise RuntimeError("ServiceTitan client not initialized. Call init_client() first.")
    return _client


async def init_client(config: Optional[ServiceTitanConfig] = None) -> ServiceTitanClient:
    """Initialize and return the global ServiceTitan client."""
    global _client
    if config is None:
        config = ServiceTitanConfig()  # type: ignore[call-arg]  — loads from env
    _client = ServiceTitanClient(config)
    _client._http = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
    return _client


async def close_client() -> None:
    """Close the global client."""
    global _client
    if _client and _client._http:
        await _client._http.aclose()
    _client = None
