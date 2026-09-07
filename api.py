from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from vector_db import get_retriever


def format_reviews(reviews):
    parts = []
    for review in reviews:
        restaurant = review.metadata.get("restaurant", "Unknown")
        source = review.metadata.get("source", "")
        parts.append(f"[Restaurant: {restaurant} | Source: {source}]\n{review.page_content}")
    return "\n\n---\n\n".join(parts)


app = FastAPI(title="Bangladesh Restaurant Bot")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

retriever = get_retriever()
model = OllamaLLM(model="llama3.2")

template = """
    You are an expert on restaurants in Bangladesh.

    Here are some relevant reviews: {reviews}

    Here is the question to answer: {question}

    Answer the question based only on the reviews above. Always state the restaurant name, area, cuisine, and price range when present. Summarize the reviews using the ratings and comments. If the reviews do not contain the restaurant or information asked about, say "I could not find that information in my database."
    """

prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model


class Query(BaseModel):
    question: str


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/query")
def query(payload: Query):
    reviews = retriever.invoke(payload.question)
    answer = chain.invoke({"reviews": format_reviews(reviews), "question": payload.question})
    sources = [
        {
            "restaurant": review.metadata.get("restaurant"),
            "source": review.metadata.get("source"),
            "snippet": review.page_content[:250],
        }
        for review in reviews
    ]
    return {"answer": answer, "sources": sources}