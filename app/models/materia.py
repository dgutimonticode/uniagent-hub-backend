from datetime import datetime, timezone

from app.extensions import db


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Materia(db.Model):
    __tablename__ = 'materias'
    __table_args__ = (
        db.UniqueConstraint('nombre', 'carrera', name='uk_materia_carrera'),
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'},
    )

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    carrera = db.Column(db.String(100))
    semestre = db.Column(db.Integer)
    icono = db.Column(db.String(10), default='📚')
    created_at = db.Column(db.DateTime, default=_utcnow)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'nombre': self.nombre,
            'carrera': self.carrera,
            'semestre': self.semestre,
            'icono': self.icono,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
