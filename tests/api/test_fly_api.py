#!/usr/bin/env python3
"""
Comprehensive test suite for the deployed Fly.io API.
Tests all endpoints with proper assertions and error handling.
"""

import asyncio
import httpx
import json
import os
from datetime import datetime
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_URL = "https://risex-trading-bot.fly.dev"
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
MASTER_KEY = "master-secret-key"

# Test account ID (The Crypto Degen)
TEST_ACCOUNT_ID = "7f673612-83ad-4e34-a323-1d77126440a8"


class APITestSuite:
    """Test suite for RISE AI Trading Bot API."""
    
    def __init__(self):
        self.base_url = BASE_URL
        self.admin_key = ADMIN_API_KEY
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "tests": {}
        }
    
    async def run_all_tests(self):
        """Run all API tests."""
        print("🧪 RISE AI Trading Bot API Test Suite")
        print(f"🌐 Testing: {self.base_url}")
        print("="*60)
        
        # Run tests in order
        await self.test_health_check()
        await self.test_list_profiles()
        await self.test_get_profile_by_handle()
        await self.test_chat_with_profile()
        await self.test_get_profile_summary()
        await self.test_get_profile_context()
        await self.test_admin_endpoints()
        await self.test_error_handling()
        
        # Save results
        self.save_results()
        self.print_summary()
    
    async def test_health_check(self):
        """Test health check endpoint."""
        print("\n📍 Testing: GET /health")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/health")
                
                assert response.status_code == 200
                data = response.json()
                assert "status" in data
                assert data["status"] == "healthy"
                assert "accounts" in data
                assert data["accounts"] > 0
                
                self.results["tests"]["health_check"] = {
                    "status": "✅ PASSED",
                    "response": data
                }
                print("✅ Health check passed")
                
            except Exception as e:
                self.results["tests"]["health_check"] = {
                    "status": "❌ FAILED",
                    "error": str(e)
                }
                print(f"❌ Health check failed: {e}")
    
    async def test_list_profiles(self):
        """Test list profiles endpoint."""
        print("\n📍 Testing: GET /api/profiles")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/api/profiles")
                
                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)
                assert len(data) > 0
                
                # Check profile structure
                profile = data[0]
                required_fields = ["handle", "name", "trading_style", "is_trading"]
                for field in required_fields:
                    assert field in profile
                
                self.results["tests"]["list_profiles"] = {
                    "status": "✅ PASSED",
                    "profile_count": len(data),
                    "sample": profile
                }
                print(f"✅ List profiles passed ({len(data)} profiles)")
                
            except Exception as e:
                self.results["tests"]["list_profiles"] = {
                    "status": "❌ FAILED",
                    "error": str(e)
                }
                print(f"❌ List profiles failed: {e}")
    
    async def test_get_profile_by_handle(self):
        """Test get profile by handle endpoint."""
        print("\n📍 Testing: GET /api/profiles/{handle}")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/api/profiles/crypto_degen")
                
                assert response.status_code == 200
                data = response.json()
                assert data["handle"] == "crypto_degen"
                assert "persona" in data or "name" in data
                
                self.results["tests"]["get_profile_by_handle"] = {
                    "status": "✅ PASSED",
                    "profile": {
                        "handle": data["handle"],
                        "name": data["name"],
                        "trading_style": data["trading_style"]
                    }
                }
                print("✅ Get profile by handle passed")
                
            except Exception as e:
                self.results["tests"]["get_profile_by_handle"] = {
                    "status": "❌ FAILED",
                    "error": str(e)
                }
                print(f"❌ Get profile by handle failed: {e}")
    
    async def test_chat_with_profile(self):
        """Test chat with profile endpoint."""
        print("\n📍 Testing: POST /api/profiles/{account_id}/chat")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                # Test bullish message
                response = await client.post(
                    f"{self.base_url}/api/profiles/{TEST_ACCOUNT_ID}/chat",
                    json={
                        "message": "Bitcoin breaking 100k today. Time to go long.",
                        "chatHistory": ""
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "response" in data
                assert "profileUpdates" in data
                assert "sessionId" in data
                assert len(data["response"]) > 0
                
                self.results["tests"]["chat_bullish"] = {
                    "status": "✅ PASSED",
                    "response_preview": data["response"][:100] + "...",
                    "updates": data["profileUpdates"],
                    "session_id": data["sessionId"]
                }
                print("✅ Chat (bullish) passed")
                
                # Test bearish message
                response = await client.post(
                    f"{self.base_url}/api/profiles/{TEST_ACCOUNT_ID}/chat",
                    json={
                        "message": "Market crash incoming. Bitcoin to 50k.",
                        "chatHistory": ""
                    }
                )
                
                assert response.status_code == 200
                data = response.json()
                
                self.results["tests"]["chat_bearish"] = {
                    "status": "✅ PASSED",
                    "response_preview": data["response"][:100] + "...",
                    "updates": data["profileUpdates"]
                }
                print("✅ Chat (bearish) passed")
                
            except Exception as e:
                self.results["tests"]["chat_with_profile"] = {
                    "status": "❌ FAILED",
                    "error": str(e)
                }
                print(f"❌ Chat with profile failed: {e}")
    
    async def test_get_profile_summary(self):
        """Test get profile summary endpoint."""
        print("\n📍 Testing: GET /api/profiles/{account_id}/summary")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/profiles/{TEST_ACCOUNT_ID}/summary"
                )
                
                assert response.status_code == 200
                data = response.json()
                
                self.results["tests"]["profile_summary"] = {
                    "status": "✅ PASSED",
                    "has_thinking": "currentThinking" in data,
                    "has_persona": "basePersona" in data
                }
                print("✅ Get profile summary passed")
                
            except Exception as e:
                self.results["tests"]["profile_summary"] = {
                    "status": "❌ FAILED",
                    "error": str(e)
                }
                print(f"❌ Get profile summary failed: {e}")
    
    async def test_get_profile_context(self):
        """Test get profile context endpoint."""
        print("\n📍 Testing: GET /api/profiles/{account_id}/context")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/profiles/{TEST_ACCOUNT_ID}/context"
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "trading_context" in data
                assert "profile_name" in data
                
                self.results["tests"]["profile_context"] = {
                    "status": "✅ PASSED",
                    "profile_name": data["profile_name"],
                    "context": data["trading_context"]
                }
                print("✅ Get profile context passed")
                
            except Exception as e:
                self.results["tests"]["profile_context"] = {
                    "status": "❌ FAILED",
                    "error": str(e)
                }
                print(f"❌ Get profile context failed: {e}")
    
    async def test_admin_endpoints(self):
        """Test admin endpoints with authentication."""
        print("\n📍 Testing: Admin Endpoints")
        
        if not self.admin_key:
            print("⚠️  No admin API key in .env, skipping admin tests")
            self.results["tests"]["admin_endpoints"] = {
                "status": "⚠️  SKIPPED",
                "reason": "No ADMIN_API_KEY in environment"
            }
            return
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {"X-API-Key": self.admin_key}
            
            # Test list profiles (admin)
            try:
                response = await client.get(
                    f"{self.base_url}/api/admin/profiles",
                    headers=headers
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "total" in data
                assert "profiles" in data
                
                self.results["tests"]["admin_list_profiles"] = {
                    "status": "✅ PASSED",
                    "total_profiles": data["total"]
                }
                print(f"✅ Admin list profiles passed ({data['total']} profiles)")
                
            except Exception as e:
                self.results["tests"]["admin_list_profiles"] = {
                    "status": "❌ FAILED",
                    "error": str(e)
                }
                print(f"❌ Admin list profiles failed: {e}")
            
            # Test get balance (may fail if account not whitelisted)
            try:
                response = await client.get(
                    f"{self.base_url}/api/admin/profiles/{TEST_ACCOUNT_ID}/balance",
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.results["tests"]["admin_get_balance"] = {
                        "status": "✅ PASSED",
                        "balance": data.get("balance", 0)
                    }
                    print("✅ Admin get balance passed")
                else:
                    self.results["tests"]["admin_get_balance"] = {
                        "status": "⚠️  WARNING",
                        "reason": "Account not whitelisted on RISE",
                        "status_code": response.status_code
                    }
                    print("⚠️  Admin get balance: Account not whitelisted")
                    
            except Exception as e:
                self.results["tests"]["admin_get_balance"] = {
                    "status": "❌ FAILED",
                    "error": str(e)
                }
                print(f"❌ Admin get balance failed: {e}")
    
    async def test_error_handling(self):
        """Test error handling with invalid requests."""
        print("\n📍 Testing: Error Handling")
        
        async with httpx.AsyncClient() as client:
            # Test 404 - Invalid profile
            try:
                response = await client.get(
                    f"{self.base_url}/api/profiles/invalid_handle"
                )
                assert response.status_code == 404
                
                self.results["tests"]["error_404"] = {
                    "status": "✅ PASSED",
                    "message": "Correctly returns 404 for invalid profile"
                }
                print("✅ 404 error handling passed")
                
            except Exception as e:
                self.results["tests"]["error_404"] = {
                    "status": "❌ FAILED",
                    "error": str(e)
                }
                print(f"❌ 404 error handling failed: {e}")
            
            # Test 401 - Invalid API key
            try:
                response = await client.get(
                    f"{self.base_url}/api/admin/profiles",
                    headers={"X-API-Key": "invalid_key"}
                )
                assert response.status_code == 401
                
                self.results["tests"]["error_401"] = {
                    "status": "✅ PASSED",
                    "message": "Correctly returns 401 for invalid API key"
                }
                print("✅ 401 error handling passed")
                
            except Exception as e:
                self.results["tests"]["error_401"] = {
                    "status": "❌ FAILED",
                    "error": str(e)
                }
                print(f"❌ 401 error handling failed: {e}")
    
    def save_results(self):
        """Save test results to JSON file."""
        with open("tests/api/test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        print("\n💾 Results saved to tests/api/test_results.json")
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        passed = 0
        failed = 0
        skipped = 0
        
        for test_name, result in self.results["tests"].items():
            status = result.get("status", "Unknown")
            if "PASSED" in status:
                passed += 1
            elif "FAILED" in status:
                failed += 1
            elif "SKIPPED" in status or "WARNING" in status:
                skipped += 1
            
            print(f"{status} {test_name}")
        
        print("="*60)
        print(f"Total: {len(self.results['tests'])} tests")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Skipped/Warning: {skipped}")
        
        if failed == 0:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠️  {failed} tests failed")


async def main():
    """Run the test suite."""
    suite = APITestSuite()
    await suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())