#!/usr/bin/env python3
"""Debug admin API endpoints."""

import os

import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://risex-trading-bot.fly.dev"
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")

async def test_admin():
    async with httpx.AsyncClient() as client:
        print(f"Testing with API key: {ADMIN_API_KEY[:10]}...")
        
        response = await client.get(
            f"{BASE_URL}/api/admin/profiles",
            headers={"X-API-Key": ADMIN_API_KEY},
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_admin())