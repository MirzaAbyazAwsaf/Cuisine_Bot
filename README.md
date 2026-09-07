# Pizza Review Bot

Ask questions about pizza restaurant reviews using a RAG (Retrieval-Augmented Generation) pipeline powered by LangChain, Ollama, and ChromaDB.

## Setup

1. Install [Ollama](https://ollama.com) and pull the required models:
   ```bash
   ollama pull llama3.2
   ollama pull mxbai-embed-large
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Run

**Web UI (Streamlit):**
```bash
streamlit run app.py
```

**CLI:**
```bash
python main.py
```

## Project Structure

- `app.py` - Streamlit web interface
- `main.py` - CLI interface
- `vector_db.py` - ChromaDB vector store setup
- `realistic_restaurant_reviews.csv` - Review dataset
- `requirements.txt` - Python dependencies
