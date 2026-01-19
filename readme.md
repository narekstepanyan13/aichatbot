MovieLover AI Backend








This is the FastAPI backend for MovieLover AI, a professional assistant for movie lovers. It handles chat requests, semantic search with Supabase, OpenAI responses, and serves frontend files directly from the main folder.

main.py Explained
1. Imports and Setup

    ```python
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse, RedirectResponse
    from pydantic import BaseModel
    from dotenv import load_dotenv
    from openai import OpenAI
    from supabase import create_client
    from functools import lru_cache
    import os
    ```


    • Loads all required modules for FastAPI, environment, AI, Supabase, and caching.

2. Caching Embeddings

    ```python
    @lru_cache(maxsize=128)
    def embed_query_cached(text: str) -> list[float]:
        return embed_query(text)
    ```

    • Caches embedding results to avoid repeated API calls.

3. Environment Variables & Clients

    ```python
    load_dotenv()

    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    ```

    • Reads keys from .env and initializes Supabase and OpenAI clients.

4. System Prompt

    ```python
    SYSTEM_PROMPT = """
    You are MovieLover AI, a professional assistant for movie lovers.
    ...
    """
    ```
    ### AI Behavior Guidelines
        • Guides AI behavior:

        • Recommend max 5 movies

        • Ask follow-ups if unclear

        • Friendly and concise

        • No repeated suggestions

5. Embedding Function
    ```python
    def embed_query(text: str) -> list[float]:
        ...
    ```

    • Converts user text into vector embeddings using OpenAI.

6. Semantic Search
    ```python
    def semantic_search(query_text: str) -> list[dict]:
        ...
    ```

    • Uses Supabase RPC match_chunks to find similar movie content.

    • Returns the top 3 matches.

7. FastAPI Initialization
    ```python 
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    ```

    • Sets up FastAPI server with CORS enabled for frontend communication.

8. Chat Request Model
    ```python
    class ChatRequest(BaseModel):
        message: str
    ```

    • Defines the payload structure for /chat POST requests.

9. Chat Endpoint
    ```python
    @app.post("/chat")
    async def chat(req: ChatRequest):
        ...
    ```

    Workflow:

    ```bash
    1. Receives user input

    2. Performs semantic search in Supabase

    3. Combines system prompt + retrieved context + user query

    4. Calls OpenAI gpt-5-nano model

    5. Returns the reply as JSON
    ```

10. Serve Frontend Files

    ```python
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    @app.get("/index.html", include_in_schema=False)
    async def serve_index():
        return FileResponse(os.path.join(BASE_DIR, "index.html"))

    @app.get("/", include_in_schema=False)
    async def root_redirect():
        return RedirectResponse(url="/index.html")

    @app.get("/style.css", include_in_schema=False)
    async def serve_css():
        return FileResponse(os.path.join(BASE_DIR, "style.css"))

    @app.get("/script.js", include_in_schema=False)
    async def serve_js():
        return FileResponse(os.path.join(BASE_DIR, "script.js"))
    ```

    • Serves HTML, CSS, JS from the main folder without requiring a /static directory.

    • / redirects to /index.html