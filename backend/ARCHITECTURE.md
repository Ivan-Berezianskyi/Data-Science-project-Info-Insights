# Chat History API - Architecture Documentation

## Table of Contents

1. [Overview](#overview)
2. [Architecture Design](#architecture-design)
3. [Project Structure](#project-structure)
4. [Database Layer](#database-layer)
5. [Service Layer](#service-layer)
6. [API Layer](#api-layer)
7. [Request/Response Flow](#requestresponse-flow)
8. [API Endpoints Reference](#api-endpoints-reference)
9. [Error Handling](#error-handling)
10. [Configuration](#configuration)
11. [Design Decisions](#design-decisions)

---

## Overview

The Chat History API is a RESTful backend service built with FastAPI and PostgreSQL, designed to store and manage AI user chat history. The system is architected for scalability, maintainability, and easy extension with new features.

### Key Features

- **Scalable Architecture**: Layered architecture with clear separation of concerns
- **Type Safety**: Full type hints and Pydantic validation
- **Database Abstraction**: SQLAlchemy ORM for database operations
- **Pagination Support**: Optional pagination for all read operations
- **Error Handling**: Comprehensive error handling with proper HTTP status codes
- **Environment Configuration**: Support for `.env` files for configuration

---

## Architecture Design

### Layered Architecture

The application follows a **3-layer architecture** pattern:

```
┌─────────────────────────────────────┐
│         API Layer (Routers)         │  ← HTTP endpoints, request validation
├─────────────────────────────────────┤
│       Service Layer (Services)       │  ← Business logic, data operations
├─────────────────────────────────────┤
│    Database Layer (Models/ORM)      │  ← Database schema, SQLAlchemy models
└─────────────────────────────────────┘
```

#### 1. **API Layer (Routers)**
- **Location**: `routers/`
- **Responsibility**: 
  - Handle HTTP requests/responses
  - Request validation using Pydantic schemas
  - Dependency injection for database sessions
  - Error handling and HTTP status codes
- **Files**: `routers/chats.py`, `routers/messages.py`

#### 2. **Service Layer**
- **Location**: `services/`
- **Responsibility**:
  - Business logic implementation
  - Database operations (CRUD)
  - Data validation and transformation
  - Error handling for business rules
- **Files**: `services/chat_service.py`, `services/message_service.py`

#### 3. **Database Layer**
- **Location**: `models.py`, `database.py`
- **Responsibility**:
  - Database schema definition
  - SQLAlchemy ORM models
  - Database connection management
  - Session management

### Data Flow

```
Client Request
    ↓
FastAPI Router (routers/*.py)
    ↓
Pydantic Schema Validation
    ↓
Service Layer (services/*.py)
    ↓
SQLAlchemy ORM (models.py)
    ↓
PostgreSQL Database
    ↓
Response (Pydantic Schema)
    ↓
Client Response
```

---

## Project Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── config.py               # Configuration settings (env vars, defaults)
├── database.py             # Database connection and session management
├── models.py               # SQLAlchemy ORM models
├── schemas.py              # Pydantic schemas for API validation
├── requirements.txt        # Python dependencies
├── init_database.py        # Database initialization script
├── create_database.py      # Database creation helper
├── test_env.py            # Environment variable testing
│
├── routers/                # API route handlers
│   ├── __init__.py
│   ├── chats.py           # Chat endpoints
│   └── messages.py        # Message endpoints
│
└── services/              # Business logic layer
    ├── __init__.py
    ├── chat_service.py    # Chat business logic
    └── message_service.py # Message business logic
```

### File Responsibilities

#### `main.py`
- FastAPI application initialization
- CORS middleware configuration
- Router registration
- Health check endpoints

#### `config.py`
- Environment variable loading (`.env` file support)
- Configuration defaults
- Settings management using Pydantic Settings

#### `database.py`
- SQLAlchemy engine creation
- Database session factory
- Session dependency for FastAPI
- Database initialization function

#### `models.py`
- SQLAlchemy model definitions
- Database table schemas
- Model relationships

#### `schemas.py`
- Pydantic models for request/response validation
- Data transfer objects (DTOs)
- Pagination schemas

---

## Database Layer

### Database Models

#### Chat Model

```python
class Chat(Base):
    __tablename__ = "chats"
    
    id: Integer (Primary Key)
    notebooks: ARRAY(String)  # Array of notebook identifiers
    created_at: DateTime (auto-generated)
    updated_at: DateTime (auto-updated)
    
    # Relationship
    messages: One-to-Many relationship with Message
```

**Purpose**: Stores chat configuration and metadata. Each chat can have multiple messages.

**Key Features**:
- `notebooks` field is an array of strings (PostgreSQL ARRAY type)
- Automatic timestamp management (`created_at`, `updated_at`)
- Cascade delete: deleting a chat deletes all associated messages

#### Message Model

```python
class Message(Base):
    __tablename__ = "messages"
    
    id: Integer (Primary Key)
    chat_id: Integer (Foreign Key → chats.id)
    role: String(20)  # 'user', 'ai', or 'system'
    content: Text
    created_at: DateTime (auto-generated, indexed)
    updated_at: DateTime (auto-updated)
    
    # Relationship
    chat: Many-to-One relationship with Chat
```

**Purpose**: Stores individual messages within a chat conversation.

**Key Features**:
- `role` field supports: 'user', 'ai', 'system'
- `created_at` is indexed for efficient time-based sorting
- Foreign key with CASCADE delete (messages deleted when chat is deleted)

### Database Connection

**Connection String Format**:
```
postgresql+psycopg://username:password@host:port/database_name?sslmode=require
```

**Connection Pooling**:
- Pool size: 10 connections
- Max overflow: 20 additional connections
- Pool pre-ping: Enabled (verifies connections before use)

### Database Initialization

The database is initialized using SQLAlchemy's `create_all()` method:

```python
Base.metadata.create_all(bind=engine)
```

This creates all tables defined in the models if they don't already exist.

---

## Service Layer

The service layer encapsulates all business logic and database operations. Services are implemented as static methods for stateless operations.

### ChatService

**Location**: `services/chat_service.py`

**Methods**:

1. **`create_chat(db, chat_data)`**
   - Creates a new chat with provided notebooks
   - Returns: `Chat` object

2. **`get_chat(db, chat_id)`**
   - Retrieves a chat by ID
   - Returns: `Chat` or `None`

3. **`get_chat_detail(db, chat_id)`**
   - Retrieves chat with message count
   - Returns: Dictionary with chat data and `messages_count`

4. **`get_chats(db, pagination)`**
   - Retrieves list of chats with optional pagination
   - Ordered by `created_at` descending (newest first)
   - Returns: Tuple of `(List[Chat], total_count)`

5. **`update_chat(db, chat_id, chat_data)`**
   - Updates chat fields (partial update supported)
   - Returns: Updated `Chat` or `None`

6. **`delete_chat(db, chat_id)`**
   - Deletes a chat (cascades to messages)
   - Returns: `True` if deleted, `False` if not found

7. **`chat_exists(db, chat_id)`**
   - Checks if chat exists
   - Returns: `True` or `False`

### MessageService

**Location**: `services/message_service.py`

**Methods**:

1. **`create_message(db, message_data)`**
   - Creates a new message
   - Validates chat exists
   - Returns: `Message` object
   - Raises: `HTTPException` if chat not found

2. **`get_message(db, message_id)`**
   - Retrieves a message by ID
   - Returns: `Message` or `None`

3. **`get_messages_by_chat(db, chat_id, pagination)`**
   - Retrieves all messages for a chat
   - **Sorted by `created_at` ascending** (oldest first)
   - Supports optional pagination
   - Validates chat exists
   - Returns: Tuple of `(List[Message], total_count)`
   - Raises: `HTTPException` if chat not found

4. **`update_message(db, message_id, message_data)`**
   - Updates message fields (partial update)
   - Returns: Updated `Message` or `None`

5. **`delete_message(db, message_id)`**
   - Deletes a message
   - Returns: `True` if deleted, `False` if not found

6. **`message_exists(db, message_id)`**
   - Checks if message exists
   - Returns: `True` or `False`

### Service Design Principles

1. **Stateless**: All methods are static, no instance state
2. **Single Responsibility**: Each service handles one entity type
3. **Error Handling**: Services raise appropriate exceptions
4. **Validation**: Business rule validation (e.g., chat existence)
5. **Pagination**: Consistent pagination support across read operations

---

## API Layer

### Router Structure

Routers are organized by resource type and use FastAPI's `APIRouter` for modular route definition.

#### Chat Router (`routers/chats.py`)

**Prefix**: `/api/chats`
**Tag**: `chats`

**Endpoints**:
- `POST /api/chats/` - Create chat
- `GET /api/chats/` - List chats (paginated)
- `GET /api/chats/{chat_id}` - Get chat details
- `PUT /api/chats/{chat_id}` - Update chat
- `DELETE /api/chats/{chat_id}` - Delete chat

#### Message Router (`routers/messages.py`)

**Prefix**: `/api/messages`
**Tag**: `messages`

**Endpoints**:
- `POST /api/messages/` - Create message
- `GET /api/messages/chat/{chat_id}` - Get messages for chat (paginated)
- `GET /api/messages/{message_id}` - Get message details
- `PUT /api/messages/{message_id}` - Update message
- `DELETE /api/messages/{message_id}` - Delete message

### Dependency Injection

FastAPI's dependency injection is used for database sessions:

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

This ensures:
- Database session is created for each request
- Session is properly closed after request
- Automatic transaction management

### Request Validation

All requests are validated using Pydantic schemas:
- **Request bodies**: Validated against create/update schemas
- **Query parameters**: Validated with type hints and constraints
- **Path parameters**: Validated as integers

### Response Serialization

All responses are serialized using Pydantic response models:
- Automatic conversion from SQLAlchemy models to Pydantic models
- Type-safe response structures
- Consistent response formats

---

## Request/Response Flow

### Example: Creating a Chat

```
1. Client sends POST request to /api/chats/
   {
     "notebooks": ["notebook1", "notebook2"]
   }

2. FastAPI Router receives request
   - Validates request body against ChatCreate schema
   - Injects database session via get_db() dependency

3. Router calls ChatService.create_chat()
   - Service creates Chat model instance
   - Saves to database
   - Commits transaction

4. Service returns Chat model

5. Router converts Chat to ChatResponse schema
   - Includes: id, notebooks, created_at, updated_at

6. FastAPI serializes response to JSON
   {
     "id": 1,
     "notebooks": ["notebook1", "notebook2"],
     "created_at": "2024-01-01T12:00:00Z",
     "updated_at": "2024-01-01T12:00:00Z"
   }

7. Client receives response with 201 Created status
```

### Example: Getting Messages for a Chat

```
1. Client sends GET request to /api/messages/chat/1?page=1&page_size=20

2. FastAPI Router receives request
   - Validates path parameter (chat_id: int)
   - Validates query parameters (page, page_size)
   - Injects database session

3. Router calls MessageService.get_messages_by_chat()
   - Service validates chat exists
   - Queries messages filtered by chat_id
   - Orders by created_at ASC (oldest first)
   - Applies pagination (offset, limit)
   - Counts total messages

4. Service returns (List[Message], total_count)

5. Router converts to PaginatedMessageResponse
   - Includes: items, total, page, page_size, total_pages

6. FastAPI serializes response
   {
     "items": [...],
     "total": 50,
     "page": 1,
     "page_size": 20,
     "total_pages": 3
   }

7. Client receives paginated response
```

---

## API Endpoints Reference

### Chat Endpoints

#### 1. Create Chat

**Endpoint**: `POST /api/chats/`

**Request Body**:
```json
{
  "notebooks": ["notebook1", "notebook2"]
}
```

**Response** (201 Created):
```json
{
  "id": 1,
  "notebooks": ["notebook1", "notebook2"],
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

**Validation**:
- `notebooks`: Array of strings (default: empty array)

---

#### 2. List Chats

**Endpoint**: `GET /api/chats/`

**Query Parameters** (optional):
- `page` (int, default: 1, min: 1) - Page number
- `page_size` (int, default: 20, min: 1, max: 100) - Items per page

**Examples**:
- `GET /api/chats/` - Get all chats (no pagination)
- `GET /api/chats/?page=1&page_size=10` - First page, 10 items
- `GET /api/chats/?page=2` - Second page, default size

**Response** (200 OK):
```json
{
  "items": [
    {
      "id": 1,
      "notebooks": ["notebook1"],
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z"
    }
  ],
  "total": 25,
  "page": 1,
  "page_size": 20,
  "total_pages": 2
}
```

**Ordering**: Newest chats first (by `created_at` descending)

---

#### 3. Get Chat Details

**Endpoint**: `GET /api/chats/{chat_id}`

**Path Parameters**:
- `chat_id` (int) - Chat ID

**Response** (200 OK):
```json
{
  "id": 1,
  "notebooks": ["notebook1", "notebook2"],
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z",
  "messages_count": 15
}
```

**Error** (404 Not Found):
```json
{
  "detail": "Chat with id 1 not found"
}
```

---

#### 4. Update Chat

**Endpoint**: `PUT /api/chats/{chat_id}`

**Request Body** (all fields optional):
```json
{
  "notebooks": ["notebook1", "notebook2", "notebook3"]
}
```

**Response** (200 OK):
```json
{
  "id": 1,
  "notebooks": ["notebook1", "notebook2", "notebook3"],
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:30:00Z"
}
```

**Note**: Partial updates supported - only provided fields are updated

---

#### 5. Delete Chat

**Endpoint**: `DELETE /api/chats/{chat_id}`

**Response** (204 No Content):
- Empty response body

**Error** (404 Not Found):
```json
{
  "detail": "Chat with id 1 not found"
}
```

**Note**: Deleting a chat also deletes all associated messages (CASCADE)

---

### Message Endpoints

#### 1. Create Message

**Endpoint**: `POST /api/messages/`

**Request Body**:
```json
{
  "chat_id": 1,
  "role": "user",
  "content": "Hello, how are you?"
}
```

**Role Values**: `"user"`, `"ai"`, `"system"`

**Response** (201 Created):
```json
{
  "id": 1,
  "chat_id": 1,
  "role": "user",
  "content": "Hello, how are you?",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

**Error** (404 Not Found):
```json
{
  "detail": "Chat with id 1 not found"
}
```

---

#### 2. Get Messages for Chat

**Endpoint**: `GET /api/messages/chat/{chat_id}`

**Path Parameters**:
- `chat_id` (int) - Chat ID

**Query Parameters** (optional):
- `page` (int, default: 1, min: 1)
- `page_size` (int, default: 20, min: 1, max: 100)

**Examples**:
- `GET /api/messages/chat/1` - Get all messages (no pagination)
- `GET /api/messages/chat/1?page=1&page_size=50` - First page, 50 items

**Response** (200 OK):
```json
{
  "items": [
    {
      "id": 1,
      "chat_id": 1,
      "role": "user",
      "content": "Hello",
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-01T12:00:00Z"
    },
    {
      "id": 2,
      "chat_id": 1,
      "role": "ai",
      "content": "Hi there!",
      "created_at": "2024-01-01T12:00:05Z",
      "updated_at": "2024-01-01T12:00:05Z"
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

**Ordering**: Messages are sorted by `created_at` **ascending** (oldest first)

**Error** (404 Not Found):
```json
{
  "detail": "Chat with id 1 not found"
}
```

---

#### 3. Get Message Details

**Endpoint**: `GET /api/messages/{message_id}`

**Path Parameters**:
- `message_id` (int) - Message ID

**Response** (200 OK):
```json
{
  "id": 1,
  "chat_id": 1,
  "role": "user",
  "content": "Hello, how are you?",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

---

#### 4. Update Message

**Endpoint**: `PUT /api/messages/{message_id}`

**Request Body** (all fields optional):
```json
{
  "content": "Updated message content",
  "role": "system"
}
```

**Response** (200 OK):
```json
{
  "id": 1,
  "chat_id": 1,
  "role": "system",
  "content": "Updated message content",
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:30:00Z"
}
```

**Note**: Partial updates supported

---

#### 5. Delete Message

**Endpoint**: `DELETE /api/messages/{message_id}`

**Response** (204 No Content):
- Empty response body

---

## Error Handling

### HTTP Status Codes

- **200 OK**: Successful GET, PUT requests
- **201 Created**: Successful POST requests (resource created)
- **204 No Content**: Successful DELETE requests
- **404 Not Found**: Resource not found
- **422 Unprocessable Entity**: Validation errors
- **500 Internal Server Error**: Server errors

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Validation Errors

When request validation fails (422):

```json
{
  "detail": [
    {
      "loc": ["body", "notebooks"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### Common Error Scenarios

1. **Chat not found** (404):
   - Getting/updating/deleting non-existent chat
   - Creating message with non-existent chat_id

2. **Message not found** (404):
   - Getting/updating/deleting non-existent message

3. **Validation errors** (422):
   - Invalid field types
   - Missing required fields
   - Invalid enum values (e.g., role must be 'user', 'ai', or 'system')

---

## Configuration

### Environment Variables

The application uses `.env` file for configuration (loaded via `pydantic-settings`).

**Required**:
- `DATABASE_URL`: PostgreSQL connection string

**Optional**:
- `DEFAULT_PAGE_SIZE`: Default pagination size (default: 20)
- `MAX_PAGE_SIZE`: Maximum pagination size (default: 100)

### Configuration Loading

1. **Priority Order**:
   - Environment variables (highest priority)
   - `.env` file
   - Default values in `config.py` (lowest priority)

2. **Connection String Format**:
   ```
   postgresql+psycopg://username:password@host:port/database_name?sslmode=require
   ```

### Example `.env` File

```env
DATABASE_URL=postgresql+psycopg://admin:admin@localhost:5432/chat_history
DEFAULT_PAGE_SIZE=20
MAX_PAGE_SIZE=100
```

---

## Design Decisions

### 1. Why Layered Architecture?

**Decision**: Separate API, Service, and Database layers

**Rationale**:
- **Separation of Concerns**: Each layer has a single responsibility
- **Testability**: Easy to unit test each layer independently
- **Maintainability**: Changes in one layer don't affect others
- **Scalability**: Can optimize each layer independently

### 2. Why Static Service Methods?

**Decision**: Services use static methods instead of class instances

**Rationale**:
- **Stateless**: No instance state to manage
- **Simple**: No need for dependency injection of services
- **Thread-safe**: No shared state between requests
- **Fast**: No object instantiation overhead

### 3. Why Pydantic Schemas?

**Decision**: Use Pydantic for request/response validation

**Rationale**:
- **Type Safety**: Automatic type validation
- **Documentation**: Auto-generated API docs (OpenAPI/Swagger)
- **Performance**: Fast validation with compiled code
- **Error Messages**: Clear validation error messages

### 4. Why PostgreSQL ARRAY for Notebooks?

**Decision**: Use PostgreSQL ARRAY type for `notebooks` field

**Rationale**:
- **Native Support**: PostgreSQL handles arrays efficiently
- **Query Performance**: Can query array elements directly
- **Simplicity**: No need for join table for simple string arrays
- **Scalability**: Works well for moderate-sized arrays

### 5. Why Sort Messages by `created_at` not `updated_at`?

**Decision**: Messages sorted by `created_at` (as specified in requirements)

**Rationale**:
- **Chronological Order**: Shows conversation flow correctly
- **Consistency**: Messages appear in order they were created
- **User Expectation**: Users expect chronological message order

### 6. Why Optional Pagination?

**Decision**: Pagination is optional for all read endpoints

**Rationale**:
- **Flexibility**: Clients can choose pagination when needed
- **Small Datasets**: No pagination overhead for small result sets
- **Backward Compatibility**: Easy to add pagination later
- **Performance**: Clients can fetch all data if needed

### 7. Why Connection Pooling?

**Decision**: Use SQLAlchemy connection pooling

**Rationale**:
- **Performance**: Reuse connections instead of creating new ones
- **Scalability**: Handle concurrent requests efficiently
- **Resource Management**: Limit database connections
- **Reliability**: Pool pre-ping verifies connections

### 8. Why CASCADE Delete?

**Decision**: Delete messages when chat is deleted

**Rationale**:
- **Data Integrity**: Prevents orphaned messages
- **Simplicity**: No need to manually delete messages
- **Consistency**: Ensures clean data state
- **User Experience**: Deleting chat removes all related data

### 9. Why FastAPI?

**Decision**: Use FastAPI framework

**Rationale**:
- **Performance**: Fast, based on Starlette and Pydantic
- **Type Safety**: Full type hints support
- **Auto Documentation**: OpenAPI/Swagger docs automatically
- **Modern**: Async support, modern Python features
- **Validation**: Built-in request/response validation

### 10. Why SQLAlchemy 2.0?

**Decision**: Use SQLAlchemy 2.0 style

**Rationale**:
- **Modern API**: Improved API design
- **Type Safety**: Better type hints support
- **Performance**: Optimized query execution
- **Future-proof**: Latest version with ongoing support

---

## Extension Points

### Adding New Endpoints

1. **Create Schema** in `schemas.py`
2. **Add Service Method** in appropriate service file
3. **Create Router Endpoint** in appropriate router file
4. **Register Router** in `main.py` (if new router)

### Adding New Models

1. **Define Model** in `models.py`
2. **Create Schemas** in `schemas.py`
3. **Create Service** in `services/`
4. **Create Router** in `routers/`
5. **Run Migration** or update `init_database.py`

### Adding Business Logic

- Add to service layer methods
- Keep business logic separate from API layer
- Use service methods for reusable logic

---

## Performance Considerations

### Database Indexes

- `chats.id`: Primary key (automatically indexed)
- `messages.id`: Primary key (automatically indexed)
- `messages.chat_id`: Foreign key (automatically indexed)
- `messages.created_at`: Indexed for sorting performance

### Query Optimization

- **Pagination**: Limits result set size
- **Selective Fields**: Only fetch needed fields
- **Connection Pooling**: Reuse database connections
- **Lazy Loading**: SQLAlchemy lazy loading for relationships

### Scalability

- **Stateless Services**: Easy to scale horizontally
- **Connection Pooling**: Handles concurrent requests
- **Database Indexes**: Fast queries on large datasets
- **Pagination**: Prevents large result sets

---

## Security Considerations

### Input Validation

- All inputs validated with Pydantic schemas
- Type checking prevents injection attacks
- Enum validation for role field

### SQL Injection Prevention

- SQLAlchemy ORM prevents SQL injection
- Parameterized queries for all database operations
- No raw SQL queries

### Environment Variables

- Sensitive data (database credentials) in `.env` file
- `.env` file should be in `.gitignore`
- Use environment variables in production

---

## Testing Recommendations

### Unit Tests

- Test service layer methods
- Mock database sessions
- Test validation logic

### Integration Tests

- Test API endpoints
- Use test database
- Test database operations

### Test Structure

```
tests/
├── unit/
│   ├── test_services/
│   └── test_schemas/
├── integration/
│   ├── test_routers/
│   └── test_database/
└── conftest.py
```

---

## Deployment Considerations

### Production Checklist

- [ ] Set `DATABASE_URL` in environment variables
- [ ] Configure CORS origins appropriately
- [ ] Use production database (not localhost)
- [ ] Enable SSL/TLS for database connections
- [ ] Set appropriate connection pool sizes
- [ ] Configure logging
- [ ] Set up monitoring
- [ ] Use Alembic for database migrations
- [ ] Configure reverse proxy (nginx)
- [ ] Set up process manager (systemd, supervisor)

### Database Migrations

For production, use Alembic instead of `init_database.py`:

```bash
# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head
```

---

## Conclusion

This architecture provides a solid foundation for a scalable chat history API. The layered design ensures maintainability, the service layer encapsulates business logic, and the API layer provides a clean RESTful interface. The system is designed to be extended with new features while maintaining code quality and performance.

For questions or contributions, please refer to the main README.md file.


