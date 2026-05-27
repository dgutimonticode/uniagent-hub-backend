import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.skill import Skill
from app.repositories import skill_repository


@pytest.fixture
def skill(app, agente):
    s = Skill(
        agente_id=agente.id,
        nombre="Cinemática",
        descripcion="MRU y MRUA",
        s3_key=f"{agente.s3_prefix}/cinematica.md",
        tamano_kb=1,
        orden=0,
    )
    db.session.add(s)
    db.session.commit()
    return s


class TestFindById:
    def test_existente_devuelve_skill(self, app, skill):
        result = skill_repository.find_by_id(skill.id)
        assert result is not None
        assert result.id == skill.id

    def test_inexistente_devuelve_none(self, app):
        assert skill_repository.find_by_id(9999) is None


class TestFindByAgente:
    def test_sin_skills_devuelve_lista_vacia(self, app, agente):
        assert skill_repository.find_by_agente(agente.id) == []

    def test_con_skills_devuelve_lista(self, app, agente, skill):
        result = skill_repository.find_by_agente(agente.id)
        assert len(result) == 1
        assert result[0].id == skill.id


class TestFindByAgenteAndNombre:
    def test_match_devuelve_skill(self, app, agente, skill):
        result = skill_repository.find_by_agente_and_nombre(agente.id, "Cinemática")
        assert result is not None
        assert result.id == skill.id

    def test_no_match_devuelve_none(self, app, agente, skill):
        result = skill_repository.find_by_agente_and_nombre(agente.id, "Dinámica")
        assert result is None


class TestCreate:
    def test_persiste_skill(self, app, agente):
        result = skill_repository.create(
            {
                "agente_id": agente.id,
                "nombre": "Dinámica",
                "descripcion": None,
                "s3_key": f"{agente.s3_prefix}/dinamica.md",
                "tamano_kb": 2,
                "orden": 0,
            }
        )
        assert result.id is not None
        assert result.nombre == "Dinámica"


class TestUpdate:
    def test_modifica_campos(self, app, skill):
        result = skill_repository.update(skill, {"nombre": "Nuevo nombre"})
        assert result.nombre == "Nuevo nombre"

        again = skill_repository.find_by_id(skill.id)
        assert again.nombre == "Nuevo nombre"


class TestDelete:
    def test_remueve_skill(self, app, skill):
        skill_id = skill.id
        skill_repository.delete(skill)
        assert skill_repository.find_by_id(skill_id) is None


class TestDeleteMany:
    def test_lista_vacia_no_falla(self, app):
        skill_repository.delete_many([])

    def test_borra_varios(self, app, agente):
        skills = []
        for i in range(3):
            s = Skill(
                agente_id=agente.id,
                nombre=f"Skill {i}",
                s3_key=f"{agente.s3_prefix}/skill-{i}.md",
                tamano_kb=1,
                orden=i,
            )
            db.session.add(s)
            skills.append(s)
        db.session.commit()

        skill_repository.delete_many(skills)
        assert skill_repository.find_by_agente(agente.id) == []


class TestUniqueConstraint:
    def test_mismo_nombre_mismo_agente_falla(self, app, agente, skill):
        with pytest.raises(IntegrityError):
            skill_repository.create(
                {
                    "agente_id": agente.id,
                    "nombre": "Cinemática",
                    "descripcion": None,
                    "s3_key": f"{agente.s3_prefix}/cinematica-2.md",
                    "tamano_kb": 1,
                    "orden": 1,
                }
            )
