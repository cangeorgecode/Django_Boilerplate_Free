"""Small retry wrapper for third-party API calls (idempotent-ish GET/POST with
short backoff). Keeps transient outages from killing whole jobs."""
import logging
import time

logger = logging.getLogger(__name__)


def retry_call(fn, attempts=3, backoff=2.0, on_error=None):
    """Call fn() up to `attempts` times with exponential backoff. The final
    exception is re-raised; earlier ones are logged (or passed to on_error)."""
    last_exc = None
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            if on_error:
                on_error(exc, attempt)
            logger.warning("API call failed (attempt %d/%d): %s", attempt, attempts, exc)
            if attempt < attempts:
                time.sleep(backoff * attempt)
    raise last_exc
