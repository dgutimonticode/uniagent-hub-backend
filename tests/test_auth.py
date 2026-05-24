from datetime import timedelta

from flask_jwt_extended import create_access_token

from app.extensions import db as _db

LOGIN_URL = "/api/v1/auth/login"
ME_URL = "/api/v1/auth/me"


class TestLogin:
    def test_credenciales_validas_devuelve_token(self, client, docente_user):
        response = client.post(
            LOGIN_URL,
            json={"email": "daniel@usfx.bo", "password": "test1234"},
        )

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["data"]["token"]
        assert payload["data"]["user"]["email"] == "daniel@usfx.bo"
        assert payload["data"]["user"]["rol"] == "docente"

    def test_password_incorrecto_devuelve_401(self, client, docente_user):
        response = client.post(
            LOGIN_URL,
            json={"email": "daniel@usfx.bo", "password": "wrong-password"},
        )

        assert response.status_code == 401
        assert response.get_json()["error"]["code"] == "INVALID_CREDENTIALS"

    def test_email_inexistente_devuelve_401(self, client):
        response = client.post(
            LOGIN_URL,
            json={"email": "noexiste@usfx.bo", "password": "test1234"},
        )

        assert response.status_code == 401
        assert response.get_json()["error"]["code"] == "INVALID_CREDENTIALS"

    def test_body_vacio_devuelve_400(self, client):
        response = client.post(LOGIN_URL, json={})

        assert response.status_code == 400
        assert response.get_json()["error"]["code"] == "VALIDATION_ERROR"

    def test_sin_campo_password_devuelve_400(self, client):
        response = client.post(LOGIN_URL, json={"email": "daniel@usfx.bo"})

        assert response.status_code == 400
        assert response.get_json()["error"]["code"] == "VALIDATION_ERROR"

    def test_actualiza_last_login_at(self, client, docente_user):
        assert docente_user.last_login_at is None

        response = client.post(
            LOGIN_URL,
            json={"email": "daniel@usfx.bo", "password": "test1234"},
        )
        assert response.status_code == 200

        _db.session.refresh(docente_user)
        assert docente_user.last_login_at is not None


class TestMe:
    def test_token_valido_devuelve_usuario(self, client, auth_headers_docente):
        response = client.get(ME_URL, headers=auth_headers_docente)

        assert response.status_code == 200
        payload = response.get_json()
        assert payload["data"]["email"] == "daniel@usfx.bo"
        assert payload["data"]["rol"] == "docente"

    def test_sin_authorization_header_devuelve_401(self, client):
        response = client.get(ME_URL)

        assert response.status_code == 401
        assert response.get_json()["error"]["code"] == "MISSING_TOKEN"

    def test_token_corrupto_devuelve_401(self, client):
        response = client.get(
            ME_URL,
            headers={"Authorization": "Bearer abc.def.ghi"},
        )

        assert response.status_code == 401
        assert response.get_json()["error"]["code"] == "INVALID_TOKEN"

    def test_token_expirado_devuelve_401(self, app, client, docente_user):
        with app.app_context():
            expired_token = create_access_token(
                identity=str(docente_user.id),
                expires_delta=timedelta(seconds=-1),
            )

        response = client.get(
            ME_URL,
            headers={"Authorization": f"Bearer {expired_token}"},
        )

        assert response.status_code == 401
        assert response.get_json()["error"]["code"] == "INVALID_TOKEN"
