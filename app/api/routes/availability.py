import uuid
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.schemas.appointment import TimeSlotResponse
from app.database import get_db
from app.services.appointment_service import AppointmentService

# Router para os endpoints de disponibilidade
router = APIRouter(prefix="/availability", tags=["Disponibilidade"])


# Endpoint para consultar a disponibilidade de um profissional em determinada data
@router.get("/{professional_id}", response_model=list[TimeSlotResponse])
def get_availability(
    professional_id: uuid.UUID,
    date: date = Query(..., description="Data para consulta no formato YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    service = AppointmentService(db)
    return service.get_availability(professional_id=professional_id, target_date=date)
