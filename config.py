from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    app_name: str = "Omnimath Backend"
    storage_path: Path = Path("./data")
    debug: bool = False
    ollama_base_url: str = "http://localhost:11434"
    default_model: str = "deepseek-r1:1.5b"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="OMNIMATH_")

settings = Settings()
