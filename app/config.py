import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
load_dotenv()
BASEDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "secret")

    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = quote_plus(os.getenv("DB_PASSWORD", ""))
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "")

    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv("JWT_SECRET", "jwt-secret")

    UPLOAD_FOLDER = "uploads"
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
