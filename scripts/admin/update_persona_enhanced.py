#!/usr/bin/env python3
"""Enhanced admin script to update persona data via API or locally."""

import os
import sys
import json
import argparse
import asyncio
import requests
from pathlib import Path
from typing import Optional, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.storage import JSONStorage


def load_persona_json(persona_file: str) -> dict[str, Any]:
    """Load persona data from JSON file."""
    # Check new location first
    filepath = Path(f"data/personas/templates/{persona_file}")
    if not filepath.exists():
        # Try old location as fallback
        filepath = Path(f"app/ai/personas/{persona_file}")
    
    if not filepath.exists():
        print(f"❌ Persona file not found: {filepath}")
        return {}
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Extract relevant fields for API update
    persona_updates = {
        # Basic fields
        "bio": data.get("base_info", {}).get("bio", ""),
        "trading_style": "contrarian",  # Map from trading behavior
        "risk_tolerance": data.get("trading_behavior", {}).get("risk_tolerance", 0.5),
        "favorite_assets": data.get("trading_behavior", {}).get("preferred_markets", ["BTC", "ETH"])[:3],
        
        # Enhanced fields
        "personality_type": data.get("base_info", {}).get("personality_type", ""),
        "extended_bio": data.get("core_traits", {}).get("worldview", ""),
        "speech_patterns": data.get("speech_patterns", {}),
        "core_beliefs": data.get("core_traits", {}),
        "market_biases": [
            data.get("trading_behavior", {}).get("market_biases", "")
        ] if data.get("trading_behavior", {}).get("market_biases") else [],
        "interaction_style": data.get("chat_behavior", {}),
    }
    
    # Extract sample posts from example interactions
    if "example_interactions" in data:
        persona_updates["sample_posts"] = [
            interaction["response"]
            for interaction in data["example_interactions"][:3]
        ]
    
    # Extract personality traits
    if "core_traits" in data and "strengths" in data["core_traits"]:
        persona_updates["personality_traits"] = data["core_traits"]["strengths"][:3]
    
    return persona_updates


def update_persona_via_api(
    profile_id: str, 
    updates: dict, 
    api_url: str, 
    api_key: str
) -> bool:
    """Update persona via Admin API."""
    endpoint = f"{api_url}/api/admin/profiles/{profile_id}/persona"
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    print(f"📡 Updating persona via API...")
    print(f"   Endpoint: {endpoint}")
    print(f"   Fields to update: {list(updates.keys())}")
    
    try:
        response = requests.patch(endpoint, json=updates, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Persona updated successfully!")
            print(f"   Updated fields: {result.get('updated_fields', [])}")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def update_persona_locally(profile_id: str, updates: dict) -> bool:
    """Update persona data locally."""
    storage = JSONStorage()
    
    # Get account
    account = storage.get_account(profile_id)
    if not account:
        print(f"❌ Profile {profile_id} not found")
        return False
    
    if not account.persona:
        print(f"❌ Profile has no persona")
        return False
    
    print(f"📝 Updating {account.persona.name} locally...")
    print(f"   Current personality_type: {getattr(account.persona, 'personality_type', 'None')}")
    
    # Update persona fields
    updated_fields = []
    for key, value in updates.items():
        if hasattr(account.persona, key):
            setattr(account.persona, key, value)
            updated_fields.append(key)
    
    # Save
    storage.save_account(account)
    
    print(f"✅ Updated {len(updated_fields)} fields locally")
    print(f"   Fields: {updated_fields}")
    
    # Show some of the updated data
    if 'personality_type' in updates:
        print(f"   New personality_type: {account.persona.personality_type}")
    if 'extended_bio' in updates:
        print(f"   Extended bio: {account.persona.extended_bio[:100]}...")
    
    return True


async def main():
    parser = argparse.ArgumentParser(description="Update persona with enhanced data")
    parser.add_argument("profile_id", help="Profile ID to update")
    parser.add_argument("--from-json", help="Load from persona JSON file (e.g., schizo_posters.json)")
    parser.add_argument("--personality-type", help="Set personality type")
    parser.add_argument("--bio", help="Update bio")
    parser.add_argument("--extended-bio", help="Set extended bio")
    parser.add_argument("--risk", type=float, help="Update risk tolerance (0.0-1.0)")
    parser.add_argument("--api", action="store_true", help="Update via API instead of locally")
    parser.add_argument("--api-url", default="https://risex-trading-bot.fly.dev", help="API URL")
    parser.add_argument("--local-api", action="store_true", help="Use local API (http://localhost:8080)")
    parser.add_argument("--deploy", action="store_true", help="Deploy to Fly after local update")
    
    args = parser.parse_args()
    
    # Build updates
    updates = {}
    
    if args.from_json:
        # Load from persona JSON
        print(f"📂 Loading from {args.from_json}...")
        updates = load_persona_json(args.from_json)
        if not updates:
            return
    else:
        # Manual updates
        if args.personality_type:
            updates["personality_type"] = args.personality_type
        if args.bio:
            updates["bio"] = args.bio
        if args.extended_bio:
            updates["extended_bio"] = args.extended_bio
        if args.risk is not None:
            updates["risk_tolerance"] = args.risk
    
    if not updates:
        print("❌ No updates specified")
        return
    
    print(f"📊 Updates to apply: {len(updates)} fields")
    
    # Update via API or locally
    if args.api or args.local_api:
        # Get API key
        api_key = os.environ.get("ADMIN_API_KEY")
        if not api_key:
            print("❌ ADMIN_API_KEY not set in environment")
            return
        
        # Determine API URL
        api_url = "http://localhost:8080" if args.local_api else args.api_url
        
        # Update via API
        success = update_persona_via_api(args.profile_id, updates, api_url, api_key)
    else:
        # Update locally
        success = await update_persona_locally(args.profile_id, updates)
        
        if success and args.deploy:
            print("\n🚀 Ready to deploy. Run: ./deploy.sh")
    
    if success:
        print("\n✅ Persona update complete!")
    else:
        print("\n❌ Persona update failed")


if __name__ == "__main__":
    asyncio.run(main())