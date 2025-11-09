#!/usr/bin/env python3
"""
Database initialization script.
Run this once to create all tables in the database.

IMPORTANT: This script only creates tables if they don't exist.
It does NOT modify existing tables or add new columns to existing tables.
For schema changes, use Alembic migrations or manual SQL ALTER statements.

Usage:
    python init_database.py
"""
from database import init_db
from models import Chat, Message


if __name__ == "__main__":
    print("Initializing database...")
    print("Creating tables: chats, messages")
    print("Note: This will only create tables if they don't exist.")
    print("      Existing tables will NOT be modified.\n")
    init_db()
    print("✓ Database initialized successfully!")
    print("\nYou can now start the API server with:")
    print("  uvicorn main:app --reload")

