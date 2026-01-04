#!/usr/bin/env python3
"""Create new trading profiles via Admin API."""

import os
import sys
import json
import argparse
import requests
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def create_profile_via_api(
    profile_data: dict, 
    api_url: str, 
    api_key: str
) -> dict:
    """Create a new profile via Admin API."""
    endpoint = f"{api_url}/api/admin/profiles"
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    print(f"📡 Creating profile via API...")
    print(f"   Name: {profile_data['name']}")
    print(f"   Handle: {profile_data['handle']}")
    print(f"   Personality: {profile_data['personality_type']}")
    print(f"   Initial deposit: ${profile_data['initial_deposit']}")
    
    try:
        response = requests.post(endpoint, json=profile_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Profile created successfully!")
            print(f"   Profile ID: {result['profile_id']}")
            print(f"   Address: {result['address']}")
            print(f"   Message: {result['message']}")
            return result
        else:
            print(f"\n❌ Failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None


def load_template_persona(template_name: str) -> dict:
    """Load a persona template from data/personas/templates/."""
    template_path = Path(f"data/personas/templates/{template_name}")
    if not template_path.exists():
        print(f"❌ Template not found: {template_path}")
        return None
    
    with open(template_path, 'r') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Create new trading profile via API")
    
    # Basic required fields
    parser.add_argument("name", help="Profile name")
    parser.add_argument("handle", help="Profile handle (unique)")
    parser.add_argument("personality_type", 
                       choices=["leftCurve", "midCurve", "rightCurve", "cynical", "schizo"],
                       help="Personality type")
    
    # Optional fields
    parser.add_argument("--bio", default="AI trader on RISE", help="Profile bio")
    parser.add_argument("--deposit", type=float, default=100.0, 
                       help="Initial USDC deposit amount")
    parser.add_argument("--risk", type=float, default=0.5, 
                       help="Risk tolerance (0.0-1.0)")
    parser.add_argument("--style", default="momentum", 
                       choices=["aggressive", "conservative", "contrarian", "momentum", "degen"],
                       help="Trading style")
    parser.add_argument("--assets", nargs="+", default=["BTC", "ETH"], 
                       help="Favorite assets")
    parser.add_argument("--from-template", 
                       help="Load from template file (e.g., schizo_posters.json)")
    
    # API configuration
    parser.add_argument("--api-url", default="https://risex-trading-bot.fly.dev", 
                       help="API URL")
    parser.add_argument("--local", action="store_true", 
                       help="Use local API (http://localhost:8080)")
    
    args = parser.parse_args()
    
    # Get API key
    api_key = os.environ.get("ADMIN_API_KEY")
    if not api_key:
        print("❌ ADMIN_API_KEY not set in environment")
        return
    
    # Build profile data
    profile_data = {
        "name": args.name,
        "handle": args.handle,
        "personality_type": args.personality_type,
        "bio": args.bio,
        "initial_deposit": args.deposit,
        "risk_tolerance": args.risk,
        "trading_style": args.style,
        "favorite_assets": args.assets,
        "personality_traits": []
    }
    
    # Load from template if specified
    if args.from_template:
        template = load_template_persona(args.from_template)
        if template:
            # Override with template data
            if "base_info" in template:
                profile_data["bio"] = template["base_info"].get("bio", args.bio)
            if "trading_behavior" in template:
                profile_data["risk_tolerance"] = template["trading_behavior"].get("risk_tolerance", args.risk)
                profile_data["favorite_assets"] = template["trading_behavior"].get("preferred_markets", args.assets)[:3]
            if "core_traits" in template and "strengths" in template["core_traits"]:
                profile_data["personality_traits"] = template["core_traits"]["strengths"][:3]
    
    # Determine API URL
    api_url = "http://localhost:8080" if args.local else args.api_url
    
    # Create profile
    result = create_profile_via_api(profile_data, api_url, api_key)
    
    if result:
        print("\n🎉 Profile created and ready for trading!")
        print(f"   To check status: curl -H 'X-API-Key: {api_key}' {api_url}/api/admin/profiles/{result['profile_id']}")
    else:
        print("\n❌ Profile creation failed")


if __name__ == "__main__":
    main()