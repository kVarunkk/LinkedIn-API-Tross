"""Configuration for LinkedIn Profile API."""
import os
from typing import Optional
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class Settings:
    """Application settings with environment variable support."""
    
    # Session cookies
    LINKEDIN_LI_AT: Optional[str] = os.getenv("LINKEDIN_LI_AT")
    LINKEDIN_JSESSIONID: Optional[str] = os.getenv("LINKEDIN_JSESSIONID")
    
    # API configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8080"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # User-Agent (optional; overrides default if set)
    USER_AGENT: Optional[str] = os.getenv("USER_AGENT")
    
    # Rate limiting
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    
    # Cache
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes

settings = Settings()