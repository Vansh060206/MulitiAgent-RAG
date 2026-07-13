import os
import logging
from typing import List, Dict, Any
from tavily import TavilyClient
from app.core.config import settings

logger = logging.getLogger(__name__)

class WebSearchService:
    """
    Modular Web Research Tool using Tavily Search API.
    Provides fallback content if the API key is not configured.
    """
    def __init__(self):
        self.api_key = settings.TAVILY_API_KEY or os.environ.get("TAVILY_API_KEY")
        if self.api_key:
            logger.info("Tavily API Key detected. Web search is enabled.")
        else:
            logger.warning("No TAVILY_API_KEY configured. Web search will run in mock fallback mode.")

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Executes a web search query.
        
        Inputs:
            query: str - The search string.
            limit: int - Max search results (default 5).
        Outputs:
            List[Dict[str, Any]] - Structured search results containing source, title, url, and content.
        """
        if not query:
            return []

        if not self.api_key:
            logger.warning("Attempted web search without TAVILY_API_KEY. Returning warning mock.")
            return [{
                "source": "web_mock",
                "doc_name": "Web Search Warning",
                "url": "https://tavily.com",
                "content": f"Web search for '{query}' was requested, but no Tavily API Key is configured in the environment. Please add TAVILY_API_KEY to your .env file."
            }]

        try:
            logger.info(f"Querying Tavily Search: '{query}'")
            tavily = TavilyClient(api_key=self.api_key)
            response = tavily.search(query=query, max_results=limit)
            
            results = []
            for result in response.get("results", []):
                results.append({
                    "source": "web",
                    "doc_name": result.get("title", "Web Result"),
                    "url": result.get("url", ""),
                    "content": result.get("content", "")
                })
            
            logger.info(f"Retrieved {len(results)} web search results.")
            return results
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return [{
                "source": "web_error",
                "doc_name": "Search Error",
                "url": "",
                "content": f"Failed to execute Tavily search: {e}"
            }]
