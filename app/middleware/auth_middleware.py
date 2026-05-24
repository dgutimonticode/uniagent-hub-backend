from functools import wraps
from typing import Any, Callable

from flask_jwt_extended import get_jwt_identity, jwt_required

from app.models.usuario import Usuario
from app.repositories import usuario_repository
from app.utils.responses import error_response


def login_required(fn: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(fn)
    @jwt_required()
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return fn(*args, **kwargs)

    return wrapper


def docente_required(fn: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(fn)
    @jwt_required()
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        user_id = int(get_jwt_identity())
        user = usuario_repository.find_by_id(user_id)
        if user is None or user.rol != Usuario.ROL_DOCENTE:
            return error_response(
                "FORBIDDEN",
                "Esta operación requiere rol de docente",
                403,
            )
        return fn(*args, **kwargs)

    return wrapper
