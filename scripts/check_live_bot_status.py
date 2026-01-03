#!/usr/bin/env python3
"""Check live bot status via API."""

import json

import requests


def check_status():
    """Check the live bot status."""
    base_url = "https://risex-trading-bot.fly.dev"
    
    print("=== RISE AI Trading Bot Status ===\n")
    
    # Check health
    try:
        resp = requests.get(f"{base_url}/health")
        print(f"Health Check: {resp.status_code}")
        print(json.dumps(resp.json(), indent=2))
    except Exception as e:
        print(f"Health check failed: {e}")
    
    print("\n--- Active Profiles ---")
    
    # Check profiles
    try:
        resp = requests.get(f"{base_url}/api/profiles/all")
        profiles = resp.json()
        
        for profile in profiles:
            print(f"\n{profile['name']} (@{profile['handle']})")
            print(f"  Active: {profile.get('is_active', False)}")
            print(f"  Equity: ${profile.get('current_equity', 0):,.2f}")
            print(f"  P&L: ${profile.get('pnl', 0):,.2f}")
            
            # Get detailed summary
            try:
                detail_resp = requests.get(f"{base_url}/api/profiles/{profile['id']}/summary")
                if detail_resp.status_code == 200:
                    detail = detail_resp.json()
                    
                    # Show positions
                    if detail.get("positions"):
                        print("  Positions:")
                        for pos in detail["positions"]:
                            print(f"    - {pos['market']}: {pos['size']} @ ${pos['avg_price']:,.2f}")
                    
                    # Show recent decisions
                    if detail.get("recent_decisions"):
                        print("  Recent Decisions:")
                        for dec in detail["recent_decisions"][:3]:
                            print(f"    - {dec['timestamp']}: {dec['decision']}")
            except:
                pass
                
    except Exception as e:
        print(f"Failed to get profiles: {e}")
    
    print("\n--- Bot Logs ---")
    # Show recent fly logs
    import subprocess
    try:
        result = subprocess.run(
            ["fly", "logs", "-a", "risex-trading-bot", "-n"],
            capture_output=True,
            text=True,
        )
        logs = result.stdout.split("\n")[-20:]  # Last 20 lines
        for line in logs:
            if any(keyword in line for keyword in ["ERROR", "WARNING", "place_market_order", "PlaceOrder reverted"]):
                print(line)
    except:
        print("Could not fetch logs")


if __name__ == "__main__":
    check_status()