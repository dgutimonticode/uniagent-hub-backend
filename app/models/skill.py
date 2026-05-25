from datetime import datetime, timezone

from app.extensions import db


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Skill(db.Model):
    __tablename__ = 'skills'
    __table_args__ = (
        db.UniqueConstraint('agente_id', 'nombre', name='uk_agente_nombre'),
        db.Index('idx_agente_orden', 'agente_id', 'orden'),
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'},
    )

    id = db.Column(db.Integer, primary_key=True)
    agente_id = db.Column(
        db.Integer,
        db.ForeignKey('agentes.id', ondelete='CASCADE'),
        nullable=False
    )
    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text)
    s3_key = db.Column(db.String(500), unique=True, nullable=False)
    tamano_kb = db.Column(db.Integer, default=0)
    orden = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    def to_dict(self, include_content: bool = False) -> dict:
        return {
            'id': self.id,
            'agente_id': self.agente_id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            's3_key': self.s3_key,
            'tamano_kb': self.tamano_kb,
            'orden': self.orden,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
