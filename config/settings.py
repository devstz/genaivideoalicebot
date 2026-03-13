from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    TOKEN: str = 'TOKEN'
    DATABASE_URL: str = 'DATABASE_URL'
    AGREEMENT_URL: str = ""
    MEDIA_ROOT: str = "./media"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    BOT_USERNAME: str = ""
    PIAPI_KEY: str = "PIAPI_KEY"

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )


settings = Config()

def get_settings():
    return settings
