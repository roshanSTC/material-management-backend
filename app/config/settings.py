import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:kTLf.A+4IsD<LQCt@34.14.155.173:5432/material_management",
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    STORAGE_BACKEND = os.getenv( "STORAGE_BACKEND", "local", )
    
    ATTACHMENT_STORAGE_PATH = os.getenv(
        "ATTACHMENT_STORAGE_PATH",
        "storage/attachments",
    )
    
    API_TITLE = "Material Management API"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.3"

    OPENAPI_URL_PREFIX = "/api/docs"
    OPENAPI_SWAGGER_UI_PATH = "/swagger-ui"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")

    if not JWT_SECRET_KEY:
        raise RuntimeError("JWT_SECRET_KEY is not configured")

    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60
    JWT_REFRESH_TOKEN_EXPIRES = 60 * 60 * 24 * 30