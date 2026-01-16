from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client
import os

load_dotenv()

SUPABASE_URL =os.env.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY=os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
sb= create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


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

messages = [
    {"role": "system", "content": SYSTEM_PROMPT}
]

user_preferences = {
    "genres": set(),
    "mood": None,
    "era": None,
    "liked_movies": set()
}

def embed_query(text: str) -> list[float]:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    return response.data[0].embedding

# takes as input a query, conducts the search, returns context
def semantic_search(query_text: str) -> list[dict]:
    emb_q = embed_query(query_text)
    res = sb.rpc("match_chunks", {"query_embedding": emb_q, "match_count" :5}).execute()
    rows = res.data or []
    # for easier debugging
    print("RAG OUTPUT:", rows)
    return rows

def extract_preferences(text: str):
    genres = [
        "action", "comedy", "drama", "horror", "romance",
        "sci-fi", "thriller", "fantasy", "animation", "mystery"
    ]

    moods = [
        "dark", "funny", "feel-good", "emotional",
        "intense", "relaxing"
    ]

    eras = [
        "classic", "old", "modern", "recent", "new"
    ]

    text_lower = text.lower()

    for genre in genres:
        if genre in text_lower:
            user_preferences["genres"].add(genre.title())

    for mood in moods:
        if mood in text_lower:
            user_preferences["mood"] = mood

    for era in eras:
        if era in text_lower:
            user_preferences["era"] = era

def add_preferences_to_context():
    summary = []

    if user_preferences["genres"]:
        summary.append(f"Genres: {', '.join(user_preferences['genres'])}")

    if user_preferences["mood"]:
        summary.append(f"Mood: {user_preferences['mood']}")

    if user_preferences["era"]:
        summary.append(f"Era: {user_preferences['era']}")

    if summary:
        messages.append({
            "role": "system",
            "content": "User preferences so far: " + " | ".join(summary)
        })

print("\n🎬 Welcome to MovieLover AI!")
print("Ask for recommendations, genres, or movies similar to ones you love.")
print("Type 'exit' to quit.\n")

while True:
    user_input = input("You: ").strip()

    if user_input.lower() == "exit":
        print("\n🍿 Thanks for using MovieLover AI. Enjoy your movies!")
        break

    extract_preferences(user_input)

    messages.append({"role": "user", "content": user_input})

    add_preferences_to_context()

    response = client.responses.create(
        model="gpt-5-nano",
        input=messages
    )

    ai_reply = response.output_text.strip()

    print("\n🎥 MovieLover AI:")
    print(ai_reply)
    print()

    messages.append({"role": "assistant", "content": ai_reply})
