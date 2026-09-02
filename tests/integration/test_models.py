import uuid
from datetime import datetime, timezone, timedelta
import pytest
from sqlalchemy.exc import IntegrityError
from app.database import SessionLocal
from app.models.user import User, UserRole
from app.models.appointment import Appointment, AppointmentStatus


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        # Limpa os dados criados apos os testes
        session.query(Appointment).delete()
        session.query(User).delete()
        session.commit()
        session.close()


def test_create_user(db_session):
    user = User(
        name="Dr. Carlos",
        email=f"carlos_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="fake_hashed_password",
        role=UserRole.PROFESSIONAL,
    )
    db_session.add(user)
    db_session.commit()

    saved_user = db_session.query(User).filter_by(id=user.id).first()
    assert saved_user is not None
    assert saved_user.name == "Dr. Carlos"
    assert saved_user.role == UserRole.PROFESSIONAL


def test_exclusion_constraint_prevents_overlapping_appointments(db_session):
    # Cria profissional e cliente
    professional = User(
        name="Dra. Maria",
        email=f"maria_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="fake_hash",
        role=UserRole.PROFESSIONAL,
    )
    client_1 = User(
        name="Cliente João",
        email=f"joao_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="fake_hash",
        role=UserRole.CLIENT,
    )
    client_2 = User(
        name="Cliente Ana",
        email=f"ana_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="fake_hash",
        role=UserRole.CLIENT,
    )
    db_session.add_all([professional, client_1, client_2])
    db_session.commit()

    now = datetime.now(timezone.utc)
    start_1 = now + timedelta(days=1, hours=14)
    end_1 = start_1 + timedelta(hours=1)

    # 1. Primeiro agendamento (14:00 as 15:00)
    app_1 = Appointment(
        client_id=client_1.id,
        professional_id=professional.id,
        start_time=start_1,
        end_time=end_1,
        status=AppointmentStatus.SCHEDULED,
    )
    db_session.add(app_1)
    db_session.commit()

    # 2. Segundo agendamento conflitante (14:30 as 15:30) para o mesmo profissional
    start_2 = start_1 + timedelta(minutes=30)
    end_2 = start_2 + timedelta(hours=1)

    app_2 = Appointment(
        client_id=client_2.id,
        professional_id=professional.id,
        start_time=start_2,
        end_time=end_2,
        status=AppointmentStatus.SCHEDULED,
    )
    db_session.add(app_2)

    # O PostgreSQL deve disparar erro de integridade (Exclusion Constraint)
    with pytest.raises(IntegrityError):
        db_session.commit()

    db_session.rollback()


def test_canceled_appointment_allows_new_booking(db_session):
    # Cria profissional e cliente
    professional = User(
        name="Dr. Lucas",
        email=f"lucas_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="fake_hash",
        role=UserRole.PROFESSIONAL,
    )
    client_1 = User(
        name="Cliente Beatriz",
        email=f"beatriz_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="fake_hash",
        role=UserRole.CLIENT,
    )
    client_2 = User(
        name="Cliente Pedro",
        email=f"pedro_{uuid.uuid4().hex[:6]}@example.com",
        password_hash="fake_hash",
        role=UserRole.CLIENT,
    )
    db_session.add_all([professional, client_1, client_2])
    db_session.commit()

    start = datetime.now(timezone.utc) + timedelta(days=2, hours=10)
    end = start + timedelta(hours=1)

    # 1. Agendamento inicial que foi cancelado
    app_1 = Appointment(
        client_id=client_1.id,
        professional_id=professional.id,
        start_time=start,
        end_time=end,
        status=AppointmentStatus.CANCELED,
    )
    db_session.add(app_1)
    db_session.commit()

    # 2. Novo agendamento no mesmo horario deve ser aceito porque o anterior esta CANCELED
    app_2 = Appointment(
        client_id=client_2.id,
        professional_id=professional.id,
        start_time=start,
        end_time=end,
        status=AppointmentStatus.SCHEDULED,
    )
    db_session.add(app_2)
    db_session.commit()

    assert app_2.id is not None
    assert app_2.status == AppointmentStatus.SCHEDULED
