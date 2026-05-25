from unittest.mock import MagicMock

import pytest

from app.extensions import db
from app.models.skill import Skill
from app.services import agente_service
from app.services.exceptions import S3ServiceError


@pytest.fixture
def mock_s3(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr(
        "app.services.agente_service.s3_service", mock, raising=False
    )
    return mock


@pytest.fixture
def agente_con_skills(app, agente):
    skills = []
    for i in range(2):
        s = Skill(
            agente_id=agente.id,
            nombre=f"Skill {i}",
            descripcion=None,
            s3_key=f"{agente.s3_prefix}/skill-{i}.md",
            tamano_kb=1,
            orden=i,
        )
        db.session.add(s)
        skills.append(s)
    db.session.commit()
    return agente, skills


class TestDeleteCascade:
    def test_borra_s3_y_db_de_cada_skill(self, app, agente_con_skills, mock_s3):
        agente, skills = agente_con_skills
        expected_keys = [s.s3_key for s in skills]
        skill_ids = [s.id for s in skills]

        agente_service.delete(agente)

        assert mock_s3.delete_file.call_count == len(skills)
        called_keys = [call.args[0] for call in mock_s3.delete_file.call_args_list]
        assert sorted(called_keys) == sorted(expected_keys)

        from app.repositories import skill_repository
        for sid in skill_ids:
            assert skill_repository.find_by_id(sid) is None

    def test_idempotente_si_skill_no_existe_en_s3(
        self, app, agente_con_skills, mock_s3
    ):
        agente, skills = agente_con_skills
        mock_s3.delete_file.side_effect = S3ServiceError(
            "S3_NOT_FOUND", "missing"
        )
        # debería ignorar S3_NOT_FOUND y seguir borrando DB
        agente_service.delete(agente)
        from app.repositories import skill_repository
        for s in skills:
            assert skill_repository.find_by_id(s.id) is None

    def test_otros_errores_s3_propagan(self, app, agente_con_skills, mock_s3):
        agente, _ = agente_con_skills
        mock_s3.delete_file.side_effect = S3ServiceError("S3_ERROR", "boom")
        with pytest.raises(S3ServiceError):
            agente_service.delete(agente)
