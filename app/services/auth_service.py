from datetime import datetime, timezone

from flask_jwt_extended import create_access_token

from app.extensions import db
from app.models.usuario import Usuario
from app.repositories import usuario_repository


def login(email: str, password: str) -> tuple[Usuario, str] | None:
    user = usuario_repository.find_by_email(email)
    if user is None or not user.check_password(password):
        return None

    user.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return user, token


def get_user_by_id(user_id: int) -> Usuario | None:
    return usuario_repository.find_by_id(user_id)
