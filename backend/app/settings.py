from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_secret_key: str = "local-only-change-me"
    cors_origins: str = "http://localhost:5173"
    netbox_url: str | None = None
    netbox_token: str | None = None
    zabbix_url: str | None = None
    zabbix_token: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
