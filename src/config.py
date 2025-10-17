from pydantic_settings import BaseSettings


class Config(BaseSettings):
    app_name: str = "Tappy"
    debug: bool = False
    database_url: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class ProdConfig(Config):
    app_name: str = "Tappy Prod"
    debug: bool = False
    database_url: str = "postgresql+psycopg2://tappy:tappy@postgres_prod:5432"


class TestConfig(Config):
    app_name: str = "Tappy Test"
    debug: bool = True
    database_url: str = (
        "postgresql+psycopg2://tappyuser:tappypassword@postgres_test:5432/tappydb"
    )


config: None | Config = None
