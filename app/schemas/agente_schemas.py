from marshmallow import Schema, fields, validate


class MateriaBriefSchema(Schema):
    id = fields.Int()
    nombre = fields.Str()
    icono = fields.Str()


class DocenteBriefSchema(Schema):
    id = fields.Int()
    nombre = fields.Str()


class AgenteCreateSchema(Schema):
    nombre = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    descripcion = fields.Str(load_default=None)
    icono = fields.Str(load_default="🤖", validate=validate.Length(max=10))
    materia_id = fields.Int(required=True)


class AgenteUpdateSchema(Schema):
    nombre = fields.Str(validate=validate.Length(min=1, max=100))
    descripcion = fields.Str()
    icono = fields.Str(validate=validate.Length(max=10))


class AgenteResponseSchema(Schema):
    id = fields.Int()
    nombre = fields.Str()
    descripcion = fields.Str()
    icono = fields.Str()
    s3_prefix = fields.Str()
    materia = fields.Nested(MateriaBriefSchema)
    docente = fields.Nested(DocenteBriefSchema)
    skills_count = fields.Method("get_skills_count")
    created_at = fields.DateTime(format="iso")
    updated_at = fields.DateTime(format="iso")

    def get_skills_count(self, agente) -> int:
        return agente.skills.count()
