from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import requests
    from requests.auth import HTTPBasicAuth
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
except ImportError:  # pragma: no cover - exercised only before dependencies are installed
    requests = None
    HTTPBasicAuth = None
    InsecureRequestWarning = None


LOGGER = logging.getLogger(__name__)


class LcuUnavailableError(RuntimeError):
    """Raised when the League client is not available or not reachable."""


class LcuApiError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class LockfileInfo:
    name: str
    pid: int
    port: int
    password: str
    protocol: str


def parse_lockfile_text(text: str) -> LockfileInfo:
    parts = text.strip().split(":")
    if len(parts) != 5:
        raise ValueError("League lockfile must contain five colon-separated fields")

    name, pid_raw, port_raw, password, protocol = parts
    if not name:
        raise ValueError("League lockfile is missing the process name")
    if not password:
        raise ValueError("League lockfile is missing the API password")
    if protocol not in {"http", "https"}:
        raise ValueError(f"Unsupported League client protocol: {protocol}")

    try:
        pid = int(pid_raw)
        port = int(port_raw)
    except ValueError as exc:
        raise ValueError("League lockfile pid and port must be integers") from exc

    return LockfileInfo(
        name=name,
        pid=pid,
        port=port,
        password=password,
        protocol=protocol,
    )


def find_lockfile(paths: tuple[Path, ...]) -> Path:
    for path in paths:
        if path.is_file():
            return path
    raise LcuUnavailableError("League lockfile was not found")


class LcuClient:
    def __init__(
        self,
        lockfile_paths: tuple[Path, ...],
        request_timeout_seconds: float,
    ) -> None:
        if requests is None or HTTPBasicAuth is None:
            raise RuntimeError("The requests package is required to use the LCU client")

        if InsecureRequestWarning is not None:
            requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

        self._lockfile_paths = lockfile_paths
        self._timeout = request_timeout_seconds
        self._session = requests.Session()
        self._info: LockfileInfo | None = None

    def reset(self) -> None:
        self._info = None
        self._session = requests.Session()

    def set_lockfile_paths(self, lockfile_paths: tuple[Path, ...]) -> None:
        self._lockfile_paths = lockfile_paths
        self.reset()

    def connect(self) -> LockfileInfo:
        lockfile = find_lockfile(self._lockfile_paths)
        info = parse_lockfile_text(lockfile.read_text(encoding="utf-8"))
        self._session.auth = HTTPBasicAuth("riot", info.password)
        self._info = info
        LOGGER.info("Connected to League client API on port %s", info.port)
        return info

    def request(self, method: str, path: str, **kwargs: Any) -> Any:
        if self._info is None:
            self.connect()

        assert self._info is not None
        url = f"{self._info.protocol}://127.0.0.1:{self._info.port}{path}"

        try:
            response = self._session.request(
                method=method,
                url=url,
                timeout=self._timeout,
                verify=False,
                **kwargs,
            )
        except requests.RequestException as exc:
            self.reset()
            raise LcuUnavailableError(str(exc)) from exc

        if response.status_code in {401, 403}:
            self.reset()
            raise LcuUnavailableError(f"League client authentication failed: {response.status_code}")

        if response.status_code >= 400:
            raise LcuApiError(
                f"League client API returned HTTP {response.status_code} for {path}",
                status_code=response.status_code,
            )

        if not response.content:
            return None

        content_type = response.headers.get("content-type", "")
        if "json" not in content_type.lower():
            return response.text

        return response.json()

    def get_gameflow_phase(self) -> str:
        phase = self.request("GET", "/lol-gameflow/v1/gameflow-phase")
        return str(phase)

    def get_ready_check(self) -> dict[str, Any] | None:
        try:
            payload = self.request("GET", "/lol-matchmaking/v1/ready-check")
        except LcuApiError as exc:
            if exc.status_code == 404:
                return None
            raise

        if isinstance(payload, dict):
            return payload
        return None

    def accept_ready_check(self) -> None:
        self.request("POST", "/lol-matchmaking/v1/ready-check/accept")
