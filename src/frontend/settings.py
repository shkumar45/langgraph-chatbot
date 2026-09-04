"""Frontend configuration — where the API is and how long to wait for it."""
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

# Render's `fromService` gives a bare hostname; assume https:// when no scheme.
_raw_api = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
API_BASE_URL = _raw_api if "://" in _raw_api else f"https://{_raw_api}"

# Generous connect timeout; no read timeout so SSE streams can stay open.
STREAM_TIMEOUT = httpx.Timeout(10.0, read=None)
REQUEST_TIMEOUT = httpx.Timeout(15.0)
