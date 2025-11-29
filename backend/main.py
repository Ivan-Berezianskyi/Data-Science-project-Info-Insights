from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from routers import chats, messages, chat_completion, notebooks

# To initialize database tables, run: python init_database.py
# Or use Alembic migrations for production

app = FastAPI(
    title="Chat History API",
    description="API for managing AI user chat history with PostgreSQL",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chats.router)
app.include_router(messages.router)
app.include_router(chat_completion.router)
app.include_router(notebooks.router)


@app.get("/")
def read_root():
    return {
        "message": "Chat History API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)