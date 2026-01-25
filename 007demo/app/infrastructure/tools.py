from langchain_core.tools import tool

@tool
async def web_search(query: str, num_results: int = 5) -> str:
    """Search the web using DuckDuckGo."""
    try:
        # Try using duckduckgo_search directly first (more reliable than langchain wrapper sometimes)
        try:
            from duckduckgo_search import DDGS

            results = []
            # Use context manager for better session handling
            with DDGS() as ddgs:
                # text() returns an iterator or list depending on version, convert to list safely
                ddg_results = ddgs.text(query, max_results=num_results)
                if ddg_results:
                    results = list(ddg_results)

            if not results:
                print(f"⚠️ Web Search: No results found for '{query}'")
                # Fallback for offline demo
                return (
                    f"Note: Network unavailable or search failed. Mock Data for '{query}':\n"
                    f"1. **DeepSeek V3 Overview**\n"
                    f"   URL: https://deepseek.com/v3\n"
                    f"   DeepSeek V3 is a Mixture-of-Experts (MoE) model with 671B parameters, "
                    f"active parameters 37B. It is trained on 14.8T tokens and achieves SOTA performance "
                    f"on math and coding benchmarks."
                )

            print(f"✅ Web Search: Found {len(results)} results for '{query}'")
            formatted = []
            for i, r in enumerate(results, 1):
                formatted.append(
                    f"{i}. **{r.get('title', 'No Title')}**\n   URL: {r.get('href', '#')}\n   {r.get('body', '')}\n"
                )
            return "\n".join(formatted)
        except ImportError:
            # Fallback to langchain if duckduckgo_search import fails
            from langchain_community.tools import DuckDuckGoSearchRun

            search = DuckDuckGoSearchRun()
            return search.invoke(query)
    except Exception as e:
        print(f"⚠️ Web Search Error: {e}")
        return f"Search failed for query '{query}': {str(e)}"
