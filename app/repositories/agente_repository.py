from app.extensions import db
from app.models.agente import Agente


def find_by_id(agente_id: int) -> Agente | None:
    return db.session.get(Agente, agente_id)


def find_all(
    search: str | None = None,
    materia_id: int | None = None,
) -> list[Agente]:
    query = Agente.query
    if search:
        query = query.filter(Agente.nombre.ilike(f"%{search}%"))
    if materia_id is not None:
        query = query.filter(Agente.materia_id == materia_id)
    return query.all()


def find_by_materia(materia_id: int) -> list[Agente]:
    return Agente.query.filter_by(materia_id=materia_id).all()


def find_by_docente(docente_id: int) -> list[Agente]:
    return Agente.query.filter_by(docente_id=docente_id).all()


def find_by_docente_y_materia(docente_id: int, materia_id: int) -> Agente | None:
    return Agente.query.filter_by(
        docente_id=docente_id,
        materia_id=materia_id,
    ).first()


def create(data: dict) -> Agente:
    agente = Agente(**data)
    db.session.add(agente)
    db.session.commit()
    return agente


def update(agente: Agente, data: dict) -> Agente:
    for key, value in data.items():
        setattr(agente, key, value)
    db.session.commit()
    return agente


def delete(agente: Agente) -> None:
    db.session.delete(agente)
    db.session.commit()
