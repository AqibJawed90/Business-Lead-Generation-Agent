from tavily import TavilyClient
from config import TAVILY_API_KEY


def search_businesses(niche: str, country: str, city: str, target: int = 10):
    """Search the web for business websites."""

    client = TavilyClient(api_key=TAVILY_API_KEY)

    query = (
         f"{niche} in {city} {country} "
        "official website contact"
)
    print(f"\nSearching: {query}")

    response = client.search(
        query=query,
        search_depth="advanced",
        max_results=min(max(target * 2, 5), 20),
        topic="general",
    )

    leads = []

    for result in response.get("results", []):
        leads.append({
            "title": result.get("title", ""),
            "url": result.get("url", ""),
            "content": result.get("content", ""),
        })

    return leads
