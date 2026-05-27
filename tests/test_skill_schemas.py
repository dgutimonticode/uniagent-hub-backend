import pytest
from marshmallow import ValidationError

from app.schemas.skill_schemas import (
    SkillCreateSchema,
    SkillDetailSchema,
    SkillDownloadSchema,
    SkillResponseSchema,
    SkillUpdateSchema,
)


class TestSkillCreateSchema:
    def test_nombre_required(self):
        schema = SkillCreateSchema()
        with pytest.raises(ValidationError) as exc:
            schema.load({})
        assert "nombre" in exc.value.messages

    def test_nombre_vacio_falla(self):
        schema = SkillCreateSchema()
        with pytest.raises(ValidationError):
            schema.load({"nombre": ""})

    def test_nombre_demasiado_largo_falla(self):
        schema = SkillCreateSchema()
        with pytest.raises(ValidationError):
            schema.load({"nombre": "x" * 151})

    def test_contenido_default_vacio(self):
        schema = SkillCreateSchema()
        result = schema.load({"nombre": "Skill 1"})
        assert result["contenido"] == ""

    def test_payload_completo_ok(self):
        schema = SkillCreateSchema()
        result = schema.load(
            {
                "nombre": "Cinemática",
                "descripcion": "MRU",
                "contenido": "# Markdown",
            }
        )
        assert result["nombre"] == "Cinemática"
        assert result["descripcion"] == "MRU"
        assert result["contenido"] == "# Markdown"


class TestSkillUpdateSchema:
    def test_update_parcial_ok(self):
        schema = SkillUpdateSchema()
        result = schema.load({"nombre": "Otro"})
        assert result == {"nombre": "Otro"}

    def test_update_vacio_ok(self):
        schema = SkillUpdateSchema()
        result = schema.load({})
        assert result == {}

    def test_nombre_demasiado_largo_falla(self):
        schema = SkillUpdateSchema()
        with pytest.raises(ValidationError):
            schema.load({"nombre": "x" * 151})


class TestSkillResponseSchema:
    def test_dump_contiene_campos(self):
        schema = SkillResponseSchema()
        result = schema.dump(
            type(
                "S",
                (),
                {
                    "id": 1,
                    "agente_id": 2,
                    "nombre": "X",
                    "descripcion": "Y",
                    "s3_key": "a/b.md",
                    "tamano_kb": 3,
                    "orden": 0,
                    "created_at": None,
                    "updated_at": None,
                },
            )()
        )
        assert result["id"] == 1
        assert result["agente_id"] == 2
        assert result["nombre"] == "X"
        assert result["s3_key"] == "a/b.md"


class TestSkillDetailSchema:
    def test_incluye_contenido(self):
        schema = SkillDetailSchema()
        result = schema.dump(
            type(
                "S",
                (),
                {
                    "id": 1,
                    "agente_id": 2,
                    "nombre": "X",
                    "descripcion": "Y",
                    "s3_key": "a/b.md",
                    "tamano_kb": 3,
                    "orden": 0,
                    "created_at": None,
                    "updated_at": None,
                    "contenido": "# md",
                },
            )()
        )
        assert result["contenido"] == "# md"


class TestSkillDownloadSchema:
    def test_dump_url_expires_filename(self):
        schema = SkillDownloadSchema()
        result = schema.dump(
            {"url": "https://example/x", "expires_in": 900, "filename": "x.md"}
        )
        assert result == {
            "url": "https://example/x",
            "expires_in": 900,
            "filename": "x.md",
        }
