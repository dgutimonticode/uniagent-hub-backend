from app.extensions import db
from app.models.materia import Materia


def test_list_materias_publico_lista_vacia(client):
    response = client.get("/api/v1/materias")

    assert response.status_code == 200
    body = response.get_json()
    assert body["data"] == []


def test_list_materias_publico_con_seed(client, app):
    with app.app_context():
        materias = [
            Materia(nombre="Física I", carrera="Ingeniería en Sistemas", semestre=1, icono="⚛️"),
            Materia(nombre="Cálculo I", carrera="Ingeniería en Sistemas", semestre=1, icono="📐"),
            Materia(nombre="Física II", carrera="Ingeniería en Sistemas", semestre=2, icono="🌊"),
            Materia(
                nombre="Infraestructura, Plataformas Tecnológicas y Redes",
                carrera="Ingeniería en Sistemas",
                semestre=6,
                icono="☁️",
            ),
        ]
        db.session.add_all(materias)
        db.session.commit()

    response = client.get("/api/v1/materias")

    assert response.status_code == 200
    body = response.get_json()
    assert len(body["data"]) == 4
    first = body["data"][0]
    assert set(first.keys()) == {"id", "nombre", "carrera", "semestre", "icono"}


def test_get_materia_por_id_existente(client, materia):
    response = client.get(f"/api/v1/materias/{materia.id}")

    assert response.status_code == 200
    body = response.get_json()
    assert body["data"]["id"] == materia.id
    assert body["data"]["nombre"] == "Física I"
    assert body["data"]["carrera"] == "Ingeniería"
    assert body["data"]["semestre"] == 1


def test_get_materia_por_id_inexistente(client):
    response = client.get("/api/v1/materias/99999")

    assert response.status_code == 404
    body = response.get_json()
    assert body["error"]["code"] == "MATERIA_NOT_FOUND"


def test_list_materias_no_requiere_auth(client):
    response = client.get("/api/v1/materias")

    assert response.status_code == 200
    assert "Authorization" not in response.headers
