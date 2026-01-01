#!/usr/bin/env python3
"""Convenience script to run the enhanced trading system test."""

import asyncio
import subprocess
import sys
from pathlib import Path

def run_test(test_name: str, description: str):
    """Run a test script and show results."""
    print(f"\n🧪 {description}")
    print("=" * 60)
    
    try:
        result = subprocess.run([
            "poetry", "run", "python", f"tests/{test_name}"
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"❌ Test failed with return code {result.returncode}")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            
    except subprocess.TimeoutExpired:
        print("⏰ Test timed out after 2 minutes")
    except Exception as e:
        print(f"❌ Error running test: {e}")

def main():
    """Run the enhanced system tests in sequence."""
    print("🚀 RISE AI Bot - Enhanced System Test Suite")
    print("=" * 60)
    print("This will test the enhanced trading system with decision logging,")
    print("historical analysis, and improved AI decision making.")
    
    # Test sequence
    tests = [
        ("test_enhanced_system.py", "Enhanced Decision Logging & Analytics"),
        ("test_automated_trading.py", "Complete Automated Trading System"),
    ]
    
    for test_file, description in tests:
        run_test(test_file, description)
        input("\nPress Enter to continue to next test...")
    
    print("\n🎉 All Enhanced System Tests Complete!")
    print("\n💡 Next steps:")
    print("1. Run the production bot: poetry run python scripts/run_trading_bot.py")
    print("2. Check data/trading_decisions.json for logged decisions")
    print("3. Watch the AI learn from trading history!")

if __name__ == "__main__":
    main()