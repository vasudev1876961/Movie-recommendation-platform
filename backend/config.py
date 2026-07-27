from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "movie_recom_db"
    jwt_secret: str = "supersecret_change_me_in_production_1234567890"
    access_token_expire_minutes: int = 1440
    tmdb_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
