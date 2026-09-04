import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.appointment import Appointment, AppointmentStatus

#classe repository para operacoes no banco de dados com agendamentos
class AppointmentRepository:
    def __init__(self, db: Session):
        self.db = db

    #busca agendamento pelo id passado
    def get_by_id(self, appointment_id: uuid.UUID) -> Appointment | None:
        return self.db.query(Appointment).filter(Appointment.id == appointment_id).first()

    #cria o agendamento
    def create(self, appointment: Appointment) -> Appointment:
        self.db.add(appointment)
        self.db.commit()
        self.db.refresh(appointment)
        return appointment
    #lista os agendamentos do usuario passado
    def list_by_user(self, user_id: uuid.UUID) -> list[Appointment]:
        return (
            self.db.query(Appointment)
            .filter((Appointment.client_id == user_id) | (Appointment.professional_id == user_id))
            .order_by(Appointment.start_time.asc())
            .all()
        )
    #lista os agendamentos ativos do profissional no periodo passado
    def list_active_by_professional_and_date_range(
        self,
        professional_id: uuid.UUID,
        start_date: datetime,
        end_date: datetime,
    ) -> list[Appointment]:
        return (
            self.db.query(Appointment)
            .filter(
                Appointment.professional_id == professional_id,
                Appointment.status == AppointmentStatus.SCHEDULED,
                Appointment.start_time < end_date,
                Appointment.end_time > start_date,
            )
            .order_by(Appointment.start_time.asc())
            .all()
        )
    #atualiza o agendamento
    def update(self, appointment: Appointment) -> Appointment:
        self.db.commit()
        self.db.refresh(appointment)
        return appointment
