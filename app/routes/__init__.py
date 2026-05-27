from flask import Flask


def register_blueprints(app: Flask) -> None:
    from app.routes.agente_routes import agente_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.health_routes import health_bp
    from app.routes.materia_routes import materia_bp
    from app.routes.skill_routes import skill_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(materia_bp)
    app.register_blueprint(agente_bp)
    app.register_blueprint(skill_bp)
