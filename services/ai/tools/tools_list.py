from enum import Enum
from typing import Any, Union
from langchain.tools import tool
from langchain_core.tools import BaseTool
from langchain_community.utilities import RequestsWrapper, GoogleSearchAPIWrapper
from config.settings import settings

class ToolId(str, Enum):
  WEB_SCRAPER = "web_scraper"
  SEARCH = "search"

@tool
def scrape_website(url: str) -> Union[str, dict[str, Any]]:
    """Useful for scraping the content of a website."""
    try:
        requests = RequestsWrapper()
        response = requests.get(url)
        return response
    except Exception as e:
        return f"Error scraping website: {e}"

@tool
def web_search(query: str) -> str:
    """Useful for searching the web for general information."""
    google_search = GoogleSearchAPIWrapper(
        google_api_key=settings.GOOGLE_SEARCH_API_KEY,
        google_cse_id=settings.GOOGLE_CSE_ID
    )
    return google_search.run(query)

def get_tool_call(id: ToolId) -> BaseTool:
    if id == ToolId.SEARCH:
        return web_search
    elif id == ToolId.WEB_SCRAPER:
        return scrape_website