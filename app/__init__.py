import os

from flask import Flask

from app.config import config
from app.extensions import cors, db, jwt, migrate


def create_app(config_name: str | None = None) -> Flask:
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, origins=app.config["CORS_ORIGINS"])

    from app.routes import register_blueprints

    register_blueprints(app)

    return app
