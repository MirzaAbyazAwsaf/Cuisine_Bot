import streamlit as st
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from vector_db import get_retriever

st.set_page_config(page_title="Pizza Review Bot",  layout="centered")
st.title(":pizza: Pizza Review Bot")
st.caption("Ask me anything about pizza restaurant reviews!")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

@st.cache_resource
def load_chain():
    retriever = get_retriever()
    model = OllamaLLM(model="llama3.2")
    template = """You are an expert in answering questions about a pizza restaurant.

Here are some relevant reviews: {reviews}

Here is the question to answer: {question}"""
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model
    return retriever, chain

retriever, chain = load_chain()

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg:
            with st.expander("Source Reviews"):
                for src in msg["sources"]:
                    st.markdown(f"⭐ {src['rating']}/5 | {src['date']}")
                    st.markdown(f"_{src['text']}_")
                    st.divider()

if question := st.chat_input("Ask a question about Pizza restaurants:"):
    st.session_state.chat_history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reviews = retriever.invoke(question)
            result = chain.invoke({"reviews": reviews, "question": question})
        st.markdown(result)

        sources = []
        for doc in reviews:
            sources.append({
                "text": doc.page_content,
                "rating": doc.metadata.get("rating", "N/A"),
                "date": doc.metadata.get("date", "N/A"),
            })
        with st.expander("Source Reviews"):
            for src in sources:
                st.markdown(f"⭐ {src['rating']}/5 | {src['date']}")
                st.markdown(f"_{src['text']}_")
                st.divider()

    st.session_state.chat_history.append({"role": "assistant", "content": result, "sources": sources})
