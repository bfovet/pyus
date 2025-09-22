from pydantic_settings import BaseSettings, SettingsConfigDict

env_file = ".env"


class Settings(BaseSettings):
    # Database
    SQLITE_USER: str = "pyus"
    SQLITE_PWD: str = "pyus"
    SQLITE_DATABASE: str = "pyus"
    SYNC_SQLITE_HOST: str = f"sqlite:///{SQLITE_DATABASE}.db"
    SQLITE_HOST: str = f"sqlite+aiosqlite:///{SQLITE_DATABASE}.db"

    model_config = SettingsConfigDict(
        env_prefix="pyus_",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_file=env_file,
        extra="allow",
    )


settings = Settings()
