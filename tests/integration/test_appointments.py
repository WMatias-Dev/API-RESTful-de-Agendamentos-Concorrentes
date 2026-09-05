import uuid
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.appointment import Appointment
from app.models.user import User

client = TestClient(app)


# Fixture para limpar o banco de dados antes e depois de cada teste
@pytest.fixture(autouse=True)
def clean_database():
    session = SessionLocal()
    session.query(Appointment).delete()
    session.query(User).delete()
    session.commit()
    yield
    session.query(Appointment).delete()
    session.query(User).delete()
    session.commit()
    session.close()


# Funcao auxiliar para cadastrar um usuario e retornar seus dados e token de acesso
def create_user_and_token(role: str = "CLIENT") -> tuple[dict, str]:
    email = f"user_{uuid.uuid4().hex[:6]}@example.com"
    password = "senha_segura_123"

    res = client.post(
        "/api/v1/auth/register",
        json={"name": "Usuario Teste", "email": email, "password": password, "role": role},
    )
    user_data = res.json()

    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = login_res.json()["access_token"]
    return user_data, token


# Testa a criacao de um agendamento com sucesso
def test_create_appointment_success():
    prof, _ = create_user_and_token(role="PROFESSIONAL")
    client_user, client_token = create_user_and_token(role="CLIENT")

    start = datetime.now(timezone.utc) + timedelta(days=1, hours=10)
    end = start + timedelta(hours=1)

    payload = {
        "professional_id": prof["id"],
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
        "notes": "Primeira consulta médica",
    }

    headers = {"Authorization": f"Bearer {client_token}"}
    response = client.post("/api/v1/appointments", json=payload, headers=headers)

    assert response.status_code == 201
    data = response.json()
    assert data["professional_id"] == prof["id"]
    assert data["client_id"] == client_user["id"]
    assert data["status"] == "SCHEDULED"
    assert data["notes"] == "Primeira consulta médica"
    assert "id" in data


# Testa a prevencao de conflito de horario (double-booking) retornando 409
def test_create_appointment_conflict_returns_409():
    prof, _ = create_user_and_token(role="PROFESSIONAL")
    _, client1_token = create_user_and_token(role="CLIENT")
    _, client2_token = create_user_and_token(role="CLIENT")

    start = datetime.now(timezone.utc) + timedelta(days=1, hours=14)
    end = start + timedelta(hours=1)

    payload = {
        "professional_id": prof["id"],
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
    }

    # Primeiro cliente reserva o horario
    res1 = client.post(
        "/api/v1/appointments",
        json=payload,
        headers={"Authorization": f"Bearer {client1_token}"},
    )
    assert res1.status_code == 201

    # Segundo cliente tenta reservar no mesmo intervalo para o mesmo profissional
    res2 = client.post(
        "/api/v1/appointments",
        json=payload,
        headers={"Authorization": f"Bearer {client2_token}"},
    )
    assert res2.status_code == 409
    assert res2.json()["detail"] == "O horário solicitado não está disponível."


# Testa a listagem de agendamentos do usuario logado
def test_list_appointments():
    prof, _ = create_user_and_token(role="PROFESSIONAL")
    _, client_token = create_user_and_token(role="CLIENT")

    start = datetime.now(timezone.utc) + timedelta(days=2, hours=9)
    end = start + timedelta(hours=1)

    payload = {
        "professional_id": prof["id"],
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
    }

    headers = {"Authorization": f"Bearer {client_token}"}
    client.post("/api/v1/appointments", json=payload, headers=headers)

    response = client.get("/api/v1/appointments", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["professional_id"] == prof["id"]


# Testa a consulta detalhada de agendamento por ID e controle de acesso
def test_get_appointment_by_id_and_permissions():
    prof, _ = create_user_and_token(role="PROFESSIONAL")
    client_user, client_token = create_user_and_token(role="CLIENT")
    _, other_token = create_user_and_token(role="CLIENT")

    start = datetime.now(timezone.utc) + timedelta(days=3, hours=11)
    end = start + timedelta(hours=1)

    payload = {
        "professional_id": prof["id"],
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
    }

    headers = {"Authorization": f"Bearer {client_token}"}
    create_res = client.post("/api/v1/appointments", json=payload, headers=headers)
    appointment_id = create_res.json()["id"]

    # 1. Cliente dono do agendamento consegue visualizar
    res1 = client.get(f"/api/v1/appointments/{appointment_id}", headers=headers)
    assert res1.status_code == 200
    assert res1.json()["id"] == appointment_id

    # 2. Outro usuario que nao participa do agendamento recebe 403
    res2 = client.get(
        f"/api/v1/appointments/{appointment_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert res2.status_code == 403


# Testa o cancelamento de um agendamento e a posterior liberacao do horario
def test_cancel_appointment_and_rebook():
    prof, _ = create_user_and_token(role="PROFESSIONAL")
    _, client1_token = create_user_and_token(role="CLIENT")
    _, client2_token = create_user_and_token(role="CLIENT")

    start = datetime.now(timezone.utc) + timedelta(days=4, hours=15)
    end = start + timedelta(hours=1)

    payload = {
        "professional_id": prof["id"],
        "start_time": start.isoformat(),
        "end_time": end.isoformat(),
    }

    # 1. Cliente 1 faz o agendamento
    res1 = client.post(
        "/api/v1/appointments",
        json=payload,
        headers={"Authorization": f"Bearer {client1_token}"},
    )
    appointment_id = res1.json()["id"]

    # 2. Cliente 1 cancela o agendamento
    cancel_res = client.delete(
        f"/api/v1/appointments/{appointment_id}",
        headers={"Authorization": f"Bearer {client1_token}"},
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELED"

    # 3. Tentar cancelar novamente gera erro 400
    cancel_again = client.delete(
        f"/api/v1/appointments/{appointment_id}",
        headers={"Authorization": f"Bearer {client1_token}"},
    )
    assert cancel_again.status_code == 400

    # 4. Agora o Cliente 2 consegue agendar exatamente no mesmo horario sem conflito
    res2 = client.post(
        "/api/v1/appointments",
        json=payload,
        headers={"Authorization": f"Bearer {client2_token}"},
    )
    assert res2.status_code == 201
    assert res2.json()["status"] == "SCHEDULED"


# Testa a consulta de disponibilidade de um profissional por data
def test_get_professional_availability():
    prof, _ = create_user_and_token(role="PROFESSIONAL")
    _, client_token = create_user_and_token(role="CLIENT")

    # Data daqui a 5 dias
    target_date = (datetime.now(timezone.utc) + timedelta(days=5)).date()
    target_date_str = target_date.isoformat()

    start = datetime(target_date.year, target_date.month, target_date.day, 10, 0, tzinfo=timezone.utc)
    end = start + timedelta(hours=1)

    # Cria agendamento das 10h as 11h
    client.post(
        "/api/v1/appointments",
        json={
            "professional_id": prof["id"],
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        },
        headers={"Authorization": f"Bearer {client_token}"},
    )

    # Consulta a rota de disponibilidade
    response = client.get(f"/api/v1/availability/{prof['id']}?date={target_date_str}")
    assert response.status_code == 200
    slots = response.json()

    # O expediente das 08h as 18h tem 10 slots de 1 hora
    assert len(slots) == 10

    # O slot das 10h deve estar ocupado (available = False)
    slot_10h = [s for s in slots if "10:00:00" in s["start_time"]][0]
    assert slot_10h["available"] is False

    # Outro slot (ex: 08h) deve estar disponivel (available = True)
    slot_8h = [s for s in slots if "08:00:00" in s["start_time"]][0]
    assert slot_8h["available"] is True
