from app.models.usuario import Usuario


def find_by_email(email: str) -> Usuario | None:
    return Usuario.query.filter_by(email=email).first()


def find_by_id(user_id: int) -> Usuario | None:
    return Usuario.query.get(user_id)
