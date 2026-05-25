from datetime import datetime, timezone

import bcrypt

from app.extensions import db


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Usuario(db.Model):
    __tablename__ = 'usuarios'
    __table_args__ = (
        db.Index('idx_email', 'email'),
        db.Index('idx_rol', 'rol'),
        {'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_ci'},
    )

    ROL_DOCENTE = 'docente'
    ROL_ESTUDIANTE = 'estudiante'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.Enum('docente', 'estudiante'), nullable=False)
    materia_id = db.Column(db.Integer, db.ForeignKey('materias.id', ondelete='SET NULL'))
    avatar_url = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=_utcnow)
    last_login_at = db.Column(db.DateTime)

    materia = db.relationship('Materia', backref='docentes')
    agentes = db.relationship('Agente', backref='docente', lazy='dynamic')

    def set_password(self, password: str) -> None:
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'nombre': self.nombre,
            'email': self.email,
            'rol': self.rol,
            'materia': self.materia.to_dict() if self.materia else None,
            'avatar_url': self.avatar_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
        }
