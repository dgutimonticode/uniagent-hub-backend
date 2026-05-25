import os

from flask import Flask

from app.config import config
from app.extensions import cors, db, jwt, migrate


def create_app(config_name: str | None = None) -> Flask:
    if config_name is None:
        config_name = os.getenv("APP_ENV") or os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    from . import models  # noqa: F401
    jwt.init_app(app)
    cors.init_app(app, origins=app.config["CORS_ORIGINS"])

    from app.utils.responses import error_response

    @jwt.unauthorized_loader
    def _missing_token(reason: str):
        return error_response("MISSING_TOKEN", "Authorization header faltante", 401)

    @jwt.invalid_token_loader
    def _invalid_token(reason: str):
        return error_response("INVALID_TOKEN", "Token JWT inválido", 401)

    @jwt.expired_token_loader
    def _expired_token(jwt_header, jwt_payload):
        return error_response("INVALID_TOKEN", "Token JWT expirado", 401)

    from app.routes import register_blueprints

    register_blueprints(app)

    @app.cli.command('seed')
    def seed_command() -> None:
        """Populate the database with initial data."""
        from app.seeds import seed_database
        seed_database()

    return app
