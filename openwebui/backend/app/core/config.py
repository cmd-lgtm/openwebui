"""
Application Configuration
"""
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    # App settings
    APP_NAME: str = "NexusAI IDE"
    DEBUG: bool = Field(default=True)
    ENVIRONMENT: str = Field(default="development")
    DEMO_MODE: bool = Field(default=False)  # Enable for development only
    DEMO_MODE: bool = Field(default=False)  # Set to True for development only

    # Security
    SECRET_KEY: str = Field(default="dev-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./nexusai.db")

    # Ollama settings
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434")
    OLLAMA_ENABLED: bool = Field(default=True)
    OLLAMA_DEFAULT_MODEL: str = Field(default="llama3.2")

    # OpenAI settings
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    OPENAI_ENABLED: bool = Field(default=False)
    OPENAI_DEFAULT_MODEL: str = Field(default="gpt-4o-mini")
    OPENAI_ORGANIZATION: Optional[str] = Field(default=None)

    # Anthropic settings
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None)
    ANTHROPIC_ENABLED: bool = Field(default=False)
    ANTHROPIC_DEFAULT_MODEL: str = Field(default="claude-3-haiku-20240307")

    # Azure OpenAI settings
    AZURE_OPENAI_API_KEY: Optional[str] = Field(default=None)
    AZURE_OPENAI_ENDPOINT: Optional[str] = Field(default=None)
    AZURE_OPENAI_DEPLOYMENT: Optional[str] = Field(default=None)
    AZURE_OPENAI_ENABLED: bool = Field(default=False)

    # Groq settings
    GROQ_API_KEY: Optional[str] = Field(default=None)
    GROQ_ENABLED: bool = Field(default=False)
    GROQ_DEFAULT_MODEL: str = Field(default="llama-3.1-70b-versatile")

    # HuggingFace settings
    HUGGINGFACE_API_KEY: Optional[str] = Field(default=None)
    HUGGINGFACE_ENABLED: bool = Field(default=False)

    # Google AI settings
    GOOGLE_API_KEY: Optional[str] = Field(default=None)
    GOOGLE_ENABLED: bool = Field(default=False)

    # Mistral AI settings
    MISTRAL_API_KEY: Optional[str] = Field(default=None)
    MISTRAL_ENABLED: bool = Field(default=False)

    # Cohere settings
    COHERE_API_KEY: Optional[str] = Field(default=None)
    COHERE_ENABLED: bool = Field(default=False)

    # Code execution
    CODE_EXECUTION_ENABLED: bool = Field(default=True)
    CODE_EXECUTION_TIMEOUT: int = 30  # seconds

    # RAG / Embeddings
    EMBEDDINGS_PROVIDER: str = Field(default="ollama")  # ollama, openai, huggingface
    VECTOR_DB_URL: Optional[str] = Field(default=None)

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True)
    RATE_LIMIT_PER_MINUTE: int = 60

    # File settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: list = Field(default_factory=lambda: [
        ".txt", ".md", ".json", ".yaml", ".yml", ".toml",
        ".js", ".jsx", ".ts", ".tsx", ".py", ".java",
        ".cpp", ".c", ".h", ".hpp", ".go", ".rs",
        ".html", ".css", ".scss", ".sql", ".sh", ".bash"
    ])

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings"""
    return Settings()


settings = get_settings()
