from app.models.materia import Materia
from app.repositories import materia_repository
from app.services.exceptions import MateriaServiceError


def get_all() -> list[Materia]:
    return materia_repository.find_all()


def get_by_id(materia_id: int) -> Materia:
    materia = materia_repository.find_by_id(materia_id)
    if materia is None:
        raise MateriaServiceError("MATERIA_NOT_FOUND", "Materia no existe", 404)
    return materia
