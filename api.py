import re
from collections import OrderedDict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from vector_db import get_retriever

FIELD_PATTERNS = {
    "address": re.compile(r"Area:\s*(.+)", re.IGNORECASE),
    "cuisine": re.compile(r"Cuisine:\s*(.+)", re.IGNORECASE),
    "price": re.compile(r"Price Range:\s*(.+)", re.IGNORECASE),
}
RATING_RE = re.compile(r"Rating:\s*([\d.]+)\s*/\s*5", re.IGNORECASE)
REVIEW_RE = re.compile(r"Review:\s*(.+)", re.IGNORECASE)
PAGE_RE = re.compile(r"Page\s*\d+\s*of\s*\d+", re.IGNORECASE)

PRICE_LABELS = {
    "$": "Budget",
    "$$": "Mid-range",
    "$$$": "Premium",
    "$$$$": "Fine dining",
}


def price_label(raw):
    if not raw:
        return None
    return PRICE_LABELS.get(raw.strip(), raw.strip())


def price_tier(raw):
    if not raw:
        return None
    return raw.strip().count("$") or None


def detect_price_filter(question):
    q = question.lower()
    if any(w in q for w in ["cheapest", "cheap", "budget", "affordable", "inexpensive", "low price"]):
        return {1}
    if any(w in q for w in ["expensive", "pricey", "costly"]):
        return {3, 4}
    if any(w in q for w in ["premium", "fine dining", "high end", "high-end", "luxury"]):
        return {4}
    if "mid" in q and "range" in q:
        return {2}
    return None


def sanitize_name(name):
    return name.replace("\ufffd", "'").strip()


def extract_field(content, pattern):
    for match in pattern.findall(content):
        text = match.strip().strip('"')
        if text:
            return text
    return None


def parse_restaurant(name, contents):
    rating_values = []
    reviews = []
    details = {key: None for key in FIELD_PATTERNS}

    for content in contents:
        content = PAGE_RE.sub("", content)
        for key, pattern in FIELD_PATTERNS.items():
            if details[key] is None:
                details[key] = extract_field(content, pattern)
        rating_values.extend(float(r) for r in RATING_RE.findall(content))
        for review in REVIEW_RE.findall(content):
            text = review.strip().strip('"')
            if len(text) >= 20 and text not in reviews:
                reviews.append(text)

    rating = round(sum(rating_values) / len(rating_values), 1) if rating_values else None
    return {
        "name": sanitize_name(name),
        "address": details["address"],
        "cuisine": details["cuisine"],
        "price": price_label(details["price"]),
        "price_tier": price_tier(details["price"]),
        "rating": rating,
        "reviews": reviews[:3],
    }


def get_full_contents(store, name):
    try:
        result = store.get(where={"restaurant": name}, include=["documents"])
    except Exception:
        return []
    return [doc for doc in result.get("documents") or [] if doc]


def build_answer(reviews, question, store):
    ranked_names = []
    for doc in reviews:
        name = sanitize_name(doc.metadata.get("restaurant") or "Unknown restaurant")
        if name not in ranked_names:
            ranked_names.append(name)
    rank = {name: i for i, name in enumerate(ranked_names)}

    tiers = detect_price_filter(question)
    if tiers:
        restaurants = load_all_restaurants(store)
        restaurants = [r for r in restaurants if r.get("price_tier") in tiers]
        restaurants.sort(key=lambda r: (rank.get(r["name"], 10**9), -(r["rating"] or 0)))
    else:
        restaurants = []
        for name in ranked_names:
            contents = get_full_contents(store, name)
            if not contents:
                continue
            parsed = parse_restaurant(name, contents)
            if parsed["rating"] is not None or parsed["reviews"]:
                restaurants.append(parsed)

    for r in restaurants[:]:
        r.pop("price_tier", None)
    restaurants = restaurants[:8]

    message = summarize(restaurants, question)
    return {"message": message, "restaurants": restaurants}


def load_all_restaurants(store):
    result = store.get(include=["documents", "metadatas"])
    grouped = OrderedDict()
    for doc, meta in zip(result.get("documents") or [], result.get("metadatas") or []):
        name = (meta or {}).get("restaurant") or "Unknown restaurant"
        grouped.setdefault(name, []).append(doc)

    restaurants = []
    for name, contents in grouped.items():
        parsed = parse_restaurant(name, contents)
        if parsed["rating"] is not None or parsed["reviews"]:
            restaurants.append(parsed)
    return restaurants


def summarize(restaurants, question):
    if not restaurants:
        return "I could not find that information in my database."

    listing = "\n".join(
        f"- {r['name']} | Area: {r['address'] or 'n/a'} | Cuisine: {r['cuisine'] or 'n/a'} | Price: {r['price'] or 'n/a'} | Rating: {r['rating'] or 'n/a'}/5"
        for r in restaurants
    )
    template = """You are a restaurant concierge in Bangladesh. A customer asked a question.

Question: {question}

The restaurants below are ranked by how well they match:

{listing}

Write 2-3 natural sentences that directly answer the question. For recommendation questions, name the top matching restaurants with a key detail each (cuisine or rating). For a question about one specific restaurant, describe that restaurant directly. Never recommend restaurants outside the list, and never invent prices, ratings, addresses, or other details not listed."""

    prompt = ChatPromptTemplate.from_template(template)
    return prompt.pipe(model).invoke({"listing": listing, "question": question}).strip()


app = FastAPI(title="Bangladesh Restaurant Bot")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

retriever = get_retriever()
store = retriever.vectorstore
model = OllamaLLM(model="llama3.2", temperature=0.2)


class Query(BaseModel):
    question: str


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/query")
def query(payload: Query):
    reviews = retriever.invoke(payload.question)
    answer = build_answer(reviews, payload.question, store)
    sources = [
        {
            "restaurant": review.metadata.get("restaurant"),
            "source": review.metadata.get("source"),
            "snippet": review.page_content[:250],
        }
        for review in reviews
    ]
    return {"answer": answer, "sources": sources}