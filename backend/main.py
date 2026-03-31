# Main FastAPI Application

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Welcome in AI Rag Accountant"}
