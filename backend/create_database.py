#!/usr/bin/env python3
"""
Script to create the database if it doesn't exist.
"""
from psycopg import connect
from config import settings
from urllib.parse import urlparse, parse_qs, unquote

# Extract connection details from settings
# SQLAlchemy format: postgresql+psycopg://user:password@host:port/dbname?params
# psycopg format: user=user password=password host=host port=port dbname=dbname

db_url = settings.database_url

try:
    # Remove the +psycopg part for parsing (or handle both postgres:// and postgresql+psycopg://)
    parse_url = db_url.replace("postgresql+psycopg://", "postgresql://").replace("postgres://", "postgresql://")
    
    # Parse the URL
    parsed = urlparse(parse_url)
    
    # Extract components
    user = unquote(parsed.username) if parsed.username else None
    password = unquote(parsed.password) if parsed.password else None
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432
    target_db = parsed.path.lstrip("/") if parsed.path else None
    
    # Handle query parameters (like sslmode)
    query_params = parse_qs(parsed.query)
    
    if not user or not target_db:
        raise ValueError("Missing user or database name in connection string")
    
    # Build connection string for psycopg (connect to 'postgres' to create target DB)
    conn_parts = [
        f"user={user}",
        f"host={host}",
        f"port={port}",
        "dbname=postgres"
    ]
    
    if password:
        conn_parts.insert(1, f"password={password}")
    
    # Add SSL mode if specified
    if "sslmode" in query_params:
        sslmode = query_params["sslmode"][0]
        conn_parts.append(f"sslmode={sslmode}")
    
    conn_string = " ".join(conn_parts)
    
    try:
        with connect(conn_string) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                # Check if database exists
                cur.execute(
                    "SELECT 1 FROM pg_database WHERE datname = %s",
                    (target_db,)
                )
                exists = cur.fetchone()
                
                if not exists:
                    cur.execute(f'CREATE DATABASE "{target_db}"')
                    print(f"✓ Database '{target_db}' created successfully!")
                else:
                    print(f"✓ Database '{target_db}' already exists.")
    except Exception as e:
        print(f"Error creating database: {e}")
        print(f"\nPlease create the database manually:")
        print(f"  psql -U {user} -h {host} -p {port} -c 'CREATE DATABASE {target_db};'")
        print(f"  OR")
        print(f"  createdb -U {user} -h {host} -p {port} {target_db}")
        
except Exception as e:
    print(f"Error parsing database URL: {e}")
    print(f"Received URL: {db_url}")
    print("\nExpected format: postgresql+psycopg://user:password@host:port/dbname?sslmode=require")
    print("\nNote: Special characters in password should be URL-encoded")
