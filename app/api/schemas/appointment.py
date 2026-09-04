import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, model_validator
from app.models.appointment import AppointmentStatus


# Schema para criacao de agendamento
class AppointmentCreate(BaseModel):
    professional_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    notes: str | None = Field(default=None, max_length=500)

    # Valida se o horario de termino e posterior ao de inicio
    @model_validator(mode="after")
    def validate_time_range(self):
        if self.end_time <= self.start_time:
            raise ValueError("O horário de término deve ser posterior ao horário de início.")
        return self


# Schema de retorno com os dados do agendamento
class AppointmentResponse(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    professional_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    status: AppointmentStatus
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Schema de retorno para blocos de horario e disponibilidade
class TimeSlotResponse(BaseModel):
    start_time: datetime
    end_time: datetime
    available: bool

