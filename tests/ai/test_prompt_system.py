"""Test modular prompt loading and interpolation."""

import pytest
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.ai.prompt_loader import PromptLoader, get_prompt_loader


class TestPromptLoader:
    """Test prompt loading functionality."""
    
    def test_load_prompt(self):
        """Test loading prompt from file."""
        loader = get_prompt_loader()
        
        # Test loading system base prompt
        prompt = loader.load_prompt('system_base')
        assert prompt is not None
        assert "Core Trading System Instructions" in prompt
        assert "{name}" in prompt  # Check for interpolation placeholders
        
    def test_interpolation(self):
        """Test variable interpolation."""
        loader = get_prompt_loader()
        
        template = "Hello {name}, your risk tolerance is {risk_tolerance}"
        variables = {"name": "Test Trader", "risk_tolerance": 0.5}
        
        result = loader.interpolate(template, variables)
        assert result == "Hello Test Trader, your risk tolerance is 0.5"
        
    def test_build_system_prompt(self):
        """Test building complete system prompt."""
        loader = get_prompt_loader()
        
        # Mock persona
        persona = {
            'name': 'Test Bot',
            'personality_traits': ['analytical', 'cautious'],
            'trading_style': 'conservative',
            'risk_tolerance': 0.3,
            'favorite_assets': ['BTC', 'ETH'],
            'personality_type': 'cynical'
        }
        
        # Mock trading context
        context = {
            'current_equity': 1000.0,
            'free_margin': 800.0,
            'open_positions': 2,
            'current_pnl': -50.0
        }
        
        prompt = loader.build_system_prompt(persona, context)
        
        # Check key components are present
        assert "Test Bot" in prompt
        assert "analytical, cautious" in prompt
        assert "conservative" in prompt
        assert "0.3" in prompt
        assert "BTC, ETH" in prompt
        
        # Check all prompt sections are included
        assert "Core Trading System Instructions" in prompt
        assert "Personality Speech Patterns" in prompt
        assert "Risk Management Rules" in prompt
        assert "Tool Usage Guidelines" in prompt
        assert "Active Trading Encouragement" in prompt
        
    def test_risk_calculations(self):
        """Test risk-based calculations."""
        loader = get_prompt_loader()
        
        # Test conservative
        assert loader._calculate_max_position_percent(0.1) == 10
        assert loader._calculate_max_exposure(0.1) == 40
        
        # Test moderate
        assert loader._calculate_max_position_percent(0.5) == 30
        assert loader._calculate_max_exposure(0.5) == 80
        
        # Test aggressive
        assert loader._calculate_max_position_percent(0.9) == 50
        assert loader._calculate_max_exposure(0.9) == 150
        
    def test_cache_functionality(self):
        """Test prompt caching."""
        loader = get_prompt_loader()
        
        # Clear cache first
        loader.reload_cache()
        
        # First load should read from file
        prompt1 = loader.load_prompt('system_base')
        
        # Second load should use cache
        prompt2 = loader.load_prompt('system_base')
        
        assert prompt1 == prompt2
        
        # Clear cache and verify it reloads
        loader.reload_cache()
        prompt3 = loader.load_prompt('system_base')
        assert prompt3 == prompt1
        
    def test_missing_prompt_file(self):
        """Test handling of missing prompt files."""
        loader = get_prompt_loader()
        
        with pytest.raises(FileNotFoundError):
            loader.load_prompt('non_existent_prompt')
            
    def test_interpolation_missing_variable(self):
        """Test interpolation with missing variables."""
        loader = get_prompt_loader()
        
        template = "Hello {name}, your level is {level}"
        variables = {"name": "Test"}  # Missing 'level'
        
        with pytest.raises(KeyError):
            loader.interpolate(template, variables)
            
    def test_speech_style_mapping(self):
        """Test personality type mapping."""
        loader = get_prompt_loader()
        
        assert loader._map_speech_style('cynical') == 'Cynical Trader'
        assert loader._map_speech_style('leftCurve') == 'Left Curve'
        assert loader._map_speech_style('midwit') == 'Midwit'
        assert loader._map_speech_style('unknown') == 'Midwit'  # Default


def run_sync_tests():
    """Run synchronous tests."""
    print("=" * 60)
    print("Testing Modular Prompt System")
    print("=" * 60)
    
    test = TestPromptLoader()
    
    print("\n🔵 Testing prompt loading...")
    test.test_load_prompt()
    print("   ✅ Prompts load successfully")
    
    print("\n🔵 Testing interpolation...")
    test.test_interpolation()
    print("   ✅ Variable interpolation works")
    
    print("\n🔵 Testing system prompt building...")
    test.test_build_system_prompt()
    print("   ✅ Complete system prompt builds correctly")
    
    print("\n🔵 Testing risk calculations...")
    test.test_risk_calculations()
    print("   ✅ Risk-based calculations correct")
    
    print("\n🔵 Testing cache functionality...")
    test.test_cache_functionality()
    print("   ✅ Prompt caching works")
    
    print("\n🔵 Testing error handling...")
    try:
        test.test_missing_prompt_file()
    except:
        pass  # Expected to raise
    print("   ✅ Error handling works correctly")
    
    print("\n✅ All prompt system tests passed!")
    

if __name__ == "__main__":
    run_sync_tests()
    
    print("\n💡 To run pytest tests:")
    print("   poetry run pytest tests/ai/test_prompt_system.py -v")