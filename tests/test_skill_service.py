from unittest.mock import MagicMock

import pytest

from app.extensions import db
from app.models.skill import Skill
from app.services import skill_service
from app.services.exceptions import S3ServiceError, SkillServiceError


@pytest.fixture
def mock_s3(monkeypatch):
    mock = MagicMock()
    mock.upload_file.return_value = None
    mock.download_file.return_value = b"# md"
    mock.delete_file.return_value = None
    mock.generate_presigned_url.return_value = "https://example/presigned"
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


class TestGetByAgente:
    def test_lista_vacia(self, app, agente):
        assert skill_service.get_by_agente(agente.id) == []

    def test_con_skills(self, app, agente, skill):
        result = skill_service.get_by_agente(agente.id)
        assert len(result) == 1


class TestGetById:
    def test_existente(self, app, skill):
        result = skill_service.get_by_id(skill.id)
        assert result.id == skill.id

    def test_inexistente_404(self, app):
        with pytest.raises(SkillServiceError) as exc:
            skill_service.get_by_id(9999)
        assert exc.value.code == "SKILL_NOT_FOUND"
        assert exc.value.status == 404


class TestGetContent:
    def test_lee_de_s3_y_decodea(self, app, skill, mock_s3):
        mock_s3.download_file.return_value = "# Cinemática\n".encode("utf-8")
        result = skill_service.get_content(skill.id)
        assert result == "# Cinemática\n"
        mock_s3.download_file.assert_called_once_with(skill.s3_key)


class TestCreate:
    def test_happy_path(self, app, agente, mock_s3):
        result = skill_service.create(
            agente,
            {"nombre": "Dinámica", "descripcion": "X", "contenido": "# md"},
        )
        assert result.id is not None
        assert result.nombre == "Dinámica"
        assert result.s3_key == f"{agente.s3_prefix}/dinamica.md"
        mock_s3.upload_file.assert_called_once()
        args, kwargs = mock_s3.upload_file.call_args
        # 2do arg = s3_key
        called_key = args[1] if len(args) > 1 else kwargs.get("s3_key")
        assert called_key == f"{agente.s3_prefix}/dinamica.md"

    def test_contenido_vacio_sube_bytes_vacios(self, app, agente, mock_s3):
        result = skill_service.create(
            agente, {"nombre": "Vacio", "descripcion": None, "contenido": ""}
        )
        assert result.tamano_kb == 0
        mock_s3.upload_file.assert_called_once()

    def test_duplicado_devuelve_409(self, app, agente, skill, mock_s3):
        with pytest.raises(SkillServiceError) as exc:
            skill_service.create(
                agente,
                {"nombre": "Cinemática", "descripcion": None, "contenido": ""},
            )
        assert exc.value.code == "DUPLICATE_SKILL_NAME"
        assert exc.value.status == 409
        mock_s3.upload_file.assert_not_called()

    def test_rollback_s3_si_db_falla(self, app, agente, mock_s3, monkeypatch):
        from app.repositories import skill_repository

        def boom(_data):
            raise RuntimeError("db down")

        monkeypatch.setattr(skill_repository, "create", boom)

        with pytest.raises(RuntimeError):
            skill_service.create(
                agente, {"nombre": "NuevaX", "descripcion": None, "contenido": "x"}
            )
        mock_s3.upload_file.assert_called_once()
        mock_s3.delete_file.assert_called_once_with(f"{agente.s3_prefix}/nuevax.md")


class TestUpdate:
    def test_solo_descripcion(self, app, skill, mock_s3):
        result = skill_service.update(skill, {"descripcion": "Nueva"})
        assert result.descripcion == "Nueva"
        mock_s3.upload_file.assert_not_called()
        mock_s3.delete_file.assert_not_called()

    def test_solo_contenido_sobrescribe_misma_key(self, app, skill, mock_s3):
        old_key = skill.s3_key
        result = skill_service.update(skill, {"contenido": "# nuevo"})
        assert result.s3_key == old_key
        mock_s3.upload_file.assert_called_once()
        args, kwargs = mock_s3.upload_file.call_args
        called_key = args[1] if len(args) > 1 else kwargs.get("s3_key")
        assert called_key == old_key
        mock_s3.delete_file.assert_not_called()

    def test_cambio_de_nombre_mueve_archivo(self, app, agente, skill, mock_s3):
        old_key = skill.s3_key
        mock_s3.download_file.return_value = b"# original"
        result = skill_service.update(skill, {"nombre": "Dinámica"})
        assert result.s3_key == f"{agente.s3_prefix}/dinamica.md"
        assert result.s3_key != old_key
        mock_s3.upload_file.assert_called_once()
        mock_s3.delete_file.assert_called_once_with(old_key)

    def test_cambio_nombre_duplicado_falla(self, app, agente, skill, mock_s3):
        otra = Skill(
            agente_id=agente.id,
            nombre="Dinámica",
            s3_key=f"{agente.s3_prefix}/dinamica.md",
            tamano_kb=1,
            orden=1,
        )
        db.session.add(otra)
        db.session.commit()

        with pytest.raises(SkillServiceError) as exc:
            skill_service.update(skill, {"nombre": "Dinámica"})
        assert exc.value.code == "DUPLICATE_SKILL_NAME"


class TestDelete:
    def test_borra_s3_y_db(self, app, skill, mock_s3):
        skill_id = skill.id
        s3_key = skill.s3_key
        skill_service.delete(skill)
        mock_s3.delete_file.assert_called_once_with(s3_key)

        from app.repositories import skill_repository
        assert skill_repository.find_by_id(skill_id) is None

    def test_idempotente_si_s3_not_found(self, app, skill, mock_s3):
        mock_s3.delete_file.side_effect = S3ServiceError(
            "S3_NOT_FOUND", "missing"
        )
        skill_id = skill.id
        # no debe propagar
        skill_service.delete(skill)
        from app.repositories import skill_repository
        assert skill_repository.find_by_id(skill_id) is None

    def test_otros_errores_s3_se_propagan(self, app, skill, mock_s3):
        mock_s3.delete_file.side_effect = S3ServiceError("S3_ERROR", "boom")
        with pytest.raises(S3ServiceError):
            skill_service.delete(skill)


class TestGetPresignedUrl:
    def test_retorna_dict_url_expires_filename(self, app, skill, mock_s3):
        result = skill_service.get_presigned_url(skill.id, expiration=900)
        assert result["url"] == "https://example/presigned"
        assert result["expires_in"] == 900
        assert result["filename"] == "cinematica.md"
        mock_s3.generate_presigned_url.assert_called_once_with(
            skill.s3_key, expiration=900
        )
