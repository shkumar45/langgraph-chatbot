import tools.stock_price as stock_price_module
from tools.stock_price import get_stock_price


def test_missing_api_key_is_a_graceful_error(monkeypatch):
    monkeypatch.setattr(stock_price_module, "ALPHAVANTAGE_API_KEY", None)
    result = get_stock_price.invoke({"symbol": "AAPL"})
    assert result == {"error": "ALPHAVANTAGE_API_KEY is not set in the environment"}


def test_happy_path_calls_alphavantage_with_symbol_and_key(monkeypatch):
    monkeypatch.setattr(stock_price_module, "ALPHAVANTAGE_API_KEY", "fake-key")
    captured = {}

    class FakeResponse:
        def json(self):
            return {"Global Quote": {"05. price": "123.45"}}

    def fake_get(url):
        captured["url"] = url
        return FakeResponse()

    monkeypatch.setattr(stock_price_module.requests, "get", fake_get)

    result = get_stock_price.invoke({"symbol": "AAPL"})

    assert result == {"Global Quote": {"05. price": "123.45"}}
    assert "AAPL" in captured["url"]
    assert "fake-key" in captured["url"]
