AGENTES_URL = "/api/v1/agentes"


class TestGetAgentes:
    def test_sin_token_devuelve_401(self, client):
        response = client.get(AGENTES_URL)

        assert response.status_code == 401
        assert response.get_json()["error"]["code"] == "MISSING_TOKEN"

    def test_lista_vacia_devuelve_200(self, client, auth_headers_docente):
        response = client.get(AGENTES_URL, headers=auth_headers_docente)

        assert response.status_code == 200
        assert response.get_json()["data"] == []

    def test_con_agente_devuelve_lista_con_un_elemento(
        self, client, auth_headers_docente, agente
    ):
        response = client.get(AGENTES_URL, headers=auth_headers_docente)

        assert response.status_code == 200
        data = response.get_json()["data"]
        assert len(data) == 1
        assert data[0]["id"] == agente.id
        assert data[0]["nombre"] == "Agente Física I"


class TestGetAgenteById:
    def test_token_valido_devuelve_shape_correcta(
        self, client, auth_headers_docente, agente
    ):
        response = client.get(
            f"{AGENTES_URL}/{agente.id}",
            headers=auth_headers_docente,
        )

        assert response.status_code == 200
        data = response.get_json()["data"]
        assert data["id"] == agente.id
        assert data["nombre"] == "Agente Física I"
        assert data["icono"] == "🤖"
        assert data["s3_prefix"] == "fisica-i"
        assert data["skills_count"] == 0
        assert data["materia"]["id"] == agente.materia_id
        assert data["materia"]["nombre"] == "Física I"
        assert data["materia"]["icono"] == "📚"
        assert data["docente"]["id"] == agente.docente_id
        assert data["docente"]["nombre"] == "Daniel"

    def test_id_inexistente_devuelve_404(self, client, auth_headers_docente):
        response = client.get(
            f"{AGENTES_URL}/999",
            headers=auth_headers_docente,
        )

        assert response.status_code == 404
        assert response.get_json()["error"]["code"] == "AGENT_NOT_FOUND"


class TestCreateAgente:
    def test_docente_crea_agente_valido(self, client, auth_headers_docente, materia):
        response = client.post(
            AGENTES_URL,
            headers=auth_headers_docente,
            json={"nombre": "Nuevo Agente", "materia_id": materia.id},
        )

        assert response.status_code == 201
        data = response.get_json()["data"]
        assert data["nombre"] == "Nuevo Agente"
        assert data["s3_prefix"] == "fisica-i"
        assert data["icono"] == "🤖"

    def test_estudiante_devuelve_403(self, client, auth_headers_estudiante, materia):
        response = client.post(
            AGENTES_URL,
            headers=auth_headers_estudiante,
            json={"nombre": "Hack", "materia_id": materia.id},
        )

        assert response.status_code == 403
        assert response.get_json()["error"]["code"] == "FORBIDDEN"

    def test_sin_token_devuelve_401(self, client, materia):
        response = client.post(
            AGENTES_URL,
            json={"nombre": "X", "materia_id": materia.id},
        )

        assert response.status_code == 401
        assert response.get_json()["error"]["code"] == "MISSING_TOKEN"

    def test_sin_materia_id_devuelve_400(self, client, auth_headers_docente):
        response = client.post(
            AGENTES_URL,
            headers=auth_headers_docente,
            json={"nombre": "X"},
        )

        assert response.status_code == 400
        assert response.get_json()["error"]["code"] == "VALIDATION_ERROR"

    def test_duplicado_devuelve_409(
        self, client, auth_headers_docente, agente, materia
    ):
        response = client.post(
            AGENTES_URL,
            headers=auth_headers_docente,
            json={"nombre": "Otro", "materia_id": materia.id},
        )

        assert response.status_code == 409
        assert response.get_json()["error"]["code"] == "DUPLICATE_AGENT"

    def test_materia_inexistente_devuelve_404(self, client, auth_headers_docente):
        response = client.post(
            AGENTES_URL,
            headers=auth_headers_docente,
            json={"nombre": "X", "materia_id": 999},
        )

        assert response.status_code == 404
        assert response.get_json()["error"]["code"] == "MATERIA_NOT_FOUND"


class TestUpdateAgente:
    def test_owner_actualiza(self, client, auth_headers_docente, agente):
        response = client.put(
            f"{AGENTES_URL}/{agente.id}",
            headers=auth_headers_docente,
            json={"nombre": "Nombre Nuevo"},
        )

        assert response.status_code == 200
        assert response.get_json()["data"]["nombre"] == "Nombre Nuevo"

    def test_docente_ajeno_devuelve_403(
        self, client, auth_headers_otro_docente, agente
    ):
        response = client.put(
            f"{AGENTES_URL}/{agente.id}",
            headers=auth_headers_otro_docente,
            json={"nombre": "Hack"},
        )

        assert response.status_code == 403
        assert response.get_json()["error"]["code"] == "FORBIDDEN"

    def test_sin_token_devuelve_401(self, client, agente):
        response = client.put(
            f"{AGENTES_URL}/{agente.id}",
            json={"nombre": "X"},
        )

        assert response.status_code == 401
        assert response.get_json()["error"]["code"] == "MISSING_TOKEN"

    def test_id_inexistente_devuelve_404(self, client, auth_headers_docente):
        response = client.put(
            f"{AGENTES_URL}/999",
            headers=auth_headers_docente,
            json={"nombre": "X"},
        )

        assert response.status_code == 404
        assert response.get_json()["error"]["code"] == "AGENT_NOT_FOUND"


class TestDeleteAgente:
    def test_owner_elimina_devuelve_204(self, client, auth_headers_docente, agente):
        response = client.delete(
            f"{AGENTES_URL}/{agente.id}",
            headers=auth_headers_docente,
        )

        assert response.status_code == 204
        assert response.data == b""

    def test_docente_ajeno_devuelve_403(
        self, client, auth_headers_otro_docente, agente
    ):
        response = client.delete(
            f"{AGENTES_URL}/{agente.id}",
            headers=auth_headers_otro_docente,
        )

        assert response.status_code == 403
        assert response.get_json()["error"]["code"] == "FORBIDDEN"

    def test_sin_token_devuelve_401(self, client, agente):
        response = client.delete(f"{AGENTES_URL}/{agente.id}")

        assert response.status_code == 401
        assert response.get_json()["error"]["code"] == "MISSING_TOKEN"

    def test_get_tras_delete_devuelve_404(self, client, auth_headers_docente, agente):
        delete_response = client.delete(
            f"{AGENTES_URL}/{agente.id}",
            headers=auth_headers_docente,
        )
        assert delete_response.status_code == 204

        get_response = client.get(
            f"{AGENTES_URL}/{agente.id}",
            headers=auth_headers_docente,
        )
        assert get_response.status_code == 404
        assert get_response.get_json()["error"]["code"] == "AGENT_NOT_FOUND"
