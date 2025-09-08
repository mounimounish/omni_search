from fastapi import FastAPI
from search_logic import browser_search

app = FastAPI()

@app.get("/search")
async def search(query: str):
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
    return result_data
