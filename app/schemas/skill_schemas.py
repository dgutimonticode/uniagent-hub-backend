from marshmallow import Schema, fields, validate


class SkillCreateSchema(Schema):
    nombre = fields.Str(required=True, validate=validate.Length(min=1, max=150))
    descripcion = fields.Str(load_default=None)
    contenido = fields.Str(load_default="")


class SkillUpdateSchema(Schema):
    nombre = fields.Str(validate=validate.Length(min=1, max=150))
    descripcion = fields.Str()
    contenido = fields.Str()


class SkillResponseSchema(Schema):
    id = fields.Int()
    agente_id = fields.Int()
    nombre = fields.Str()
    descripcion = fields.Str()
    s3_key = fields.Str()
    tamano_kb = fields.Int()
    orden = fields.Int()
    created_at = fields.DateTime(format="iso")
    updated_at = fields.DateTime(format="iso")


class SkillDetailSchema(SkillResponseSchema):
    contenido = fields.Str()


class SkillDownloadSchema(Schema):
    url = fields.Str()
    expires_in = fields.Int()
    filename = fields.Str()
