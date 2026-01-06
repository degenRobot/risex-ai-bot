#!/usr/bin/env python3
"""Create a clean deployment file with only the 4 target personas."""

import json
from pathlib import Path

def create_clean_deployment():
    """Create deployment file with only the 4 target personas."""
    
    # Load current accounts
    with open("data/accounts.json", 'r') as f:
        all_accounts = json.load(f)
    
    # Define our target personas
    target_personas = {
        "Drunk Wassie": "vXgJJCcakMbmvmq_CPXTnA",
        "Midwit McGee": "VeRw6CY7dOF9SEpFmfU1bA", 
        "Wise Chad": "iPOWY7Dtc60irRICBUF9nw",
        "SCHIZO_POSTERS": "6d77bcf3-7d3a-48aa-bed3-79b58870c8a8"
    }
    
    # Filter to only our 4 personas
    clean_accounts = {}
    for persona_name, account_id in target_personas.items():
        if account_id in all_accounts:
            account = all_accounts[account_id]
            if account.get('persona', {}).get('name') == persona_name:
                clean_accounts[account_id] = account
                print(f"✅ Including: {persona_name} (ID: {account_id})")
            else:
                print(f"⚠️  Account ID mismatch for {persona_name}")
        else:
            print(f"❌ Missing: {persona_name} (ID: {account_id})")
    
    # Save clean deployment file
    with open("data/accounts_deployment_clean.json", 'w') as f:
        json.dump(clean_accounts, f, indent=2)
    
    print(f"\n📦 Created clean deployment with {len(clean_accounts)} personas")
    print("\nTo deploy:")
    print("1. cp data/accounts_deployment_clean.json data/accounts_deployment.json")
    print("2. ./deploy.sh --reset-personas")

if __name__ == "__main__":
    create_clean_deployment()