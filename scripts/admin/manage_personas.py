#!/usr/bin/env python3
"""Manage persona data in the new structure."""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.storage import JSONStorage


class PersonaManager:
    """Manage persona data in the new directory structure."""
    
    def __init__(self):
        self.storage = JSONStorage()
        self.personas_dir = Path("data/personas")
        self.templates_dir = self.personas_dir / "templates"
        
    def create_profile_directory(self, account_id: str) -> Path:
        """Create directory structure for a profile."""
        profile_dir = self.personas_dir / account_id
        profile_dir.mkdir(parents=True, exist_ok=True)
        return profile_dir
    
    def export_persona(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Export persona data from account to file structure."""
        account = self.storage.get_account(account_id)
        if not account or not account.persona:
            print(f"❌ No persona found for account {account_id}")
            return None
        
        # Create profile directory
        profile_dir = self.create_profile_directory(account_id)
        
        # Export persona data
        persona_data = {
            "account_id": account_id,
            "base_info": {
                "name": account.persona.name,
                "handle": account.persona.handle,
                "bio": account.persona.bio,
                "personality_type": account.persona.personality_type,
                "trading_style": account.persona.trading_style,
            },
            "personality": {
                "traits": account.persona.personality_traits,
                "risk_tolerance": account.persona.risk_tolerance,
                "favorite_assets": account.persona.favorite_assets,
                "sample_posts": account.persona.sample_posts,
            }
        }
        
        # Add enhanced fields if present
        if account.persona.extended_bio:
            persona_data["base_info"]["extended_bio"] = account.persona.extended_bio
        if account.persona.speech_patterns:
            persona_data["speech_patterns"] = account.persona.speech_patterns
        if account.persona.core_beliefs:
            persona_data["core_beliefs"] = account.persona.core_beliefs
        if account.persona.market_biases:
            persona_data["personality"]["market_biases"] = account.persona.market_biases
        if account.persona.interaction_style:
            persona_data["interaction_style"] = account.persona.interaction_style
        
        # Save to file
        persona_file = profile_dir / "persona.json"
        with open(persona_file, 'w') as f:
            json.dump(persona_data, f, indent=2)
        
        print(f"✅ Exported persona to {persona_file}")
        return persona_data
    
    def import_from_template(
        self, 
        account_id: str, 
        template_name: str
    ) -> bool:
        """Import persona data from a template."""
        template_file = self.templates_dir / template_name
        if not template_file.exists():
            print(f"❌ Template not found: {template_file}")
            return False
        
        # Load template
        with open(template_file, 'r') as f:
            template_data = json.load(f)
        
        # Get account
        account = self.storage.get_account(account_id)
        if not account:
            print(f"❌ Account not found: {account_id}")
            return False
        
        # Update persona with template data
        if account.persona:
            # Update existing persona
            if "base_info" in template_data:
                account.persona.extended_bio = template_data.get("core_traits", {}).get("worldview", "")
                account.persona.personality_type = template_data["base_info"].get("personality_type", account.persona.personality_type)
            
            if "speech_patterns" in template_data:
                account.persona.speech_patterns = template_data["speech_patterns"]
            
            if "core_traits" in template_data:
                account.persona.core_beliefs = template_data["core_traits"]
                if "strengths" in template_data["core_traits"]:
                    account.persona.personality_traits = template_data["core_traits"]["strengths"][:3]
            
            if "trading_behavior" in template_data:
                account.persona.risk_tolerance = template_data["trading_behavior"].get("risk_tolerance", 0.5)
                account.persona.market_biases = [template_data["trading_behavior"].get("market_biases", "")]
            
            if "chat_behavior" in template_data:
                account.persona.interaction_style = template_data["chat_behavior"]
            
            # Save account
            self.storage.save_account(account)
            
            # Export to profile directory
            self.export_persona(account_id)
            
            print(f"✅ Imported template data for {account.persona.name}")
            return True
        else:
            print(f"❌ Account has no persona")
            return False
    
    def list_profiles(self) -> None:
        """List all profiles with persona directories."""
        accounts = self.storage.list_accounts()
        
        print("\n📋 Profile Directories:")
        print("=" * 60)
        
        for account in accounts:
            if account.persona:
                profile_dir = self.personas_dir / account.id
                status = "✅" if profile_dir.exists() else "❌"
                print(f"{status} {account.id:30} {account.persona.name:20} {account.persona.personality_type or 'Unknown'}")
        
        print("\n📁 Available Templates:")
        print("=" * 40)
        
        if self.templates_dir.exists():
            for template in self.templates_dir.glob("*.json"):
                print(f"   {template.name}")
    
    def sync_all_profiles(self) -> None:
        """Sync all profiles to the new directory structure."""
        accounts = self.storage.list_accounts()
        
        print(f"\n🔄 Syncing {len(accounts)} profiles...")
        
        success_count = 0
        for account in accounts:
            if account.persona:
                result = self.export_persona(account.id)
                if result:
                    success_count += 1
        
        print(f"\n✅ Synced {success_count} profiles to data/personas/")


def main():
    parser = argparse.ArgumentParser(description="Manage persona data")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export persona to file")
    export_parser.add_argument("account_id", help="Account ID to export")
    
    # Import command
    import_parser = subparsers.add_parser("import", help="Import from template")
    import_parser.add_argument("account_id", help="Account ID to update")
    import_parser.add_argument("template", help="Template file name")
    
    # List command
    subparsers.add_parser("list", help="List all profiles")
    
    # Sync command
    subparsers.add_parser("sync", help="Sync all profiles to new structure")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = PersonaManager()
    
    if args.command == "export":
        manager.export_persona(args.account_id)
    elif args.command == "import":
        manager.import_from_template(args.account_id, args.template)
    elif args.command == "list":
        manager.list_profiles()
    elif args.command == "sync":
        manager.sync_all_profiles()


if __name__ == "__main__":
    main()