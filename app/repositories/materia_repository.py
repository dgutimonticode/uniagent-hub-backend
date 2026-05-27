from app.extensions import db
from app.models.materia import Materia


def find_all() -> list[Materia]:
    return Materia.query.order_by(Materia.semestre, Materia.nombre).all()


def find_by_id(materia_id: int) -> Materia | None:
    return db.session.get(Materia, materia_id)
