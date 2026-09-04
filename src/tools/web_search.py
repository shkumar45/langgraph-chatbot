from ddgs import DDGS
from langchain_core.tools import tool


@tool
def web_search(query: str, max_results: int = 5) -> list[dict]:
    """
    Search the web with DuckDuckGo and return a list of results.
    Each result is a dict with 'title', 'href' and 'body'.
    Use this for current events or facts the model may not know.
    """
    try:
        with DDGS() as ddgs:
            return list(ddgs.text(query, region="us-en", max_results=max_results))
    except Exception as e:
        return [{"error": str(e)}]
