from flask import Blueprint, g, request
from flask_jwt_extended import get_jwt_identity
from marshmallow import ValidationError

from app.middleware.auth_middleware import (
    agente_owner_required,
    docente_required,
    login_required,
)
from app.schemas.agente_schemas import (
    AgenteCreateSchema,
    AgenteResponseSchema,
    AgenteUpdateSchema,
)
from app.services import agente_service
from app.services.agente_service import AgenteServiceError
from app.utils.responses import error_response, success_response

agente_bp = Blueprint("agentes", __name__, url_prefix="/api/v1/agentes")

response_schema = AgenteResponseSchema()
response_schema_many = AgenteResponseSchema(many=True)


@agente_bp.route("", methods=["GET"])
@login_required
def list_agentes():
    search = request.args.get("search")
    materia_id_raw = request.args.get("materia_id")
    try:
        materia_id = int(materia_id_raw) if materia_id_raw else None
    except ValueError:
        return error_response(
            "VALIDATION_ERROR",
            "materia_id debe ser un entero",
            400,
        )

    agentes = agente_service.get_all(search=search, materia_id=materia_id)
    return success_response(response_schema_many.dump(agentes))


@agente_bp.route("/<int:id>", methods=["GET"])
@login_required
def get_agente(id):
    try:
        agente = agente_service.get_by_id(id)
    except AgenteServiceError as err:
        return error_response(err.code, err.message, err.status)
    return success_response(response_schema.dump(agente))


@agente_bp.route("", methods=["POST"])
@docente_required
def create_agente():
    schema = AgenteCreateSchema()
    try:
        data = schema.load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return error_response("VALIDATION_ERROR", str(err.messages), 400)

    docente_id = int(get_jwt_identity())
    try:
        agente = agente_service.create(docente_id, data)
    except AgenteServiceError as err:
        return error_response(err.code, err.message, err.status)

    return success_response(
        response_schema.dump(agente),
        message="Agente creado",
        status=201,
    )


@agente_bp.route("/<int:id>", methods=["PUT"])
@agente_owner_required
def update_agente(id):
    schema = AgenteUpdateSchema()
    try:
        data = schema.load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return error_response("VALIDATION_ERROR", str(err.messages), 400)

    agente = agente_service.update(g.agente, data)
    return success_response(response_schema.dump(agente))


@agente_bp.route("/<int:id>", methods=["DELETE"])
@agente_owner_required
def delete_agente(id):
    agente_service.delete(g.agente)
    return "", 204
