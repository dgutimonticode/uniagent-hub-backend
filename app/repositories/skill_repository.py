from app.extensions import db
from app.models.skill import Skill


def find_by_id(skill_id: int) -> Skill | None:
    return db.session.get(Skill, skill_id)


def find_by_agente(agente_id: int) -> list[Skill]:
    return (
        Skill.query.filter_by(agente_id=agente_id)
        .order_by(Skill.orden.asc(), Skill.id.asc())
        .all()
    )


def find_by_agente_and_nombre(agente_id: int, nombre: str) -> Skill | None:
    return Skill.query.filter_by(agente_id=agente_id, nombre=nombre).first()


def create(data: dict) -> Skill:
    skill = Skill(**data)
    db.session.add(skill)
    db.session.commit()
    return skill


def update(skill: Skill, data: dict) -> Skill:
    for key, value in data.items():
        setattr(skill, key, value)
    db.session.commit()
    return skill


def delete(skill: Skill) -> None:
    db.session.delete(skill)
    db.session.commit()


def delete_many(skills: list[Skill]) -> None:
    if not skills:
        return
    for skill in skills:
        db.session.delete(skill)
    db.session.commit()
