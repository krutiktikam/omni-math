import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

def get_valid_storage_path() -> Path:
    r"""
    Health-gate check against E:\omnimath_storage\.
    Falls back to local ./data on SSD if E:\ is unavailable.
    """
    e_path = Path("E:/omnimath_storage")
    try:
        if e_path.exists() and e_path.is_dir():
            # Test write access
            test_file = e_path / ".health_gate_check"
            test_file.touch()
            test_file.unlink()
            return e_path
    except Exception:
        pass
    
    local_data = Path("./data").resolve()
    local_data.mkdir(parents=True, exist_ok=True)
    return local_data

storage_root = get_valid_storage_path()
hf_cache = storage_root / "models" / "huggingface"
hf_cache.mkdir(parents=True, exist_ok=True)
os.environ["HF_HOME"] = str(hf_cache)
os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(hf_cache)

class Settings(BaseSettings):
    app_name: str = "Omnimath Backend"
    storage_path: Path = storage_root
    debug: bool = False
    ollama_base_url: str = "http://localhost:11434"
    default_model: str = "deepseek-r1:1.5b"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="OMNIMATH_")

settings = Settings()
