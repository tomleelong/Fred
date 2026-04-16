"""Configuration management for the FRED MCP server."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class FredSettings(BaseSettings):
    """Loads FRED API configuration from environment variables or .env file.

    Attributes:
        api_key: FRED API key (32-char alphanumeric).
            Register at https://fredaccount.stlouisfed.org
        base_url: FRED API base URL.
    """

    model_config = SettingsConfigDict(
        env_prefix="FRED_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: str = Field(description="FRED API key")
    base_url: str = Field(
        default="https://api.stlouisfed.org/fred",
        description="FRED API base URL",
    )
