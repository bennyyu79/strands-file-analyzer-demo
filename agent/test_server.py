"""Simple test server for LangGraph migration."""

from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Test Server")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "framework": "langgraph"}

@app.get("/")
async def root():
    return {"message": "LangGraph File Investigator Agent"}

if __name__ == "__main__":
    print("Starting test server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
