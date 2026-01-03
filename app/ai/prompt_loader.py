"""Modular prompt loading and interpolation system."""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class PromptLoader:
    """Load and interpolate modular prompts from markdown files."""
    
    def __init__(self, prompts_dir: Optional[Path] = None):
        """Initialize the prompt loader.
        
        Args:
            prompts_dir: Directory containing prompt files. Defaults to app/ai/prompts.
        """
        if prompts_dir is None:
            prompts_dir = Path(__file__).parent / "prompts"
        self.prompts_dir = prompts_dir
        self._cache: Dict[str, str] = {}
        
    def load_prompt(self, name: str) -> str:
        """Load a prompt by name from markdown file.
        
        Args:
            name: Name of the prompt file (without .md extension)
            
        Returns:
            The prompt content as a string
            
        Raises:
            FileNotFoundError: If the prompt file doesn't exist
        """
        # Check cache first
        if name in self._cache:
            return self._cache[name]
            
        # Load from file
        file_path = self.prompts_dir / f"{name}.md"
        if not file_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {file_path}")
            
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Cache for future use
        self._cache[name] = content
        return content
        
    def interpolate(self, template: str, variables: Dict[str, Any]) -> str:
        """Interpolate variables into a prompt template.
        
        Args:
            template: The template string with {variable} placeholders
            variables: Dictionary of variable names to values
            
        Returns:
            The interpolated string
        """
        try:
            # Convert all values to strings for interpolation
            str_vars = {k: str(v) for k, v in variables.items()}
            return template.format(**str_vars)
        except KeyError as e:
            logger.error(f"Missing variable in template: {e}")
            raise
            
    def build_system_prompt(self, persona: Dict[str, Any], trading_context: Dict[str, Any]) -> str:
        """Build a complete system prompt from modular components.
        
        Args:
            persona: Persona configuration dictionary
            trading_context: Current trading context (positions, equity, etc.)
            
        Returns:
            Complete system prompt
        """
        # Calculate risk-based parameters
        risk_tolerance = persona.get('risk_tolerance', 0.5)
        max_position_percent = self._calculate_max_position_percent(risk_tolerance)
        max_total_exposure = self._calculate_max_exposure(risk_tolerance)
        
        # Prepare interpolation variables
        variables = {
            # Persona fields
            'name': persona.get('name', 'Trader'),
            'personality_traits': ', '.join(persona.get('personality_traits', [])),
            'trading_style': persona.get('trading_style', 'balanced'),
            'risk_tolerance': risk_tolerance,
            'favorite_assets': ', '.join(persona.get('favorite_assets', ['BTC', 'ETH'])),
            'speech_style': self._map_speech_style(persona.get('personality_type', 'midwit')),
            
            # Risk parameters  
            'max_position_percent': max_position_percent,
            'max_total_exposure': max_total_exposure,
            'max_correlated': max_total_exposure * 0.7,  # 70% of total for correlated
            'max_loss_percent': min(10, max_position_percent * 0.3),  # 30% of position max
            'daily_loss_limit': min(20, max_total_exposure * 0.2),  # 20% of exposure
            
            # Context fields
            'current_equity': trading_context.get('current_equity', 0),
            'free_margin': trading_context.get('free_margin', 0),
            'open_positions': trading_context.get('open_positions', 0),
            'current_pnl': trading_context.get('current_pnl', 0),
        }
        
        # Load and combine prompt components
        components = []
        
        # 1. System base
        base_prompt = self.load_prompt('system_base')
        components.append(self.interpolate(base_prompt, variables))
        
        # 2. Personality speech patterns
        speech_prompt = self.load_prompt('personality_speech')
        components.append(self.interpolate(speech_prompt, variables))
        
        # 3. Risk management rules
        risk_prompt = self.load_prompt('risk_management')
        components.append(self.interpolate(risk_prompt, variables))
        
        # 4. Tool usage policy
        tools_prompt = self.load_prompt('tools_policy')
        components.append(self.interpolate(tools_prompt, variables))
        
        # 5. Active trading encouragement
        trade_prompt = self.load_prompt('trade_loop')
        components.append(self.interpolate(trade_prompt, variables))
        
        # Combine all components
        return "\n\n---\n\n".join(components)
        
    def _calculate_max_position_percent(self, risk_tolerance: float) -> int:
        """Calculate max position size as percentage based on risk tolerance."""
        if risk_tolerance <= 0.2:
            return 10
        elif risk_tolerance <= 0.4:
            return 20
        elif risk_tolerance <= 0.6:
            return 30
        elif risk_tolerance <= 0.8:
            return 40
        else:
            return 50
            
    def _calculate_max_exposure(self, risk_tolerance: float) -> int:
        """Calculate max total exposure percentage based on risk tolerance."""
        if risk_tolerance <= 0.2:
            return 40
        elif risk_tolerance <= 0.4:
            return 60
        elif risk_tolerance <= 0.6:
            return 80
        elif risk_tolerance <= 0.8:
            return 100
        else:
            return 150
            
    def _map_speech_style(self, personality_type: str) -> str:
        """Map personality type to speech style."""
        mapping = {
            'cynical': 'Cynical Trader',
            'leftCurve': 'Left Curve',
            'midwit': 'Midwit'
        }
        return mapping.get(personality_type, 'Midwit')
        
    def reload_cache(self):
        """Clear the cache to force reload of prompts."""
        self._cache.clear()
        logger.info("Prompt cache cleared")


# Singleton instance
_prompt_loader = None


def get_prompt_loader() -> PromptLoader:
    """Get the singleton PromptLoader instance."""
    global _prompt_loader
    if _prompt_loader is None:
        _prompt_loader = PromptLoader()
    return _prompt_loader