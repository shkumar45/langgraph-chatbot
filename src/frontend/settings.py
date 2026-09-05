"""Frontend configuration — where the API is and how long to wait for it."""
import os

import httpx
from dotenv import load_dotenv

load_dotenv()


def normalize_base_url(raw: str) -> str:
    """Trim a trailing slash and assume https:// when no scheme is given
    (Render's `fromService` hands over a bare hostname)."""
    raw = raw.strip().rstrip("/")
    return raw if "://" in raw else f"https://{raw}"


# Default, from the environment. session_state.init() may override this per
# session; api_client holds the value actually used for requests.
API_BASE_URL = normalize_base_url(os.getenv("API_BASE_URL", "http://127.0.0.1:8000"))

# Generous connect timeout; no read timeout so SSE streams can stay open.
STREAM_TIMEOUT = httpx.Timeout(10.0, read=None)
REQUEST_TIMEOUT = httpx.Timeout(15.0)
# PDF ingestion embeds every chunk via the OpenAI API — can take a while for
# a large file.
INGEST_TIMEOUT = httpx.Timeout(10.0, read=60.0)
