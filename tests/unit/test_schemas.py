import uuid
from datetime import datetime, timezone, timedelta
import pytest
from pydantic import ValidationError
from app.api.schemas.appointment import AppointmentCreate

#para validar se o agendamento foi criado corretamente
def test_appointment_create_valid():
    start = datetime.now(timezone.utc) + timedelta(hours=1)
    end = start + timedelta(hours=1)

    data = AppointmentCreate(
        professional_id=uuid.uuid4(),
        start_time=start,
        end_time=end,
        notes="Consulta de rotina",
    )

    assert data.notes == "Consulta de rotina"
    assert data.end_time > data.start_time

#para testar o erro de horario invalido
def test_appointment_create_invalid_time_range():
    start = datetime.now(timezone.utc) + timedelta(hours=2)
    end = datetime.now(timezone.utc) + timedelta(hours=1)

    with pytest.raises(ValidationError) as exc_info:
        AppointmentCreate(
            professional_id=uuid.uuid4(),
            start_time=start,
            end_time=end,
        )

    assert "O horário de término deve ser posterior ao horário de início" in str(exc_info.value)
