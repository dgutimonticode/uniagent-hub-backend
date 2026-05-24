import pytest

from app import create_app
from app.extensions import db as _db
from app.models.usuario import Usuario


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def docente_user(app):
    user = Usuario(
        nombre="Daniel",
        email="daniel@usfx.bo",
        rol=Usuario.ROL_DOCENTE,
    )
    user.set_password("test1234")
    _db.session.add(user)
    _db.session.commit()
    return user


@pytest.fixture
def estudiante_user(app):
    user = Usuario(
        nombre="Alumno",
        email="alumno@usfx.bo",
        rol=Usuario.ROL_ESTUDIANTE,
    )
    user.set_password("test1234")
    _db.session.add(user)
    _db.session.commit()
    return user


@pytest.fixture
def docente_token(client, docente_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "daniel@usfx.bo", "password": "test1234"},
    )
    return response.get_json()["data"]["token"]


@pytest.fixture
def auth_headers_docente(docente_token):
    return {"Authorization": f"Bearer {docente_token}"}


@pytest.fixture
def otro_docente_user(app):
    user = Usuario(
        nombre="Otro Docente",
        email="otro@usfx.bo",
        rol=Usuario.ROL_DOCENTE,
    )
    user.set_password("test1234")
    _db.session.add(user)
    _db.session.commit()
    return user


@pytest.fixture
def auth_headers_otro_docente(client, otro_docente_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "otro@usfx.bo", "password": "test1234"},
    )
    token = response.get_json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_estudiante(client, estudiante_user):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "alumno@usfx.bo", "password": "test1234"},
    )
    token = response.get_json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}
