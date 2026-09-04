import requests
from langchain_core.tools import tool

from config import ALPHAVANTAGE_API_KEY


@tool
def get_stock_price(symbol: str) -> dict:
    """
    Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA')
    using Alpha Vantage. Requires ALPHAVANTAGE_API_KEY in the environment.
    """
    if not ALPHAVANTAGE_API_KEY:
        return {"error": "ALPHAVANTAGE_API_KEY is not set in the environment"}
    url = (
        "https://www.alphavantage.co/query"
        f"?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHAVANTAGE_API_KEY}"
    )
    r = requests.get(url)
    return r.json()
