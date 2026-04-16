# AIRag Application

## Overview
AIRag is a Retrieval-Augmented Generation (RAG) application for financial document analysis. Upload CSV or text files containing financial data, and ask questions using natural language. The system uses OpenAI embeddings for document retrieval and GPT for generating answers grounded in your data.

## Features
- **Document Ingestion** – Upload CSV or plain-text files; documents are chunked, embedded, and stored in a vector store.
- **Financial Analysis** – CSV files are automatically analyzed with descriptive statistics, growth rates, and correlations.
- **RAG Q&A** – Ask natural-language questions and get answers grounded in your uploaded documents.
- **Web UI** – Clean, responsive frontend for uploading files and chatting with your data.
- **REST API** – Full FastAPI backend with OpenAPI docs at `/docs`.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/king4arabs/AIRag.git
   cd AIRag
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env and set your OPENAI_API_KEY
   ```

## Usage
Start the application:
```bash
./run.sh
```

Then open [http://localhost:8000](http://localhost:8000) in your browser.

### API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Serve frontend UI |
| `GET` | `/api/health` | Health check & vector store status |
| `POST` | `/api/upload` | Upload a file (CSV or text) for ingestion |
| `POST` | `/api/ingest-text` | Ingest raw text directly |
| `POST` | `/api/query` | Ask a question (RAG pipeline) |
| `DELETE` | `/api/documents` | Clear all ingested documents |

## Structure
- **src/** – Core application logic
  - `config.py` – Configuration from environment variables
  - `llm_provider.py` – OpenAI LLM and embedding integration
  - `vector_store.py` – NumPy-based vector store with cosine similarity
  - `financial_analyzer.py` – Pandas-based financial data analysis
  - `rag_pipeline.py` – RAG orchestration (ingest → chunk → embed → query)
- **backend/** – FastAPI application and API routes
- **frontend/** – HTML/CSS/JS web interface

## Contributing
Contributions are welcome! Please open an issue or submit a pull request.