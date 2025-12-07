from pydantic_settings import BaseSettings
from typing import Optional, Literal
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Jamf Monitor"
    api_version: str = "v1"
    environment: Literal["development", "production"] = "development"
    
    jamf_url: str
    jamf_client_id: str
    jamf_client_secret: str
    
    check_in_threshold_hours: int = 24
    recon_threshold_hours: int = 24
    pending_command_threshold_hours: int = 6
    
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    secret_key: str
    access_token_expire_minutes: int = 30

    admin_username: str
    admin_password: str

    cache_ttl_seconds: int = 300
    
    # Database configuration
    database_path: str = "./jamf_monitor.db"
    
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "jamf_monitor"
    mysql_password: str = ""
    mysql_database: str = "jamf_monitor"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
