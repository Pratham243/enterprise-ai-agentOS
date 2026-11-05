"""Application configuration.

Reads settings from environment variables (and .env file when present).
Each setting has a safe default so the app starts without any env file
during development.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration loaded once at startup."""

    app_name: str = "Enterprise AI AgentOS"
    app_env: str = "development"
    debug: bool = False

    # Database — defaults to a local SQLite file for development.
    # In production this will be a PostgreSQL connection string.
    database_url: str = "sqlite+aiosqlite:///./agentos.db"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # Azure OpenAI (alternative to direct OpenAI)
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_deployment: str = ""

    # Pinecone vector database
    pinecone_api_key: str = ""
    pinecone_environment: str = ""
    pinecone_index_name: str = "agentos"

    # JWT authentication
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


# Single shared instance — import this wherever settings are needed.
settings = Settings()
