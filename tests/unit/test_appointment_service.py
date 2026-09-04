import uuid
from datetime import date, datetime, timezone, timedelta
from unittest.mock import MagicMock
import pytest
from sqlalchemy.exc import IntegrityError

from app.api.schemas.appointment import AppointmentCreate
from app.exceptions import (
    AppException,
    AppointmentConflictError,
    ForbiddenError,
    NotFoundError,
)
from app.models.appointment import Appointment, AppointmentStatus
from app.models.user import User, UserRole
from app.services.appointment_service import AppointmentService


@pytest.fixture
def mock_db():
    return MagicMock()

#para testar se o agendamento foi criado corretamente
@pytest.fixture
def service(mock_db):
    return AppointmentService(mock_db)

#para testar se o profissional consegue agendar consigo mesmo   
def test_cannot_book_with_self(service):
    same_id = uuid.uuid4()
    data = AppointmentCreate(
        professional_id=same_id,
        start_time=datetime.now(timezone.utc) + timedelta(days=1),
        end_time=datetime.now(timezone.utc) + timedelta(days=1, hours=1),
    )

    with pytest.raises(AppException) as exc:
        service.create(client_id=same_id, data=data)

    assert "consigo mesmo" in exc.value.message

#testa se o profissional nao existe
def test_cannot_book_non_existent_professional(service):
    client_id = uuid.uuid4()
    prof_id = uuid.uuid4()

    service.user_repo.get_by_id = MagicMock(return_value=None)

    data = AppointmentCreate(
        professional_id=prof_id,
        start_time=datetime.now(timezone.utc) + timedelta(days=1),
        end_time=datetime.now(timezone.utc) + timedelta(days=1, hours=1),
    )

    with pytest.raises(NotFoundError):
        service.create(client_id=client_id, data=data)

#testa se o agendamento é no passado
def test_cannot_book_past_date(service):
    client_id = uuid.uuid4()
    prof_id = uuid.uuid4()

    prof = User(id=prof_id, name="Dr. Teste", role=UserRole.PROFESSIONAL)
    service.user_repo.get_by_id = MagicMock(return_value=prof)

    # Horario no passado
    past_start = datetime.now(timezone.utc) - timedelta(hours=2)
    past_end = datetime.now(timezone.utc) - timedelta(hours=1)

    data = AppointmentCreate(
        professional_id=prof_id,
        start_time=past_start,
        end_time=past_end,
    )

    with pytest.raises(AppException) as exc:
        service.create(client_id=client_id, data=data)

    assert "no futuro" in exc.value.message

#testa se o agendamento é conflitante
def test_create_appointment_concurrency_conflict(service):
    client_id = uuid.uuid4()
    prof_id = uuid.uuid4()

    prof = User(id=prof_id, name="Dr. Teste", role=UserRole.PROFESSIONAL)
    service.user_repo.get_by_id = MagicMock(return_value=prof)

    # Simula o banco disparando IntegrityError devido a constraint de exclusao
    service.appointment_repo.create = MagicMock(side_effect=IntegrityError("statement", {}, Exception()))

    data = AppointmentCreate(
        professional_id=prof_id,
        start_time=datetime.now(timezone.utc) + timedelta(days=1),
        end_time=datetime.now(timezone.utc) + timedelta(days=1, hours=1),
    )

    with pytest.raises(AppointmentConflictError):
        service.create(client_id=client_id, data=data)

    service.db.rollback.assert_called_once()

#testa se o agendamento é proibido para outro usuario
def test_cancel_appointment_forbidden_for_other_user(service):
    owner_client_id = uuid.uuid4()
    prof_id = uuid.uuid4()
    other_user_id = uuid.uuid4()

    app_obj = Appointment(
        id=uuid.uuid4(),
        client_id=owner_client_id,
        professional_id=prof_id,
        status=AppointmentStatus.SCHEDULED,
    )
    service.appointment_repo.get_by_id = MagicMock(return_value=app_obj)

    with pytest.raises(ForbiddenError):
        service.cancel(appointment_id=app_obj.id, user_id=other_user_id)

#testa se a disponibilidade foi da forma devida
def test_get_availability_generates_correct_slots(service):
    prof_id = uuid.uuid4()
    prof = User(id=prof_id, name="Dr. Teste", role=UserRole.PROFESSIONAL)
    service.user_repo.get_by_id = MagicMock(return_value=prof)

    target_date = date(2026, 9, 10)
    slot_start = datetime(2026, 9, 10, 10, 0, tzinfo=timezone.utc)
    slot_end = datetime(2026, 9, 10, 11, 0, tzinfo=timezone.utc)

    # Mock de um agendamento existente das 10h as 11h
    service.appointment_repo.list_active_by_professional_and_date_range = MagicMock(
        return_value=[
            Appointment(
                professional_id=prof_id,
                start_time=slot_start,
                end_time=slot_end,
                status=AppointmentStatus.SCHEDULED,
            )
        ]
    )

    slots = service.get_availability(prof_id, target_date)

    # De 08:00 as 18:00 sao 10 slots de 1 hora
    assert len(slots) == 10

    # O slot das 10h as 11h deve estar indisponivel
    slot_10h = [s for s in slots if s["start_time"] == slot_start][0]
    assert slot_10h["available"] is False

    # Os demais devem estar disponiveis
    slot_8h = [s for s in slots if s["start_time"].hour == 8][0]
    assert slot_8h["available"] is True
