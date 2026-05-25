from flask import Blueprint, g, request
from marshmallow import ValidationError

from app.middleware.auth_middleware import (
    agente_owner_required,
    login_required,
)
from app.schemas.skill_schemas import (
    SkillCreateSchema,
    SkillDetailSchema,
    SkillDownloadSchema,
    SkillResponseSchema,
    SkillUpdateSchema,
)
from app.services import agente_service, skill_service
from app.services.agente_service import AgenteServiceError
from app.services.exceptions import S3ServiceError, SkillServiceError
from app.utils.responses import error_response, success_response

skill_bp = Blueprint(
    "skills",
    __name__,
    url_prefix="/api/v1/agentes/<int:agente_id>/skills",
)

response_schema = SkillResponseSchema()
response_schema_many = SkillResponseSchema(many=True)
detail_schema = SkillDetailSchema()
download_schema = SkillDownloadSchema()


def _handle_s3_error(err: S3ServiceError):
    if err.code == "S3_NOT_FOUND":
        return error_response(err.code, err.message, 404)
    return error_response("S3_ERROR", err.message, 502)


def _ensure_agente_exists(agente_id: int):
    try:
        return agente_service.get_by_id(agente_id)
    except AgenteServiceError as err:
        return error_response(err.code, err.message, err.status)


@skill_bp.route("", methods=["GET"])
@login_required
def list_skills(agente_id: int):
    agente_or_response = _ensure_agente_exists(agente_id)
    if not hasattr(agente_or_response, "id"):
        return agente_or_response

    skills = skill_service.get_by_agente(agente_id)
    return success_response(response_schema_many.dump(skills))


@skill_bp.route("/<int:id>", methods=["GET"])
@login_required
def get_skill_detail(agente_id: int, id: int):
    agente_or_response = _ensure_agente_exists(agente_id)
    if not hasattr(agente_or_response, "id"):
        return agente_or_response

    try:
        skill = skill_service.get_by_id(id)
        contenido = skill_service.get_content(id)
    except SkillServiceError as err:
        return error_response(err.code, err.message, err.status)
    except S3ServiceError as err:
        return _handle_s3_error(err)

    skill.contenido = contenido
    return success_response(detail_schema.dump(skill))


@skill_bp.route("/<int:id>/download", methods=["GET"])
@login_required
def download_skill(agente_id: int, id: int):
    agente_or_response = _ensure_agente_exists(agente_id)
    if not hasattr(agente_or_response, "id"):
        return agente_or_response

    try:
        payload = skill_service.get_presigned_url(id, expiration=900)
    except SkillServiceError as err:
        return error_response(err.code, err.message, err.status)
    except S3ServiceError as err:
        return _handle_s3_error(err)

    return success_response(download_schema.dump(payload))


@skill_bp.route("", methods=["POST"])
@agente_owner_required
def create_skill(agente_id: int):
    schema = SkillCreateSchema()
    try:
        data = schema.load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return error_response("VALIDATION_ERROR", str(err.messages), 400)

    try:
        skill = skill_service.create(g.agente, data)
    except SkillServiceError as err:
        return error_response(err.code, err.message, err.status)
    except S3ServiceError as err:
        return _handle_s3_error(err)

    return success_response(
        response_schema.dump(skill),
        message="Skill creada",
        status=201,
    )


@skill_bp.route("/<int:id>", methods=["PUT"])
@agente_owner_required
def update_skill(agente_id: int, id: int):
    schema = SkillUpdateSchema()
    try:
        data = schema.load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return error_response("VALIDATION_ERROR", str(err.messages), 400)

    try:
        skill = skill_service.get_by_id(id)
        skill = skill_service.update(skill, data)
    except SkillServiceError as err:
        return error_response(err.code, err.message, err.status)
    except S3ServiceError as err:
        return _handle_s3_error(err)

    return success_response(response_schema.dump(skill))


@skill_bp.route("/<int:id>", methods=["DELETE"])
@agente_owner_required
def delete_skill(agente_id: int, id: int):
    try:
        skill = skill_service.get_by_id(id)
        skill_service.delete(skill)
    except SkillServiceError as err:
        return error_response(err.code, err.message, err.status)
    except S3ServiceError as err:
        return _handle_s3_error(err)

    return "", 204
