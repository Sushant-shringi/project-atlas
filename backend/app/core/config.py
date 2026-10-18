"""
Project Atlas - Application Configuration
Uses pydantic-settings to load environment variables safely.
"""

from typing import Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    # Application & Environment
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    ADMIN_API_KEY: str = "atlas-admin-secret-key-change-in-production"

    # Gemini LLM Settings
    GEMINI_API_KEY: Optional[str] = os.getenv("GENAI_API_KEY") or os.getenv("GEMINI_API_KEY") or "placeholder-key"
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Qdrant Vector DB Settings
    QDRANT_HOST: str = "127.0.0.1"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "report_chunks"
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    VECTOR_DIMENSION: int = 384

    # MySQL Operational App Account
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_DATABASE: str = "project_atlas"
    MYSQL_USER: str = "atlas_app"
    MYSQL_PASSWORD: str = "atlas_app_secure_password"
    MYSQL_ROOT_PASSWORD: str = "atlas_root_secure_password"

    # MySQL Read-Only Analytical Account
    MYSQL_READONLY_USER: str = "atlas_readonly"
    MYSQL_READONLY_PASSWORD: str = "atlas_readonly_secure_password"

    # CodeIgniter 3 Portal
    PORTAL_PORT: int = 8080
    API_BASE_URL: str = "http://localhost:8000"

    # Security & Confidence Thresholds
    CONFIDENCE_THRESHOLD: float = 0.70
    MAX_RETRIEVAL_CHUNKS: int = 5
    REQUEST_TIMEOUT_SECONDS: int = 30

    # Licensing / Upgrade Paths
    UPGRADE_CONTACT_EMAIL: str = ""
    UPGRADE_PORTAL_URL: str = ""

    @model_validator(mode="after")
    def validate_security_credentials(self) -> "Settings":
        """
        Enforces that production deployments cannot use default or insecure credentials,
        while maintaining zero-friction setup for local development and automated testing.
        """
        env = (self.ENVIRONMENT or "").strip().lower()
        if env == "production":
            insecure_defaults = {
                "ADMIN_API_KEY": [
                    "atlas-admin-secret-key-change-in-production",
                    "placeholder-key",
                    "admin",
                    "secret",
                    ""
                ],
                "MYSQL_PASSWORD": [
                    "atlas_app_secure_password",
                    "password",
                    "root",
                    ""
                ],
                "MYSQL_ROOT_PASSWORD": [
                    "atlas_root_secure_password",
                    "password",
                    "root",
                    ""
                ],
                "MYSQL_READONLY_PASSWORD": [
                    "atlas_readonly_secure_password",
                    "password",
                    ""
                ],
                "GEMINI_API_KEY": [
                    "placeholder-key",
                    "your_gemini_api_key_here",
                    ""
                ]
            }

            errors = []
            if self.ADMIN_API_KEY in insecure_defaults["ADMIN_API_KEY"] or len(self.ADMIN_API_KEY) < 16:
                errors.append("Production requires a strong, non-default ADMIN_API_KEY (minimum 16 characters).")

            if self.MYSQL_PASSWORD in insecure_defaults["MYSQL_PASSWORD"]:
                errors.append("Production requires a secure, non-default MYSQL_PASSWORD.")

            if self.MYSQL_ROOT_PASSWORD in insecure_defaults["MYSQL_ROOT_PASSWORD"]:
                errors.append("Production requires a secure, non-default MYSQL_ROOT_PASSWORD.")

            if self.MYSQL_READONLY_PASSWORD in insecure_defaults["MYSQL_READONLY_PASSWORD"]:
                errors.append("Production requires a secure, non-default MYSQL_READONLY_PASSWORD.")

            if not self.GEMINI_API_KEY or self.GEMINI_API_KEY in insecure_defaults["GEMINI_API_KEY"]:
                errors.append("Production requires a valid, non-placeholder GEMINI_API_KEY.")

            if errors:
                raise ValueError("Insecure production configuration detected:\n- " + "\n- ".join(errors))

        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
