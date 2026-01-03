"""Configuration management for RISE AI trading bot."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # OpenRouter AI
    openrouter_api_key: str = ""
    openrouter_model: str = "x-ai/grok-4.1-fast"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    
    # RISE API
    rise_api_base: str = "https://api.testnet.rise.trade"
    rise_chain_id: int = 11155931
    
    # Trading configuration
    trade_interval_seconds: int = 300  # 5 minutes
    max_position_usd: float = 100.0
    
    # Admin API
    admin_api_key: str = ""  # Set via ADMIN_API_KEY environment variable
    
    # Environment
    environment: str = "testnet"
    debug: bool = False
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra environment variables


settings = Settings()