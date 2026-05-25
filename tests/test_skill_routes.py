from unittest.mock import MagicMock

import pytest

from app.extensions import db
from app.models.skill import Skill
from app.services import skill_service
from app.services.exceptions import S3ServiceError


@pytest.fixture
def mock_s3(monkeypatch):
    mock = MagicMock()
    mock.upload_file.return_value = None
    mock.download_file.return_value = b"# Cinematica\n"
    mock.delete_file.return_value = None
    mock.generate_presigned_url.return_value = "https://example/presigned-url"
    monkeypatch.setattr(skill_service, "s3_service", mock)
    return mock


@pytest.fixture
def skill(app, agente):
    s = Skill(
        agente_id=agente.id,
        nombre="Cinemática",
        descripcion="MRU",
        s3_key=f"{agente.s3_prefix}/cinematica.md",
        tamano_kb=1,
        orden=0,
    )
    db.session.add(s)
    db.session.commit()
    return s


def skills_url(agente_id: int, suffix: str = "") -> str:
    return f"/api/v1/agentes/{agente_id}/skills{suffix}"


class TestListSkills:
    def test_sin_token_401(self, client, agente):
        response = client.get(skills_url(agente.id))
        assert response.status_code == 401
        assert response.get_json()["error"]["code"] == "MISSING_TOKEN"

    def test_lista_vacia_200(self, client, auth_headers_docente, agente):
        response = client.get(skills_url(agente.id), headers=auth_headers_docente)
        assert response.status_code == 200
        assert response.get_json()["data"] == []

    def test_con_skill_200(self, client, auth_headers_docente, agente, skill):
        response = client.get(skills_url(agente.id), headers=auth_headers_docente)
        assert response.status_code == 200
        data = response.get_json()["data"]
        assert len(data) == 1
        assert data[0]["id"] == skill.id
        assert data[0]["nombre"] == "Cinemática"


class TestGetSkillDetail:
    def test_200_con_contenido(
        self, client, auth_headers_docente, agente, skill, mock_s3
    ):
        response = client.get(
            skills_url(agente.id, f"/{skill.id}"), headers=auth_headers_docente
        )
        assert response.status_code == 200
        data = response.get_json()["data"]
        assert data["id"] == skill.id
        assert data["contenido"] == "# Cinematica\n"

    def test_404_skill_not_found(self, client, auth_headers_docente, agente, mock_s3):
        response = client.get(
            skills_url(agente.id, "/9999"), headers=auth_headers_docente
        )
        assert response.status_code == 404
        assert response.get_json()["error"]["code"] == "SKILL_NOT_FOUND"


class TestDownloadSkill:
    def test_200_presigned_url(
        self, client, auth_headers_docente, agente, skill, mock_s3
    ):
        response = client.get(
            skills_url(agente.id, f"/{skill.id}/download"),
            headers=auth_headers_docente,
        )
        assert response.status_code == 200
        data = response.get_json()["data"]
        assert data["url"] == "https://example/presigned-url"
        assert data["expires_in"] == 900
        assert data["filename"] == "cinematica.md"


class TestCreateSkill:
    def test_201_owner_crea(self, client, auth_headers_docente, agente, mock_s3):
        response = client.post(
            skills_url(agente.id),
            headers=auth_headers_docente,
            json={"nombre": "Dinámica", "descripcion": "X", "contenido": "# md"},
        )
        assert response.status_code == 201
        data = response.get_json()["data"]
        assert data["nombre"] == "Dinámica"
        assert data["s3_key"] == f"{agente.s3_prefix}/dinamica.md"
        mock_s3.upload_file.assert_called_once()

    def test_400_sin_nombre(self, client, auth_headers_docente, agente, mock_s3):
        response = client.post(
            skills_url(agente.id),
            headers=auth_headers_docente,
            json={"descripcion": "X"},
        )
        assert response.status_code == 400
        assert response.get_json()["error"]["code"] == "VALIDATION_ERROR"

    def test_403_no_owner(
        self, client, auth_headers_otro_docente, agente, mock_s3
    ):
        response = client.post(
            skills_url(agente.id),
            headers=auth_headers_otro_docente,
            json={"nombre": "X"},
        )
        assert response.status_code == 403

    def test_401_sin_token(self, client, agente):
        response = client.post(
            skills_url(agente.id), json={"nombre": "X"}
        )
        assert response.status_code == 401

    def test_409_duplicado(
        self, client, auth_headers_docente, agente, skill, mock_s3
    ):
        response = client.post(
            skills_url(agente.id),
            headers=auth_headers_docente,
            json={"nombre": "Cinemática"},
        )
        assert response.status_code == 409
        assert response.get_json()["error"]["code"] == "DUPLICATE_SKILL_NAME"

    def test_404_agente_inexistente(
        self, client, auth_headers_docente, mock_s3
    ):
        response = client.post(
            skills_url(9999),
            headers=auth_headers_docente,
            json={"nombre": "X"},
        )
        assert response.status_code == 404
        assert response.get_json()["error"]["code"] == "AGENT_NOT_FOUND"


class TestUpdateSkill:
    def test_200_owner_actualiza(
        self, client, auth_headers_docente, agente, skill, mock_s3
    ):
        response = client.put(
            skills_url(agente.id, f"/{skill.id}"),
            headers=auth_headers_docente,
            json={"descripcion": "Nueva descripción"},
        )
        assert response.status_code == 200
        assert response.get_json()["data"]["descripcion"] == "Nueva descripción"

    def test_403_no_owner(
        self, client, auth_headers_otro_docente, agente, skill, mock_s3
    ):
        response = client.put(
            skills_url(agente.id, f"/{skill.id}"),
            headers=auth_headers_otro_docente,
            json={"descripcion": "Hack"},
        )
        assert response.status_code == 403

    def test_404_skill_inexistente(
        self, client, auth_headers_docente, agente, mock_s3
    ):
        response = client.put(
            skills_url(agente.id, "/9999"),
            headers=auth_headers_docente,
            json={"descripcion": "X"},
        )
        assert response.status_code == 404
        assert response.get_json()["error"]["code"] == "SKILL_NOT_FOUND"


class TestDeleteSkill:
    def test_204_owner_elimina(
        self, client, auth_headers_docente, agente, skill, mock_s3
    ):
        response = client.delete(
            skills_url(agente.id, f"/{skill.id}"),
            headers=auth_headers_docente,
        )
        assert response.status_code == 204
        assert response.data == b""
        mock_s3.delete_file.assert_called_once_with(skill.s3_key)

    def test_403_no_owner(
        self, client, auth_headers_otro_docente, agente, skill, mock_s3
    ):
        response = client.delete(
            skills_url(agente.id, f"/{skill.id}"),
            headers=auth_headers_otro_docente,
        )
        assert response.status_code == 403

    def test_404_skill_inexistente(
        self, client, auth_headers_docente, agente, mock_s3
    ):
        response = client.delete(
            skills_url(agente.id, "/9999"),
            headers=auth_headers_docente,
        )
        assert response.status_code == 404


class TestS3ErrorPropagation:
    def test_s3_not_found_en_detail_devuelve_404(
        self, client, auth_headers_docente, agente, skill, mock_s3
    ):
        mock_s3.download_file.side_effect = S3ServiceError(
            "S3_NOT_FOUND", "missing"
        )
        response = client.get(
            skills_url(agente.id, f"/{skill.id}"), headers=auth_headers_docente
        )
        assert response.status_code == 404
        assert response.get_json()["error"]["code"] == "S3_NOT_FOUND"

    def test_s3_generic_en_detail_devuelve_502(
        self, client, auth_headers_docente, agente, skill, mock_s3
    ):
        mock_s3.download_file.side_effect = S3ServiceError("S3_ERROR", "boom")
        response = client.get(
            skills_url(agente.id, f"/{skill.id}"), headers=auth_headers_docente
        )
        assert response.status_code == 502
        assert response.get_json()["error"]["code"] == "S3_ERROR"
