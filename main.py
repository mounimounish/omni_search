from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
import asyncio
from search_logic import browser_search

app = FastAPI()

class QueryRequest(BaseModel):
    queries: List[str]

@app.post("/search")
async def search(request: QueryRequest) -> List[Dict[str, Any]]:
    """
    Performs a search for one or more queries and returns the results.
    Each query is processed concurrently for high efficiency.
    """
    tasks = [browser_search(query) for query in request.queries]
    results = await asyncio.gather(*tasks)

    formatted_results = []
    for sources, query in results:
        if sources:
            result_data = {
                "type": "summary",
                "query": query,
                "sources": sources
            }
        else:
            result_data = {"error": "Could not find a relevant answer for that query."}
        formatted_results.append(result_data)
        
    return formatted_results