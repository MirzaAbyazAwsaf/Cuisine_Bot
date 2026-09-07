from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import glob
import os
import re

RESTAURANT_RE = re.compile(r"Restaurant:\s*(.+)")

def split_restaurants(text, source):
    blocks = re.split(r"(?=Restaurant:)", text)
    documents = []
    for block in blocks:
        match = RESTAURANT_RE.search(block)
        if not match:
            continue
        documents.append(
            Document(
                page_content=block.strip(),
                metadata={
                    "restaurant": match.group(1).strip(),
                    "source": source,
                },
            )
        )
    return documents


def get_retriever():
    embeddings = OllamaEmbeddings(model="mxbai-embed-large")

    db_location = "./chroma_db"
    add_docs = not os.path.exists(db_location)

    documents = []
    if add_docs:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
        )

        pdf_files = glob.glob("data/*.pdf")
        if not pdf_files:
            raise FileNotFoundError(
                "No PDF files found in data/. Place your restaurant PDFs in data/ first."
            )

        for pdf in pdf_files:
            pages = PyPDFLoader(pdf).load()
            text = "\n".join(page.page_content for page in pages)
            for block in split_restaurants(text, pdf):
                documents.extend(splitter.split_documents([block]))

    vector_store = Chroma(
        collection_name="restaurant_reviews",
        persist_directory=db_location,
        embedding_function=embeddings,
    )

    if add_docs:
        vector_store.add_documents(documents=documents)

    return vector_store.as_retriever(search_kwargs={"k": 6})