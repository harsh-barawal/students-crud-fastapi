import httpx

from app import ai_service

STUDENT = {
    "name": "Aarav Sharma",
    "date_of_birth": "2004-08-15",
    "email": "aarav@example.com",
    "phone": "+919876543210",
    "course": "Python Backend",
}


def add_student(client, **changes):
    return client.post("/students", json={**STUDENT, **changes})


def test_create_and_get(client):
    response = add_student(client)
    assert response.status_code == 201
    student_id = response.json()["student_id"]

    response = client.get(f"/students/{student_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Aarav Sharma"


def test_validation(client):
    assert add_student(client, name="A").status_code == 422
    assert add_student(client, name="Aarav123").status_code == 422
    assert add_student(client, date_of_birth="2999-01-01").status_code == 422
    assert add_student(client, email="wrong-email").status_code == 422
    assert add_student(client, phone="123").status_code == 422
    assert add_student(client, email=None, phone=None).status_code == 422


def test_duplicate_email(client):
    add_student(client)
    response = add_student(client, phone="+919000000001")
    assert response.status_code == 409


def test_student_not_found(client):
    assert client.get("/students/EWB20269999").status_code == 404
    assert client.patch("/students/EWB20269999", json={"course": "X"}).status_code == 404
    assert client.delete("/students/EWB20269999").status_code == 404


def test_update(client):
    student_id = add_student(client).json()["student_id"]

    response = client.patch(f"/students/{student_id}", json={"course": "Data Science"})
    assert response.status_code == 200
    assert response.json()["course"] == "Data Science"
    assert response.json()["name"] == "Aarav Sharma"

    assert client.patch(f"/students/{student_id}", json={}).status_code == 422


def test_delete(client):
    student_id = add_student(client).json()["student_id"]
    assert client.delete(f"/students/{student_id}").status_code == 204
    assert client.get(f"/students/{student_id}").status_code == 404


def test_search_filter_and_pagination(client):
    add_student(client)
    add_student(client, name="Diya Verma", email="diya@example.com",
                phone="+919000000002", date_of_birth="2006-05-20", course="Web Development")
    add_student(client, name="Kabir Singh", email="kabir@example.com",
                phone="+919000000003", date_of_birth="2007-09-02")

    assert client.get("/students").json()["total"] == 3
    assert client.get("/students?search=diya").json()["total"] == 1
    assert client.get("/students?course=web development").json()["total"] == 1
    assert client.get("/students?born_after=2006-01-01").json()["total"] == 2

    page = client.get("/students?limit=2&page=2").json()
    assert len(page["students"]) == 1


def test_ai_answers_from_database_when_ollama_is_off(client, monkeypatch):
    add_student(client)
    add_student(client, name="Diya Verma", email="diya@example.com",
                phone="+919000000002", date_of_birth="2006-05-20")

    def ollama_off(question, context):
        raise httpx.ConnectError("not running")

    monkeypatch.setattr(ai_service, "ask_ollama", ollama_off)

    data = client.post("/ai/ask", json={"question": "How many students are there?"}).json()
    assert data["source"] == "database"
    assert "2" in data["answer"]

    data = client.post("/ai/ask", json={"question": "List students born after 2005"}).json()
    assert data["records_used"] == 1


def test_ai_sends_only_safe_fields_to_model(client, monkeypatch):
    add_student(client)
    received = {}

    def fake_ollama(question, context):
        received["context"] = str(context)
        return "ok"

    monkeypatch.setattr(ai_service, "ask_ollama", fake_ollama)
    client.post("/ai/ask", json={"question": "List all students"})

    assert "Aarav Sharma" in received["context"]
    assert "aarav@example.com" not in received["context"]
    assert "+919876543210" not in received["context"]
