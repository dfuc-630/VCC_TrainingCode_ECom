from flask import Flask
from .extensions import db, migrate, jwt, ma
from .config import Config


def create_app():

    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)

    from .routes.auth import auth_bp
    from .routes.user import user_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)

    return app