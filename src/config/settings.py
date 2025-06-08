"""Application settings management."""
import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env file in development environment
if os.getenv("ENVIRONMENT", "development") == "development":
    load_dotenv()


@dataclass
class Settings:
    """Application settings."""

    # Google Cloud
    project_id: str
    bigquery_dataset: str
    bigquery_table: str
    bigquery_location: str

    # J-Quants API
    jquants_base_url: str
    jquants_refresh_token_secret: str
    jquants_email: Optional[str] = None
    jquants_password: Optional[str] = None

    # Application settings
    log_level: str = "INFO"
    retry_max_attempts: int = 3
    timeout_seconds: int = 30

    # Development settings
    environment: str = "development"
    debug: bool = False
    port: int = 8080

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables."""
        return cls(
            project_id=os.environ["GOOGLE_CLOUD_PROJECT"],
            bigquery_dataset=os.environ["BIGQUERY_DATASET"],
            bigquery_table=os.environ["BIGQUERY_TABLE"],
            bigquery_location=os.getenv("BIGQUERY_LOCATION", "asia-northeast1"),
            jquants_base_url=os.environ["JQUANTS_BASE_URL"],
            jquants_refresh_token_secret=os.environ["JQUANTS_REFRESH_TOKEN_SECRET"],
            jquants_email=os.getenv("JQUANTS_EMAIL"),
            jquants_password=os.getenv("JQUANTS_PASSWORD"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            retry_max_attempts=int(os.getenv("RETRY_MAX_ATTEMPTS", "3")),
            timeout_seconds=int(os.getenv("TIMEOUT_SECONDS", "30")),
            environment=os.getenv("ENVIRONMENT", "development"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            port=int(os.getenv("PORT", "8080"))
        )


# Create singleton instance
try:
    settings = Settings.from_env()
except KeyError as e:
    raise RuntimeError(
        f"Missing required environment variable: {e}. "
        "Please check your .env file or environment settings."
    ) from e
