from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client
from functools import lru_cache
import os

@lru_cache(maxsize=128)
def embed_query_cached(text: str) -> list[float]:
    return embed_query(text)


load_dotenv()

# Supabase setup
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
sb = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# OpenAI setup
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You are MovieLover AI, a professional assistant for movie lovers.

Your responsibilities:
- Help users find movies they will enjoy
- Ask follow-up questions if preferences are unclear
- Recommend a maximum of 5 movies at a time
- Give a short explanation for each movie
- Do not repeat previously suggested movies
- Be friendly, concise, and knowledgeable

You may ask about:
- Genres
- Mood
- Time period (classic, modern, recent)
- Language
- Movies the user already loves
"""

# Embedding function
def embed_query(text: str) -> list[float]:
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print("Embedding error:", e)
        return []

# Semantic search using Supabase
def semantic_search(query_text: str) -> list[dict]:
    emb_q = embed_query(query_text)
    if not emb_q:
        return []
    
    try:
        res = sb.rpc("match_chunks", {"query_embedding": emb_q, "match_count": 3}).execute()
        rows = res.data or []
        print("Supabase RAG OUTPUT:", rows)
        return rows
    except Exception as e:
        print("Supabase RPC error:", e)
        return []

# FastAPI setup
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat(req: ChatRequest):
    user_message = req.message

    # Conduct semantic search
    rag_rows = semantic_search(user_message)

    # Format retrieved context
    context = "\n\n".join(
        f"[Source {i+1} | sim={row.get('similarity'):.3f}]\n{row.get('content','')}"
        for i, row in enumerate(rag_rows)
    )

    # RAG system message
    rag_message = {
        "role": "system",
        "content": (
            "Use the retrieved context below to answer. If it doesn't contain the answer, say so.\n\n"
            f"RETRIEVED CONTEXT:\n{context if context else '(no matches)'}"
        )
    }

    # User message
    user_msg = {"role": "user", "content": user_message}

    # Full conversation including system prompt
    full_prompt = f"""
    {SYSTEM_PROMPT}

    RETRIEVED CONTEXT:
    {context if context else '(no matches)'}

    User: {user_message}

    Answer concisely:
    """


    # Call OpenAI responses API
    try:
        response = client.responses.create(
            model="gpt-5-nano",
            input=full_prompt
        )

        # Extract the reply text safely
        reply = getattr(response, "output_text", None)
        if not reply and hasattr(response, "output"):
            try:
                reply = response.output[0].content[0].text
            except Exception:
                reply = "Sorry, I couldn't generate a reply."
    except Exception as e:
        print("OpenAI API error:", e)
        reply = "Sorry, there was an error generating a reply."

    return {"reply": reply}
