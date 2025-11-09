# Migration Guide: Adding `name` Field to Chat Model

## Overview

The `name` field has been added to the Chat model to allow storing a chat name/title.

## Changes Made

1. **Database Model** (`models.py`):
   - Added `name = Column(String(255), nullable=True)` to Chat model

2. **Schemas** (`schemas.py`):
   - Added `name` field to `ChatBase`, `ChatCreate`, `ChatUpdate`, and `ChatResponse`
   - Field is optional (nullable) with max length of 255 characters

3. **Service Layer** (`services/chat_service.py`):
   - Updated `create_chat()` to handle `name` field
   - Updated `get_chat_detail()` to include `name` in response

4. **Routers**: No changes needed - automatically work with updated schemas

## Database Migration

### For New Databases

If you're creating a new database, simply run:

```bash
python init_database.py
```

The `name` column will be created automatically.

### For Existing Databases

If you have an existing database, you need to add the `name` column manually:

#### Option 1: Using SQL

```sql
ALTER TABLE chats ADD COLUMN name VARCHAR(255);
```

#### Option 2: Using psql

```bash
psql -U your_user -d your_database -c "ALTER TABLE chats ADD COLUMN name VARCHAR(255);"
```

#### Option 3: Using Alembic (Recommended for Production)

If you're using Alembic for migrations:

```bash
# Create a new migration
alembic revision --autogenerate -m "add_name_to_chat"

# Review the migration file, then apply it
alembic upgrade head
```

## API Usage

### Creating a Chat with Name

```bash
POST /api/chats/
{
  "name": "My Chat Session",
  "notebooks": ["notebook1", "notebook2"]
}
```

### Creating a Chat without Name (Optional)

```bash
POST /api/chats/
{
  "notebooks": ["notebook1"]
}
```

### Updating Chat Name

```bash
PUT /api/chats/1
{
  "name": "Updated Chat Name"
}
```

### Response Format

All chat responses now include the `name` field:

```json
{
  "id": 1,
  "name": "My Chat Session",
  "notebooks": ["notebook1"],
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

## Backward Compatibility

- The `name` field is **optional** (nullable), so existing code will continue to work
- Existing chats will have `name: null` until updated
- All endpoints support the `name` field in requests and responses


