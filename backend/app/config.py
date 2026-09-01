import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
load_dotenv()
class Settings(BaseSettings):
    APP_NAME: str = "MMX Mechanics"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False") == "True"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://mmx:mmx@localhost:5432/mmx")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    USE_GPU: bool = os.getenv("USE_GPU", "True") == "True"
    GPU_DEVICE_ID: int = int(os.getenv("GPU_DEVICE_ID", "0"))
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "/app/uploads")
    RESULTS_DIR: str = os.getenv("RESULTS_DIR", "/app/results")
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "200"))
    DEFAULT_LANG: str = os.getenv("DEFAULT_LANG", "pt-BR")
    FREE_SIMULATION_LIMIT: int = int(os.getenv("FREE_SIMULATION_LIMIT", "5"))
    PRO_SIMULATION_LIMIT: int = int(os.getenv("PRO_SIMULATION_LIMIT", "100"))
    MAX_GRID_FREE: int = 128
    MAX_GRID_PRO: int = 512
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173", "https://mmx.figsmor.com.br"]
    class Config:
        env_file = ".env"
settings = Settings()
