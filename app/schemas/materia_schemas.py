from marshmallow import Schema, fields


class MateriaResponseSchema(Schema):
    id = fields.Int()
    nombre = fields.Str()
    carrera = fields.Str()
    semestre = fields.Int()
    icono = fields.Str()
