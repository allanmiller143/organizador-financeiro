import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    return default if value is None else value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    CDI_AUTO_SYNC = True

    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
    BREVO_API_KEY = os.getenv("BREVO_API_KEY")
    BREVO_FROM_EMAIL = os.getenv("BREVO_FROM_EMAIL")
    BREVO_FROM_NAME = os.getenv("BREVO_FROM_NAME", "Organizador Financeiro")
    PASSWORD_RESET_TOKEN_MINUTES = int(os.getenv("PASSWORD_RESET_TOKEN_MINUTES", "30"))
    PASSWORD_RESET_DEBUG = _env_bool("PASSWORD_RESET_DEBUG", False)


class DevelopmentConfig(Config):
    DEBUG = True
    PASSWORD_RESET_DEBUG = _env_bool("PASSWORD_RESET_DEBUG", True)


class TestingConfig(Config):
    TESTING = True
    SECRET_KEY = "chave-de-teste-com-mais-de-32-caracteres-0123456789"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    CDI_AUTO_SYNC = False
    PASSWORD_RESET_DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    PASSWORD_RESET_DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
