import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# Ensure stdout uses UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add backend directory to sys.path to ensure module resolution works regardless of CWD
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from rag_pipeline import query_assistant

# Request Schema
class ChatRequest(BaseModel):
    message: str

app = FastAPI(title="Mutual Fund FAQ Assistant API")

# Add CORS middleware to support potential development split
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Endpoint for Chat
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    query = request.message.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query message cannot be empty")
        
    try:
        response_data = query_assistant(query)
        return response_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

# Mount Static Files from Frontend directory
# This mounts the directory to serve index.html, style.css, and app.js directly at the root
frontend_dir = os.path.join(os.path.dirname(backend_dir), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")
else:
    print(f"Warning: Frontend directory not found at {frontend_dir}. API will run without static file hosting.")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting Mutual Fund FAQ Assistant server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)

