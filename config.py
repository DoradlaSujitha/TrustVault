from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    database_url: str = "sqlite:///./trustvault.db"
    jwt_secret_key: str = "development-only-change-me"
    access_token_minutes: int = 30
    max_upload_mb: int = 10
    storage_dir: str = "storage"
    cors_origins: str = "http://localhost:8501,http://127.0.0.1:8501"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    @property
    def cors_origin_list(self): return [x.strip() for x in self.cors_origins.split(",") if x.strip()]
settings = Settings()
