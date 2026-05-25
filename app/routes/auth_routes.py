from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity
from marshmallow import ValidationError

from app.middleware.auth_middleware import login_required
from app.schemas.auth_schemas import LoginSchema
from app.services import auth_service
from app.utils.responses import error_response, success_response

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


@auth_bp.route("/login", methods=["POST"])
def login():
    schema = LoginSchema()
    try:
        data = schema.load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return error_response("VALIDATION_ERROR", str(err.messages), 400)

    result = auth_service.login(data["email"], data["password"])
    if result is None:
        return error_response(
            "INVALID_CREDENTIALS",
            "Email o contraseña incorrectos",
            401,
        )

    user, token = result
    return success_response(
        {"token": token, "user": user.to_dict()},
        message="Login exitoso",
    )


@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    user_id = int(get_jwt_identity())
    user = auth_service.get_user_by_id(user_id)
    if user is None:
        return error_response("USER_NOT_FOUND", "Usuario no existe", 404)

    return success_response(user.to_dict())
