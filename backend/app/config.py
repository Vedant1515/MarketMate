import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


logger = logging.getLogger(__name__)

# Resolve .env relative to this file's directory (app/), then up one level to backend/
_ENV_FILE = Path(__file__).parent.parent / ".env"

# Load .env into os.environ immediately so pydantic-settings can always find the values
load_dotenv(dotenv_path=_ENV_FILE, override=False, encoding="utf-8-sig")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8-sig",
        case_sensitive=False,
        extra="ignore",
    )

    anthropic_api_key: str
    llm_provider: str = "anthropic"
    llm_model: str = "claude-sonnet-4-6"
    chroma_persist_dir: str = "./chroma_db"
    sales_data_path: str = "./data/produce_sales.csv"
    demo_mode: bool = True
    cors_origins: List[str] = ["http://localhost:5173"]
    log_level: str = "INFO"

    @property
    def log_level_int(self) -> int:
        return getattr(logging, self.log_level.upper(), logging.INFO)


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    logger.info(
        "Settings loaded: provider=%s model=%s demo_mode=%s",
        settings.llm_provider,
        settings.llm_model,
        settings.demo_mode,
    )
    return settings
