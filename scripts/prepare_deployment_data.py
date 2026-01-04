#!/usr/bin/env python3
"""Prepare clean data for deployment with only 4 selected personas."""

import json
import shutil
from pathlib import Path

def prepare_deployment_data():
    """Prepare accounts.json with only the 4 personas we want to deploy."""
    
    # Backup current data
    accounts_path = Path("data/accounts.json")
    backup_path = Path("data/accounts_backup.json")
    
    if accounts_path.exists():
        shutil.copy(accounts_path, backup_path)
        print(f"✅ Backed up accounts to {backup_path}")
    
    # Define the personas we want to keep
    target_personas = {
        "leftcurve_redacted": "Drunk Wassie",  # Left curve persona
        "midcurve_midwit": "Midwit McGee",     # Mid curve persona
        "rightcurve_bigbrain": "Wise Chad",     # Right curve persona (assumption)
        "schizo_posters": "SCHIZO_POSTERS"      # Schizo persona
    }
    
    # Load current accounts
    with open(accounts_path, 'r') as f:
        accounts = json.load(f)
    
    # Filter accounts to keep only our target personas
    filtered_accounts = {}
    persona_count = 0
    
    for account_id, account in accounts.items():
        if 'persona' in account and account['persona']:
            persona_name = account['persona'].get('name', '')
            
            # Check if this is one of our target personas
            if persona_name in target_personas.values():
                filtered_accounts[account_id] = account
                persona_count += 1
                print(f"✅ Keeping: {persona_name} (ID: {account_id})")
    
    # Verify we have exactly 4 personas
    if persona_count != 4:
        print(f"⚠️  Warning: Expected 4 personas, found {persona_count}")
        print(f"   Found personas: {[acc['persona']['name'] for acc in filtered_accounts.values()]}")
        
        # If we're missing SCHIZO_POSTERS, we need to ensure it's in the data
        found_names = [acc['persona']['name'] for acc in filtered_accounts.values()]
        if "SCHIZO_POSTERS" not in found_names:
            print("❌ SCHIZO_POSTERS not found in accounts.json!")
            print("   You may need to run create_new_personas.py first")
    
    # Save filtered accounts
    deployment_path = Path("data/accounts_deployment.json")
    with open(deployment_path, 'w') as f:
        json.dump(filtered_accounts, f, indent=2)
    
    print(f"\n✅ Created deployment data at {deployment_path}")
    print(f"   Total personas: {persona_count}")
    
    # Create deployment script that will run on Fly.io
    deploy_script = """#!/bin/bash
# This script runs on Fly.io to set up the correct data

echo "Setting up deployment data..."

# Use deployment accounts if it exists
if [ -f /data/accounts_deployment.json ]; then
    cp /data/accounts_deployment.json /data/accounts.json
    echo "✅ Deployed with filtered personas"
else
    echo "⚠️  No deployment data found, using existing accounts"
fi

# Ensure all required data files exist
for file in markets.json trading_decisions.json thought_processes.json chat_sessions.json equity_snapshots.json pending_actions.json positions.json profile_updates.json trading_data.json chat_influence_results.json; do
    if [ ! -f /data/$file ]; then
        echo "{}" > /data/$file
        echo "✅ Created empty $file"
    fi
done

echo "✅ Data setup complete"
"""
    
    setup_script_path = Path("scripts/setup_deployment_data.sh")
    with open(setup_script_path, 'w') as f:
        f.write(deploy_script)
    setup_script_path.chmod(0o755)
    
    print(f"✅ Created setup script at {setup_script_path}")
    
    # Summary
    print("\n📊 Deployment Summary:")
    print("=" * 50)
    for persona_type, expected_name in target_personas.items():
        found = any(acc['persona']['name'] == expected_name for acc in filtered_accounts.values())
        status = "✅" if found else "❌"
        print(f"{status} {persona_type}: {expected_name}")
    
    print("\n🚀 Next Steps:")
    print("1. Review data/accounts_deployment.json")
    print("2. Copy accounts_deployment.json to the Docker image during build")
    print("3. Run ./deploy.sh to deploy to Fly.io")
    
    return filtered_accounts

if __name__ == "__main__":
    print("Preparing deployment data...")
    print("=" * 50)
    
    filtered = prepare_deployment_data()
    
    print("\n✅ Preparation complete!")
    print(f"   Personas ready for deployment: {len(filtered)}")