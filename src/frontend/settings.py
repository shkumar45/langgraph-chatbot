"""Frontend configuration — where the API is and how long to wait for it."""
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

# Generous connect timeout; no read timeout so SSE streams can stay open.
STREAM_TIMEOUT = httpx.Timeout(10.0, read=None)
REQUEST_TIMEOUT = httpx.Timeout(15.0)
