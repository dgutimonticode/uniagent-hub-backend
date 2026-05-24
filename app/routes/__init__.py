from flask import Flask


def register_blueprints(app: Flask) -> None:
    from app.routes.auth_routes import auth_bp
    from app.routes.health_routes import health_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
