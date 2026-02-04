import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "secret")

    SQLALCHEMY_DATABASE_URI = (
        os.getenv("DB_URI") or
        "sqlite:///" + os.path.join(basedir, "db.sqlite")
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv("JWT_SECRET", "jwt-secret")

    UPLOAD_FOLDER = "uploads"
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
