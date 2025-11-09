#!/usr/bin/env python3
"""
Test script to verify .env file loading
"""
from config import settings

print("Current database URL:")
print(settings.database_url)
print("\nIf this shows the default value, your .env file is not being loaded.")
print("Make sure:")
print("1. .env file exists in the backend directory")
print("2. .env file contains: DATABASE_URL=postgresql+psycopg://...")
print("3. No spaces around the = sign in .env file")


