import asyncio
import json
import re
import sys
import aiohttp

# The user will need to install these libraries:
# pip install ddgs aiohttp
try:
    from ddgs import DDGS
except ImportError:
    print("Error: The 'ddgs' library is required. Please install it by running: pip install ddgs", file=sys.stderr)
    sys.exit(1)

def get_precise_answer_from_text(text: str, url: str) -> str | None:
    """Uses regex to find the incumbent Prime Minister from Wikipedia text."""
    match = re.search(r"Incumbent\s+([A-Z][\w\.\-]*(?:\s+[A-Z][\w\.\-]*)*)\s+since", text.replace("\n", ""))
    if match:
        name = re.sub(r'([a-z])([A-Z])', r'\1 \2', match.group(1))
        return name

    if "en.wikipedia.org/wiki/" in url:
        title = url.split("/wiki/")[-1].replace("_", " ")
        if len(title.split()) > 1 and len(title.split()) < 4:
            return title

    return None

def strip_html_tags(html_content: str) -> str:
    """A basic function to remove HTML tags and clean up whitespace."""
    html_content = re.sub(r'(?is)<(script|style).*?>.*?(</\1>)', '', html_content)
    text = re.sub(r'<.*?>', '', html_content)
    return ' '.join(text.split())

async def fetch_url(session, url, query, precise_answer_found):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    try:
        async with session.get(url, headers=headers, timeout=10) as response:
            response.raise_for_status()
            text = await response.text()
            
            precise_answer = None
            if ("pm of india" in query.lower() or "prime minister of india" in query.lower()) and not precise_answer_found.is_set():
                precise_answer = get_precise_answer_from_text(text, url)
                if precise_answer:
                    precise_answer_found.set()

            text_content = strip_html_tags(text)
            return {"url": url, "content": text_content}, precise_answer
    except aiohttp.ClientError as e:
        print(f"Warning: Could not fetch {url}. Reason: {e}", file=sys.stderr)
        return None, None

async def browser_search(query: str, num_results: int = 3) -> tuple[str | None, list[dict]]:
    """
    Performs a web search asynchronously. If a precise answer is found, it's returned.
    Otherwise, returns a list of sources for summarization.
    """
    print(f"Performing web search for: '{query}'", file=sys.stderr)
    sources = []
    precise_answer = None
    
    try:
        with DDGS() as ddgs:
            search_results = list(ddgs.text(query, max_results=num_results))
        
        if not search_results:
            return None, []

        urls_to_fetch = [r['href'] for r in search_results]
        print(f"Fetching content from: {', '.join(urls_to_fetch)}", file=sys.stderr)

        async with aiohttp.ClientSession() as session:
            precise_answer_found = asyncio.Event()
            tasks = [fetch_url(session, url, query, precise_answer_found) for url in urls_to_fetch]
            results = await asyncio.gather(*tasks)

            for result, pa in results:
                if result:
                    sources.append(result)
                if pa and not precise_answer:
                    precise_answer = pa

    except Exception as e:
        print(f"Error: An unexpected error occurred during web search: {e}", file=sys.stderr)
    
    return precise_answer, sources

def generate_html_output(data: dict) -> str:
    """Generates a clean HTML document from the result data."""
    query = data.get('query', 'N/A')
    answer_type = data.get('type', 'N/A')

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Search Result: {query}</title>
    <style>
        body {{ font-family: sans-serif; line-height: 1.6; margin: 2em; background-color: #f8f9fa; color: #212529; }}
        .container {{ max-width: 800px; margin: auto; background-color: #ffffff; padding: 2em; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #343a40; }}
        h2 {{ color: #495057; border-bottom: 1px solid #dee2e6; padding-bottom: 0.3em; }}
        .source {{ margin-bottom: 1.5em; }}
        .source a {{ color: #007bff; text-decoration: none; }}
        .source a:hover {{ text-decoration: underline; }}
        .content {{ background-color: #f8f9fa; padding: 1em; border-radius: 5px; white-space: pre-wrap; word-wrap: break-word; }}
        .factual-answer {{ font-size: 1.5em; font-weight: bold; color: #28a745; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Search Query</h1>
        <p><em>{query}</em></p>
        <h2>Result</h2>
    """

    if answer_type == 'fact':
        html += f'<div class="factual-answer">{data.get("answer", "No answer found.")}</div>'
    elif answer_type == 'summary':
        for source in data.get('sources', []):
            content_preview = source.get('content', '')[:800]
            if len(source.get('content', '')) > 800:
                content_preview += "..."
            html += f"""
            <div class="source">
                <strong>Source:</strong> <a href="{source.get('url')}" target="_blank">{source.get('url')}</a>
                <div class="content">{content_preview}</div>
            </div>
            """
    else:
        html += "<p>No results found.</p>"

    html += """
    </div>
</body>
</html>"""
    return html


async def main():
    """Main function to run the search model."""
    args = sys.argv[1:]
    if not args or (len(args) == 1 and args[0] in ["--format", "html"]):
        print("Usage: python model.py [--format html] \"<query>\"", file=sys.stderr)
        sys.exit(1)

    output_format = 'json'
    query_list = []
    # Corrected argument parsing
    is_format_flag = False
    for arg in args:
        if is_format_flag:
            if arg.lower() == 'html':
                output_format = 'html'
            is_format_flag = False
            continue
        if arg.lower() == '--format':
            is_format_flag = True
        else:
            query_list.append(arg)
    
    query = " ".join(query_list)
    result_data = {}

    # Perform the search, which may return a precise answer directly
    precise_answer, sources = await browser_search(query)

    if precise_answer:
        result_data = {
            "type": "fact",
            "query": query,
            "answer": precise_answer
        }
    elif sources:
        result_data = {
            "type": "summary",
            "query": query,
            "sources": sources
        }
    else:
        result_data = {"error": "Could not find a relevant answer for that query."}

    if output_format == 'html':
        print(generate_html_output(result_data))
    else:
        print(json.dumps(result_data, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
