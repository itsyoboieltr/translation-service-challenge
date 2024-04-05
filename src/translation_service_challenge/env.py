"""Module that contains the Env model for environment variables."""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Env(BaseSettings):
    """Model that contains environment variables."""

    model_config = SettingsConfigDict()

    DATABASE_URL: str = ""

    @field_validator("DATABASE_URL")
    @classmethod
    def check_not_empty(cls, value):
        """Validates that the value is not empty."""
        if value == "":
            raise ValueError("DATABASE_URL environment variable is empty")
        return value


# Load and validate environment variables
env = Env()
