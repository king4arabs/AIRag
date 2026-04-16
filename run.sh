#!/bin/bash

# Start the AIRag application
set -e

# Ensure data directories exist
mkdir -p data/uploads data/vector_store

# Start the FastAPI server
echo "Starting AIRag server on http://0.0.0.0:8000"
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
