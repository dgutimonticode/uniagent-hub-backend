import pytest

from app.extensions import db as _db
from app.models import Agente, Materia, Skill, Usuario


@pytest.fixture
def materia(app):
    with app.app_context():
        m = Materia(nombre='Física I', carrera='Ingeniería', semestre=1)
        _db.session.add(m)
        _db.session.commit()
        yield m


@pytest.fixture
def docente(app, materia):
    with app.app_context():
        u = Usuario(nombre='Doc Test', email='doc@test.com', rol=Usuario.ROL_DOCENTE)
        u.set_password('secret123')
        _db.session.add(u)
        _db.session.commit()
        yield u


@pytest.fixture
def agente(app, materia, docente):
    with app.app_context():
        a = Agente(
            nombre='Agente Física',
            materia_id=materia.id,
            docente_id=docente.id,
            s3_prefix='fisica-i',
        )
        _db.session.add(a)
        _db.session.commit()
        yield a


class TestUsuario:
    def test_check_password_correcto(self, app, docente):
        with app.app_context():
            u = _db.session.get(Usuario, docente.id)
            assert u.check_password('secret123') is True

    def test_check_password_incorrecto(self, app, docente):
        with app.app_context():
            u = _db.session.get(Usuario, docente.id)
            assert u.check_password('wrong') is False

    def test_to_dict_no_expone_password_hash(self, app, docente):
        with app.app_context():
            u = _db.session.get(Usuario, docente.id)
            assert 'password_hash' not in u.to_dict()

    def test_to_dict_campos_esperados(self, app, docente):
        with app.app_context():
            u = _db.session.get(Usuario, docente.id)
            data = u.to_dict()
            for key in ('id', 'nombre', 'email', 'rol', 'materia', 'avatar_url', 'created_at'):
                assert key in data


class TestMateria:
    def test_to_dict_campos_correctos(self, app, materia):
        with app.app_context():
            m = _db.session.get(Materia, materia.id)
            data = m.to_dict()
            assert data['nombre'] == 'Física I'
            assert data['carrera'] == 'Ingeniería'
            assert data['semestre'] == 1
            assert 'id' in data
            assert 'created_at' in data


class TestAgente:
    def test_skills_count_cero_sin_skills(self, app, agente):
        with app.app_context():
            a = _db.session.get(Agente, agente.id)
            assert a.to_dict()['skills_count'] == 0

    def test_to_dict_sin_skills_no_incluye_key(self, app, agente):
        with app.app_context():
            a = _db.session.get(Agente, agente.id)
            assert 'skills' not in a.to_dict()

    def test_to_dict_include_skills_true(self, app, agente):
        with app.app_context():
            a = _db.session.get(Agente, agente.id)
            data = a.to_dict(include_skills=True)
            assert 'skills' in data
            assert data['skills'] == []


class TestSkill:
    def test_to_dict_campos_correctos(self, app, agente):
        with app.app_context():
            a = _db.session.get(Agente, agente.id)
            s = Skill(
                agente_id=a.id,
                nombre='Termodinámica',
                s3_key='fisica-i/termodinamica.md',
                orden=1,
            )
            _db.session.add(s)
            _db.session.commit()
            data = s.to_dict()
            assert data['nombre'] == 'Termodinámica'
            assert data['agente_id'] == a.id
            assert data['orden'] == 1
            assert 'created_at' in data
