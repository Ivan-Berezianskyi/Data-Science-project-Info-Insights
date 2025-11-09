# Chat History Backend API

A scalable FastAPI backend for managing AI user chat history with PostgreSQL.

📖 **For detailed architecture documentation, see [ARCHITECTURE.md](./ARCHITECTURE.md)**

## Features

- PostgreSQL database connection with SQLAlchemy ORM
- Chat and Message models with proper relationships
- RESTful API endpoints for CRUD operations
- Optional pagination for read requests
- Scalable service layer architecture
- Type-safe Pydantic schemas for validation

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Database

Create a `.env` file in the `backend` directory:

```bash
cp .env.example .env
```

Then edit `.env` and update with your database credentials:

```env
DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/chat_history
```

**Note:** The `.env` file is automatically loaded by the application. The `DATABASE_URL` in `.env` will override the default value in `config.py`.

### 3. Initialize Database

Run the initialization script to create tables:

```bash
python -c "from backend.database import init_db; from backend.models import Chat, Message; init_db()"
```

Or from the backend directory:
```bash
cd backend
python -c "from database import init_db; from models import Chat, Message; init_db()"
```

### 4. Run the Server

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

API documentation will be available at: `http://localhost:8000/docs`

## API Endpoints

### Chats

- `POST /api/chats/` - Create a new chat
- `GET /api/chats/` - Get list of chats (with optional pagination: `?page=1&page_size=20`)
- `GET /api/chats/{chat_id}` - Get detailed chat information
- `PUT /api/chats/{chat_id}` - Update a chat
- `DELETE /api/chats/{chat_id}` - Delete a chat

### Messages

- `POST /api/messages/` - Create a new message
- `GET /api/messages/chat/{chat_id}` - Get all messages for a chat, time sorted by createdAt (with optional pagination)
- `GET /api/messages/{message_id}` - Get a specific message
- `PUT /api/messages/{message_id}` - Update a message
- `DELETE /api/messages/{message_id}` - Delete a message

## Project Structure

```
backend/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration settings
├── database.py          # Database connection and session management
├── models.py            # SQLAlchemy ORM models
├── schemas.py           # Pydantic schemas for API validation
├── services/            # Business logic layer
│   ├── chat_service.py
│   └── message_service.py
└── routers/             # API route handlers
    ├── chats.py
    └── messages.py
```

## Models

### Chat
- `id`: Primary key
- `notebooks`: Array of strings (notebook identifiers)
- `created_at`: Timestamp
- `updated_at`: Timestamp

### Message
- `id`: Primary key
- `chat_id`: Foreign key to Chat
- `role`: Enum ('user', 'ai', 'system')
- `content`: Text content
- `created_at`: Timestamp (used for sorting)
- `updated_at`: Timestamp

## Future Scalability

The architecture is designed for scalability:

- Service layer separation allows easy addition of business logic
- Pagination support for large datasets
- Connection pooling configured for high concurrency
- Type-safe schemas make API evolution easier
- Ready for Alembic migrations for production schema management

