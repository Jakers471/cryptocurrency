"""HTTP helpers shared by every exchange: per-thread sessions, rate limiting, retries."""
import threading
import time

import requests

UA = {"User-Agent": "Mozilla/5.0"}
_local = threading.local()


def session():
    if not hasattr(_local, "s"):
        _local.s = requests.Session()
        _local.s.headers.update(UA)
    return _local.s


class RateLimiter:
    def __init__(self, per_sec):
        self.interval = 1.0 / per_sec
        self.lock = threading.Lock()
        self.next = 0.0

    def wait(self):
        with self.lock:
            now = time.monotonic()
            t = max(now, self.next)
            self.next = t + self.interval
        if t > now:
            time.sleep(t - now)


def get(url, limiter=None, params=None, raw=False, tries=6):
    """GET with retry/backoff on 429/5xx. Returns parsed JSON (or bytes if raw), None on 404."""
    for i in range(tries):
        if limiter:
            limiter.wait()
        try:
            r = session().get(url, params=params, timeout=30)
            if r.status_code == 429 or r.status_code >= 500:
                time.sleep(2 ** i)
                continue
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.content if raw else r.json()
        except (requests.RequestException, ValueError):
            if i == tries - 1:
                raise
            time.sleep(2 ** i)
    raise RuntimeError(f"gave up on {url}")
