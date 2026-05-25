import time
import threading
from dataclasses import dataclass
from typing import Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


@dataclass
class RequestResult:
    elapsed: float
    queue_delay: float
    total_elapsed: float
    success: bool
    status_code: Optional[int]
    error: Optional[str]


_thread_local = threading.local()
_pool_connections = 10
_pool_maxsize = 10
_retry_total = 0
_retry_backoff = 0.0
_active_lock = threading.Lock()
_active_requests = 0
_max_active_requests = 0


def configure_http_client(
    pool_connections: int,
    pool_maxsize: int,
    retry_total: int,
    retry_backoff: float,
) -> None:
    global _pool_connections, _pool_maxsize, _retry_total, _retry_backoff
    _pool_connections = max(1, pool_connections)
    _pool_maxsize = max(1, pool_maxsize)
    _retry_total = max(0, retry_total)
    _retry_backoff = max(0.0, retry_backoff)


def reset_activity_metrics() -> None:
    global _active_requests, _max_active_requests
    with _active_lock:
        _active_requests = 0
        _max_active_requests = 0


def get_max_active_requests() -> int:
    with _active_lock:
        return _max_active_requests


def _get_session() -> requests.Session:
    session = getattr(_thread_local, "session", None)
    if session is None:
        session = requests.Session()
        retry = Retry(
            total=_retry_total,
            connect=_retry_total,
            read=_retry_total,
            status=_retry_total,
            backoff_factor=_retry_backoff,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET"]),
            raise_on_status=False,
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(
            pool_connections=_pool_connections,
            pool_maxsize=_pool_maxsize,
            max_retries=retry,
            pool_block=False,
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        _thread_local.session = session
    return session


def make_request(
    url: str,
    connect_timeout_seconds: int,
    read_timeout_seconds: int,
    submit_time: float,
) -> RequestResult:
    request_start = time.perf_counter()
    queue_delay = request_start - submit_time
    session = _get_session()

    global _active_requests, _max_active_requests
    with _active_lock:
        _active_requests += 1
        if _active_requests > _max_active_requests:
            _max_active_requests = _active_requests

    try:
        timeout: Tuple[int, int] = (connect_timeout_seconds, read_timeout_seconds)
        response = session.get(url, timeout=timeout)
        request_end = time.perf_counter()
        status_code = response.status_code
        success = 200 <= status_code < 400
        return RequestResult(
            elapsed=request_end - request_start,
            queue_delay=queue_delay,
            total_elapsed=request_end - submit_time,
            success=success,
            status_code=status_code,
            error=None,
        )
    except requests.RequestException as exc:
        request_end = time.perf_counter()
        return RequestResult(
            elapsed=request_end - request_start,
            queue_delay=queue_delay,
            total_elapsed=request_end - submit_time,
            success=False,
            status_code=None,
            error=type(exc).__name__,
        )
    finally:
        with _active_lock:
            _active_requests -= 1
