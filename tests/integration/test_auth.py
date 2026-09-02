import uuid
import pytest
from fastapi.testclient import TestClient
from app.database import SessionLocal
from app.main import app
from app.models.appointment import Appointment
from app.models.user import User

client = TestClient(app)

#para limpar o banco de dados antes e depois de cada teste
@pytest.fixture(autouse=True)
def clean_database():
    # Limpa as tabelas antes e depois de cada teste de integracao
    session = SessionLocal()
    session.query(Appointment).delete()
    session.query(User).delete()
    session.commit()
    yield
    session.query(Appointment).delete()
    session.query(User).delete()
    session.commit()
    session.close()

#testa o cadastro de usuario
def test_register_user_success():
    payload = {
        "name": "Maria Silva",
        "email": f"maria_{uuid.uuid4().hex[:6]}@example.com",
        "password": "senha_segura_123",
        "role": "CLIENT",
    }
    response = client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["email"] == payload["email"]
    assert data["role"] == "CLIENT"
    assert "id" in data
    assert "password" not in data
    assert "password_hash" not in data

#testa o cadastro de usuario com email duplicado
def test_register_user_duplicate_email():
    email = f"duplicado_{uuid.uuid4().hex[:6]}@example.com"
    payload = {
        "name": "Primeiro Usuario",
        "email": email,
        "password": "senha_segura_123",
        "role": "CLIENT",
    }
    # Primeiro cadastro tem que ser 201
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Segundo cadastro com o mesmo e-mail deve retornar 409
    res2 = client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 409
    assert res2.json()["detail"] == "Email já cadastrado."

#testa o login de usuario
def test_login_success():
    email = f"login_{uuid.uuid4().hex[:6]}@example.com"
    password = "senha_correta_123"

    # Cadastra o usuario
    client.post(
        "/api/v1/auth/register",
        json={"name": "Usuario Teste", "email": email, "password": password, "role": "CLIENT"},
    )

    # Realiza o login
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

#testa o login de usuario com senha invalida
def test_login_invalid_password():
    email = f"login_invalido_{uuid.uuid4().hex[:6]}@example.com"

    client.post(
        "/api/v1/auth/register",
        json={"name": "Usuario Teste", "email": email, "password": "senha_correta", "role": "CLIENT"},
    )

    # Tenta login com senha errada
    response = client.post("/api/v1/auth/login", json={"email": email, "password": "senha_errada"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Email ou senha incorretos."

#testa o auth/me autenticado
def test_get_current_user_me_authenticated():
    email = f"me_{uuid.uuid4().hex[:6]}@example.com"
    password = "minha_senha_123"

    # 1. Cadastra
    client.post(
        "/api/v1/auth/register",
        json={"name": "Ana Paula", "email": email, "password": password, "role": "PROFESSIONAL"},
    )

    # 2. Faz login para obter o token
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = login_res.json()["access_token"]

    # 3. Acessa a rota /me enviando o Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/auth/me", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email
    assert data["name"] == "Ana Paula"
    assert data["role"] == "PROFESSIONAL"

#testa o auth/me não autenticado
def test_get_current_user_me_unauthorized():
    # Sem header de autenticacao
    res1 = client.get("/api/v1/auth/me")
    assert res1.status_code == 401

    # Com token falso/invalido
    headers = {"Authorization": "Bearer token_falso_invalido"}
    res2 = client.get("/api/v1/auth/me", headers=headers)
    assert res2.status_code == 401
