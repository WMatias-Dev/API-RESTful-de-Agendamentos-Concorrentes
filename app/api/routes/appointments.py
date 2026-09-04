import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.schemas.appointment import AppointmentCreate, AppointmentResponse
from app.database import get_db
from app.models.user import User
from app.services.appointment_service import AppointmentService

# Router para os endpoints de agendamento
router = APIRouter(prefix="/appointments", tags=["Agendamentos"])


# Endpoint para criar novo agendamento
@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_appointment(
    data: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AppointmentService(db)
    return service.create(client_id=current_user.id, data=data)


# Endpoint para listar agendamentos do usuario logado
@router.get("", response_model=list[AppointmentResponse])
def list_appointments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AppointmentService(db)
    return service.list_by_user(user_id=current_user.id)


# Endpoint para buscar agendamento por id
@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
    appointment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AppointmentService(db)
    return service.get_by_id(appointment_id=appointment_id, user_id=current_user.id)


# Endpoint para cancelar agendamento
@router.delete("/{appointment_id}", response_model=AppointmentResponse)
def cancel_appointment(
    appointment_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AppointmentService(db)
    return service.cancel(appointment_id=appointment_id, user_id=current_user.id)
