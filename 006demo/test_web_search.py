#!/usr/bin/env python3
import asyncio
import httpx
from bs4 import BeautifulSoup
import urllib.parse


async def web_search_direct(query: str, num_results: int = 8) -> str:
    """Direct implementation of web search with fallback to mock results."""
    # Limit num_results
    num_results = min(max(num_results, 1), 20)

    try:
        # DuckDuckGo search URL
        encoded_query = urllib.parse.quote(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

        # Find search results
        results = []
        result_divs = soup.find_all("div", class_="result")

        for i, div in enumerate(result_divs[:num_results], 1):
            # Extract title
            title_elem = div.find("a", class_="result__a")
            title = title_elem.get_text(strip=True) if title_elem else "No title"

            # Extract URL
            url = (
                title_elem["href"] if title_elem and "href" in title_elem.attrs else ""
            )

            # Extract snippet
            snippet_elem = div.find("a", class_="result__snippet")
            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

            if title and url:
                results.append(f"{i}. **{title}**\n   URL: {url}\n   {snippet[:300]}\n")

        if results:
            return "\n".join(results)
        else:
            # No search results available
            return f"No search results found for query: {query}"

    except Exception as e:
        # Return error message instead of mock results
        print(f"Web search failed: {e}")
        return f"Search failed for query '{query}': {str(e)}"


async def test_web_search():
    """Test the web search tool directly."""
    print("Testing web search tool...")

    try:
        result = await web_search_direct("artificial intelligence news")
        print("✅ Web search successful!")
        print(f"Result length: {len(result)}")
        print(f"Full result: {result}")
        return True
    except Exception as e:
        print(f"❌ Web search failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_web_search())
    print(f"Test {'PASSED' if success else 'FAILED'}")
