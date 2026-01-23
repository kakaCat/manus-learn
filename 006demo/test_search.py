#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup


def test_duckduckgo_search():
    query = "Python tutorial"
    url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        results = soup.find_all("div", class_="result")

        print(f"Found {len(results)} results")

        for i, div in enumerate(results[:3], 1):
            title_elem = div.find("a", class_="result__a")
            title = title_elem.get_text(strip=True) if title_elem else "No title"
            url = (
                title_elem["href"] if title_elem and "href" in title_elem.attrs else ""
            )
            snippet_elem = div.find("a", class_="result__snippet")
            snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

            print(f"{i}. {title}")
            print(f"   URL: {url}")
            print(f"   {snippet[:100]}...")
            print("---")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_duckduckgo_search()
