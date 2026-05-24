from flask import Flask


def register_blueprints(app: Flask) -> None:
    from app.routes.health_routes import health_bp

    app.register_blueprint(health_bp)
