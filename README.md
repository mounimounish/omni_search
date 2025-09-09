# Omni-Search
A Versatile Search Microservice for AI-Driven Systems
Omni-Search is a lightweight, browser-like microservice designed to act as a core component for an AI-driven operating system or any larger model requiring external information. It takes user queries, intelligently performs web searches, and returns concise, relevant summaries from top web results in a structured format.

The primary goal of this service is to abstract away the complexity of web scraping and information retrieval, allowing the main AI model to focus on processing and generating responses.

## ✨ Features
General Web Search: Performs broad, undiscriminating searches using DuckDuckGo to find relevant web pages for any query.

Robust Fallback: If the primary web search fails to return results, the service automatically falls back to a reliable Wikipedia API to ensure a summary is always provided for encyclopedic queries.

Dynamic Summarization: Fetches content from top web links and provides a concise, one-page summary, avoiding large, unwieldy chunks of text.

Asynchronous & Efficient: Designed with asyncio to handle multiple queries concurrently, making it highly efficient for multi-tasking AI applications.

API & CLI Interface: Can be used as a standalone command-line tool for testing or as a RESTful API endpoint for seamless integration into larger systems.

# #📦 Installation
To get started, first, create and activate a Python virtual environment to manage dependencies:

Bash

python -m venv .venv
## On Windows:
.venv\Scripts\activate
## On macOS/Linux:
source .venv/bin/activate
Next, install the required libraries using pip. The following command installs all the necessary dependencies:

Bash

pip install fastapi "uvicorn[standard]" aiohttp ddgs beautifulsoup4
🚀 Usage
The service can be used in two ways: via the command-line interface (CLI) or as a RESTful API.

1. Command-Line Interface (CLI)
This is ideal for testing and quick information retrieval.

Bash

# Search for a single query
python search_logic.py "What is quantum computing"

# Search for multiple queries at once
python search_logic.py "pm of india" "top leetcode problems" "what is photosynthesis"
Example Output (JSON):

JSON

[
  {
    "type": "summary",
    "query": "What is quantum computing",
    "sources": [
      {
        "url": "https://en.wikipedia.org/wiki/Quantum_computing",
        "content": "Quantum computing is a type of computation whose operations can harness the phenomena of quantum mechanics, such as superposition, entanglement and quantum interference, to perform calculations. Computers that do this are known as quantum computers. Though current quantum computers are too small to outperform a typical modern classical computer for practical applications, they have a lot of potential when it comes to problems that classical computers struggle with, such as cryptography and the simulation of molecules...."
      }
    ]
  },
  {
    "type": "summary",
    "query": "pm of india",
    "sources": [
      {
        "url": "https://en.wikipedia.org/wiki/Prime_Minister_of_India",
        "content": "The prime minister of India is the chief executive of the Government of India. In India's parliamentary system, the president is the ceremonial head of state, while the prime minister and the Council of Ministers are the real executive authority. The prime minister is the leader of the main government in the Union of India...."
      }
    ]
  }
]
2. RESTful API
To run the service as a web API, you'll use uvicorn.

Bash

uvicorn main:app --reload
The API will be available at http://127.0.0.1:8000. You can send a POST request to the /search endpoint with a list of queries.

Example Request (using curl):

Bash

curl -X POST "http://127.0.0.1:8000/search" \
-H "Content-Type: application/json" \
-d '{
  "queries": [
    "what is Python",
    "who is the CEO of Google"
  ]
}'
Example Response:

The response will be a JSON array, similar to the CLI output, containing a summary for each query.

## 📂 File Structure
The project has a clean and simple structure.

/omni-search
├── main.py             # FastAPI application and API endpoint
├── search_logic.py     # Core search logic and helper functions
├── .gitignore          # Tells Git which files to ignore
├── requirements.txt    # Lists all project dependencies
└── README.md           # The file you are reading now!
## 📜 License
This project is open source and available under the MIT License.