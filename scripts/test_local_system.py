#!/usr/bin/env python3
"""Test the complete system locally with API and bot running."""

import asyncio
import subprocess
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def print_section(title):
    """Print a section header."""
    print(f"\n{'=' * 70}")
    print(f" {title}")
    print('=' * 70)


async def run_system_test():
    """Run complete system test."""
    print("RISE AI Trading Bot - Complete System Test")
    print_section("Starting Services")
    
    # Start the main application (API + Bot)
    print("\nStarting API server and trading bot...")
    print("This will run in the background. Press Ctrl+C to stop.\n")
    
    # Run start.py in subprocess with poetry
    process = subprocess.Popen(
        ["poetry", "run", "python", "start.py"],
        env={**subprocess.os.environ, "TRADING_MODE": "dry", "TRADING_INTERVAL": "30"}
    )
    
    # Give services time to start
    print("Waiting for services to start...")
    await asyncio.sleep(5)
    
    print_section("Testing API Endpoints")
    
    # Test API
    import httpx
    base_url = "http://localhost:8080"
    
    async with httpx.AsyncClient() as client:
        # Check health
        print("\n1. Checking system health...")
        try:
            response = await client.get(f"{base_url}/health")
            health = response.json()
            print(f"   Status: {health['status']}")
            print(f"   Accounts: {health.get('accounts', 0)}")
        except Exception as e:
            print(f"   Error: {e}")
            print("   Make sure no other services are running on port 8080")
            process.terminate()
            return
        
        # List profiles
        print("\n2. Listing trading profiles...")
        response = await client.get(f"{base_url}/api/profiles")
        profiles = response.json()
        print(f"   Found {len(profiles)} profiles:")
        
        for profile in profiles:
            print(f"   - {profile['handle']}: {profile['name']} ({profile['trading_style']})")
            print(f"     Trading: {profile['is_trading']}, P&L: ${profile['total_pnl']:.2f}")
        
        # Get detailed profile
        if profiles:
            handle = profiles[0]['handle']
            print(f"\n3. Getting details for {handle}...")
            response = await client.get(f"{base_url}/api/profiles/{handle}")
            details = response.json()
            
            print(f"   Name: {details['name']}")
            print(f"   Bio: {details['bio']}")
            print(f"   Risk Tolerance: {details['risk_tolerance']:.0%}")
            print(f"   Account: {details['account_address']}")
            print(f"   Pending Actions: {len(details['pending_actions'])}")
            
            # Start trading for one profile
            print(f"\n4. Starting trading for {handle}...")
            response = await client.post(f"{base_url}/api/profiles/{handle}/start")
            result = response.json()
            print(f"   Result: {result['message']}")
    
    print_section("System Running")
    print("\nThe system is now running with:")
    print("- FastAPI server at http://localhost:8080")
    print("- API docs at http://localhost:8080/docs")
    print("- Trading bot running in background")
    print("\nMonitor the output above to see trading activity.")
    print("Press Ctrl+C to stop all services.\n")
    
    try:
        # Keep running
        process.wait()
    except KeyboardInterrupt:
        print("\n\nShutting down services...")
        process.terminate()
        print("Services stopped.")


async def quick_test():
    """Quick test without running the full system."""
    print_section("Quick API Test")
    
    import httpx
    base_url = "http://localhost:8080"
    
    print("Testing API endpoints (assuming system is already running)...")
    
    async with httpx.AsyncClient() as client:
        try:
            # Test endpoints
            endpoints = [
                ("GET", "/"),
                ("GET", "/health"),
                ("GET", "/api/profiles"),
            ]
            
            for method, path in endpoints:
                print(f"\n{method} {path}")
                response = await client.request(method, f"{base_url}{path}")
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"   Results: {len(data)} items")
                    else:
                        print(f"   Response: {list(data.keys())}")
                        
        except Exception as e:
            print(f"\nError: {e}")
            print("Make sure the system is running: python start.py")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test RISE AI Trading Bot system")
    parser.add_argument(
        "--quick", 
        action="store_true",
        help="Run quick API test (assumes system is already running)"
    )
    
    args = parser.parse_args()
    
    if args.quick:
        asyncio.run(quick_test())
    else:
        # First ensure we have test accounts
        print("Checking for test accounts...")
        from app.services.storage import JSONStorage
        storage = JSONStorage()
        accounts = storage.list_accounts()
        
        if len(accounts) == 0:
            print("No accounts found. Run this first:")
            print("  python scripts/setup_test_accounts.py")
            return
        
        print(f"Found {len(accounts)} accounts. Starting system test...")
        asyncio.run(run_system_test())


if __name__ == "__main__":
    main()