#!/usr/bin/env python3
"""
Initialize the database
"""
import asyncio
from database import init_db

async def main():
    """Initialize database tables"""
    print("Initializing database...")
    await init_db()
    print("Database initialized successfully!")

if __name__ == "__main__":
    asyncio.run(main())
