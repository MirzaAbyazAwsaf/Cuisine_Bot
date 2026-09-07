from glob import escape

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


def main():
    retriever = get_retriever()
    model = OllamaLLM(model="llama3.2")

    template = """
    You are an expert on restaurants in Bangladesh especially in Dhaka .

    Here are some relevant reviews: {reviews}

    Here is the question to answer: {question}

    Answer the question based only on the reviews above. Always state the restaurant name, area, cuisine, and price range when present. Summarize the reviews using the ratings and comments. If the reviews do not contain the restaurant or information asked about, say "I could not find that information in my database."
    """

    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model

    while True:
        print("-------------------------------------------------------------------")
        question = input("Ask a question about restaurants in Bangladesh (q to quit): ")
        if question == "q":
            break

        reviews = retriever.invoke(question)
        results = chain.invoke({"reviews": format_reviews(reviews), "question": question})
        print(results)


if __name__ == "__main__":
    main()
