from datetime import datetime, timezone

from app.extensions import db


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Agente(db.Model):
    __tablename__ = 'agentes'
    __table_args__ = (
        db.UniqueConstraint('materia_id', 'docente_id', name='uk_materia_docente'),
        db.Index('idx_materia', 'materia_id'),
        db.Index('idx_docente', 'docente_id'),
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'},
    )

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    icono = db.Column(db.String(10), default='🤖')
    materia_id = db.Column(db.Integer, db.ForeignKey('materias.id'), nullable=False)
    docente_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    s3_prefix = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    materia = db.relationship('Materia', backref='agentes')
    skills = db.relationship('Skill', backref='agente', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self, include_skills: bool = False) -> dict:
        data = {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'icono': self.icono,
            'materia_id': self.materia_id,
            'docente_id': self.docente_id,
            's3_prefix': self.s3_prefix,
            'skills_count': self.skills.count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_skills:
            data['skills'] = [s.to_dict() for s in self.skills]
        return data
