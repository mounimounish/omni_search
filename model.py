# micro_wiki_service.py
import requests
import json
import sys
import re

# Define API endpoints
WIKI_API = "https://en.wikipedia.org/w/api.php"
WIKIDATA_SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

def get_wikidata_answer(query: str) -> str | None:
    """
    Attempts to get a precise, factual answer using Wikidata.
    """
    # Simple keyword mapping for specific queries
    if "pm of india" in query.lower() or "prime minister of india" in query.lower():
        # Wikidata query to get the current Prime Minister of India
        sparql_query = """
        SELECT ?personLabel WHERE {
          ?person wdt:P39 wd:Q15951806;  # P39 is 'position held', Q15951806 is 'Prime Minister of India'
                  p:P39 ?statement.
          ?statement pq:P580 ?start_time. # P580 is 'start time'
          FILTER NOT EXISTS { ?statement pq:P582 ?end_time. } # P582 is 'end time' - ensures we get the current holder
          SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
        }
        LIMIT 1
        """
        response = requests.get(WIKIDATA_SPARQL_ENDPOINT, params={'query': sparql_query, 'format': 'json'})
        data = response.json()
        
        bindings = data.get("results", {}).get("bindings", [])
        if bindings:
            return bindings[0]['personLabel']['value']
    
    return None

def search_wikipedia_summary(query: str) -> str | None:
    """
    Searches for the best-matching Wikipedia page and fetches its summary.
    This is used for general, descriptive queries.
    """
    headers = {
        'User-Agent': 'AIDrivenOS-Microservice/1.0 (contact@example.com)'
    }
    
    # Step 1: Search for the correct page title
    search_params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": query,
        "srlimit": 1
    }
    
    try:
        search_response = requests.get(WIKI_API, params=search_params, headers=headers, timeout=5)
        search_response.raise_for_status()
        search_data = search_response.json()
        
        search_results = search_data.get("query", {}).get("search", [])
        if not search_results:
            return None
        
        page_title = search_results[0]['title']

        # Step 2: Fetch the introductory summary of the found page
        fetch_params = {
            "action": "query",
            "format": "json",
            "prop": "extracts",
            "explaintext": True,
            "exintro": True,
            "titles": page_title
        }
        
        fetch_response = requests.get(WIKI_API, params=fetch_params, headers=headers, timeout=5)
        fetch_response.raise_for_status()
        fetch_data = fetch_response.json()
        
        pages = fetch_data.get("query", {}).get("pages", {})
        page = next(iter(pages.values()), None)

        if page and "missing" not in page:
            content = page.get("extract", "")
            # Clean up unwanted junk like 'disambiguation' warnings
            cleaned_content = re.sub(r'\(.*?\)', '', content).strip()
            return cleaned_content
        
        return None
    except requests.exceptions.RequestException as e:
        # Log the error for debugging by the main model
        print(f"Request error: {e}", file=sys.stderr)
        return None

def main():
    """
    Main function to run the microservice.
    It takes a query as a command-line argument.
    """
    if len(sys.argv) < 2:
        # Return a structured error to the main model
        print(json.dumps({"error": "Usage: python micro_wiki_service.py '<query>'"}), file=sys.stderr)
        sys.exit(1)

    query = sys.argv[1]
    
    # Attempt to get a precise answer from Wikidata
    precise_answer = get_wikidata_answer(query)
    
    if precise_answer:
        # If a precise answer is found, return it immediately
        print(json.dumps({"answer": precise_answer}))
        sys.exit(0)
    
    # Otherwise, fall back to a descriptive summary from Wikipedia
    wiki_summary = search_wikipedia_summary(query)

    if wiki_summary:
        print(json.dumps({"answer": wiki_summary}))
        sys.exit(0)
    else:
        print(json.dumps({"error": "Could not find a relevant answer for that query."}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()