import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, computed_field

# 1. Lokalizacja projektu
CURRENT_FILE_PATH = Path(__file__).resolve()
DEFAULT_ROOT = CURRENT_FILE_PATH.parent.parent

class Settings(BaseSettings):
    # --- PODSTAWOWE ---
    API_TITLE: str = "Salary Predictor API"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    API_PORT: int = 8000
    API_URL: str = "http://127.0.0.1:8000"
    PROJECT_ROOT: Path = Field(default=DEFAULT_ROOT)

    # --- ŚCIEŻKI JAKO METODY (Pewność działania) ---
    # Zmieniamy @property na zwykłe metody, aby uniknąć konfliktów z Pydantic
    def get_data_dir(self) -> Path:
        path = self.PROJECT_ROOT / "data"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_log_dir(self) -> Path:
        path = self.PROJECT_ROOT / "logs" / "api"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def MODEL_NAME(self) -> str:
        return str(self.get_data_dir() / "final_salary_model")

    @property
    def DEFAULTS_JSON_PATH(self) -> Path:
        return self.get_data_dir() / "model_defaults.json"

    @property
    def LOG_DIR(self) -> Path:
        return self.get_log_dir()

    model_config = SettingsConfigDict(
        env_file=str(DEFAULT_ROOT / ".env"),
        extra="ignore"
    )

def get_settings():
    env_path = DEFAULT_ROOT / ".env"
    if not env_path.exists():
        content = (
            f"PROJECT_ROOT={DEFAULT_ROOT}\n"
            "LOG_LEVEL=INFO\n"
            "API_URL=http://127.0.0.1:8000\n"
        )
        env_path.write_text(content, encoding="utf-8")
    return Settings()

settings = get_settings()
