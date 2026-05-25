from flask import Blueprint

from app.schemas.materia_schemas import MateriaResponseSchema
from app.services import materia_service
from app.services.exceptions import MateriaServiceError
from app.utils.responses import error_response, success_response

materia_bp = Blueprint("materias", __name__, url_prefix="/api/v1/materias")

response_schema = MateriaResponseSchema()
response_schema_many = MateriaResponseSchema(many=True)


@materia_bp.route("", methods=["GET"])
def list_materias():
    materias = materia_service.get_all()
    return success_response(response_schema_many.dump(materias))


@materia_bp.route("/<int:id>", methods=["GET"])
def get_materia(id):
    try:
        materia = materia_service.get_by_id(id)
    except MateriaServiceError as err:
        return error_response(err.code, err.message, err.status)
    return success_response(response_schema.dump(materia))
