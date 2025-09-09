import asyncio
import json
import re
import sys
import aiohttp
from typing import List, Dict, Any, Tuple
from ddgs import DDGS
from bs4 import BeautifulSoup

# Define API endpoint for Wikipedia fallback
WIKI_API = "https://en.wikipedia.org/w/api.php"

def summarize_text(text: str) -> str:
    """Provides a concise summary of the text."""
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
    num_sentences = 5 if len(sentences) > 5 else len(sentences)
    summary_sentences = sentences[:num_sentences]
    summary = " ".join(summary_sentences)
    if len(sentences) > num_sentences:
        summary += "..."
    return summary

def strip_html_tags(html_content: str) -> str:
    """Removes HTML tags and cleans up whitespace."""
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text(separator=' ', strip=True)
    return text

async def fetch_and_summarize_url(session: aiohttp.ClientSession, url: str) -> Dict[str, str] | None:
    """Fetches, cleans, and summarizes content from a single URL."""
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    try:
        async with session.get(url, headers=headers, timeout=10) as response:
            response.raise_for_status()
            text = await response.text()
            text_content = strip_html_tags(text)
            summary = summarize_text(text_content)
            return {"url": url, "content": summary}
    except aiohttp.ClientError as e:
        print(f"Warning: Could not fetch {url}. Reason: {e}", file=sys.stderr)
        return None

async def browser_search(query: str) -> Tuple[List[Dict], str]:
    """
    Performs a general web search with a fallback to a Wikipedia API search.
    """
    print(f"Performing general web search for: '{query}'", file=sys.stderr)
    sources = []
    
    try:
        with DDGS() as ddgs:
            search_results = list(ddgs.text(query, max_results=5))
        
        urls_to_fetch = [r['href'] for r in search_results]
        
        # Take the top 3 most relevant URLs from the search
        if not urls_to_fetch:
            # If DDGS returns no results, fall back to Wikipedia
            return await wikipedia_fallback_search(query)
            
        urls_to_fetch = urls_to_fetch[:3]
        
        async with aiohttp.ClientSession() as session:
            print(f"Fetching content from: {', '.join(urls_to_fetch)}", file=sys.stderr)
            tasks = [fetch_and_summarize_url(session, url) for url in urls_to_fetch]
            results = await asyncio.gather(*tasks)

            for result in results:
                if result:
                    sources.append(result)
    except Exception as e:
        print(f"Error during web search: {e}. Falling back...", file=sys.stderr)
        return await wikipedia_fallback_search(query)
    
    return sources, query

async def wikipedia_fallback_search(query: str) -> Tuple[List[Dict], str]:
    """Fallback method using Wikipedia API."""
    print(f"Web search failed. Falling back to Wikipedia API for: '{query}'", file=sys.stderr)
    
    search_params = {"action": "query", "format": "json", "list": "search", "srsearch": query, "srlimit": 1}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(WIKI_API, params=search_params) as response:
                search_data = await response.json()
                search_results = search_data.get("query", {}).get("search", [])
                if not search_results:
                    return [], query
                
                page_title = search_results[0]['title']
                fetch_params = {"action": "query", "format": "json", "prop": "extracts", "explaintext": True, "titles": page_title}
                
                async with session.get(WIKI_API, params=fetch_params) as response:
                    fetch_data = await response.json()
                    pages = fetch_data.get("query", {}).get("pages", {})
                    page = next(iter(pages.values()), None)

                    if page and "missing" not in page:
                        content = page.get("extract", "")
                        return [{"url": f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}", "content": content}], query
                    return [], query
    except Exception as e:
        print(f"Wikipedia fallback error: {e}", file=sys.stderr)
        return [], query

async def main_cli():
    """Main function for the command-line interface."""
    args = sys.argv[1:]
    if not args:
        print("Usage: python search_logic.py \"query1\" \"query2\" ...", file=sys.stderr)
        sys.exit(1)
    
    tasks = [browser_search(query) for query in args]
    results = await asyncio.gather(*tasks)

    formatted_results = []
    for sources, query in results:
        if sources:
            result_data = {"type": "summary", "query": query, "sources": sources}
        else:
            result_data = {"error": "Could not find a relevant answer for that query."}
        formatted_results.append(result_data)
        
    print(json.dumps(formatted_results, indent=2))

if __name__ == "__main__":
    asyncio.run(main_cli())
