from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.agente import Agente
from app.models.materia import Materia
from app.repositories import agente_repository, skill_repository
from app.services.exceptions import S3ServiceError
from app.services.s3_service import s3_service
from app.utils.slugify import slugify


class AgenteServiceError(Exception):
    def __init__(self, code: str, message: str, status: int) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


def get_all(
    search: str | None = None,
    materia_id: int | None = None,
) -> list[Agente]:
    return agente_repository.find_all(search=search, materia_id=materia_id)


def get_by_id(agente_id: int) -> Agente:
    agente = agente_repository.find_by_id(agente_id)
    if agente is None:
        raise AgenteServiceError("AGENT_NOT_FOUND", "Agente no existe", 404)
    return agente


def create(docente_id: int, data: dict) -> Agente:
    materia = db.session.get(Materia, data["materia_id"])
    if materia is None:
        raise AgenteServiceError("MATERIA_NOT_FOUND", "Materia no existe", 404)

    existing = agente_repository.find_by_docente_y_materia(docente_id, materia.id)
    if existing is not None:
        raise AgenteServiceError(
            "DUPLICATE_AGENT",
            "Ya tenés un agente para esta materia",
            409,
        )

    payload = {
        "nombre": data["nombre"],
        "descripcion": data.get("descripcion"),
        "icono": data.get("icono") or "🤖",
        "materia_id": materia.id,
        "docente_id": docente_id,
        "s3_prefix": slugify(materia.nombre),
    }

    try:
        return agente_repository.create(payload)
    except IntegrityError:
        db.session.rollback()
        raise AgenteServiceError(
            "DUPLICATE_AGENT",
            "Conflicto al crear agente",
            409,
        )


def update(agente: Agente, data: dict) -> Agente:
    return agente_repository.update(agente, data)


def delete(agente: Agente) -> None:
    skills = skill_repository.find_by_agente(agente.id)
    for skill in skills:
        try:
            s3_service.delete_file(skill.s3_key)
        except S3ServiceError as err:
            if err.code != "S3_NOT_FOUND":
                raise

    if skills:
        skill_repository.delete_many(skills)

    agente_repository.delete(agente)
    # TODO: publicar evento SQS para cada skill borrada (ASL futuro)
