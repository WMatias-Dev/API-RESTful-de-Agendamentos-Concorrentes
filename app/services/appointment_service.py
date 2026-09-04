import uuid
from datetime import date, datetime, time, timezone, timedelta
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.schemas.appointment import AppointmentCreate
from app.exceptions import (
    AppException,
    AppointmentConflictError,
    ForbiddenError,
    NotFoundError,
)
from app.models.appointment import Appointment, AppointmentStatus
from app.models.user import UserRole
from app.repositories.appointment_repository import AppointmentRepository
from app.repositories.user_repository import UserRepository


# Classe que centraliza as regras de negocio de agendamentos e disponibilidade
class AppointmentService:
    def __init__(self, db: Session):
        self.db = db
        self.appointment_repo = AppointmentRepository(db)
        self.user_repo = UserRepository(db)

    # Cria um novo agendamento validando regras e tratando conflito de horario
    def create(self, client_id: uuid.UUID, data: AppointmentCreate) -> Appointment:
        # Nao permite agendar consigo mesmo
        if client_id == data.professional_id:
            raise AppException("Não é possível agendar um horário consigo mesmo.")

        # Verifica se o profissional existe e tem a role adequada
        professional = self.user_repo.get_by_id(data.professional_id)
        if not professional or professional.role != UserRole.PROFESSIONAL:
            raise NotFoundError("Profissional não encontrado.")

        # Garante que o agendamento seja marcado para o futuro
        now = datetime.now(timezone.utc)
        if data.start_time <= now:
            raise AppException("O horário de início deve ser no futuro.")

        appointment = Appointment(
            client_id=client_id,
            professional_id=data.professional_id,
            start_time=data.start_time,
            end_time=data.end_time,
            notes=data.notes,
            status=AppointmentStatus.SCHEDULED,
        )

        # Tenta salvar no banco; caso ocorra sobreposicao, a Exclusion Constraint dispara IntegrityError
        try:
            return self.appointment_repo.create(appointment)
        except IntegrityError:
            self.db.rollback()
            raise AppointmentConflictError("O horário solicitado não está disponível.")

    # Busca um agendamento garantindo que o usuario tenha permissao para ve-lo
    def get_by_id(self, appointment_id: uuid.UUID, user_id: uuid.UUID) -> Appointment:
        appointment = self.appointment_repo.get_by_id(appointment_id)
        if not appointment:
            raise NotFoundError("Agendamento não encontrado.")

        if appointment.client_id != user_id and appointment.professional_id != user_id:
            raise ForbiddenError("Acesso não permitido para este agendamento.")

        return appointment

    # Lista todos os agendamentos do usuario logado
    def list_by_user(self, user_id: uuid.UUID) -> list[Appointment]:
        return self.appointment_repo.list_by_user(user_id)

    # Cancela um agendamento existente
    def cancel(self, appointment_id: uuid.UUID, user_id: uuid.UUID) -> Appointment:
        appointment = self.appointment_repo.get_by_id(appointment_id)
        if not appointment:
            raise NotFoundError("Agendamento não encontrado.")

        if appointment.client_id != user_id and appointment.professional_id != user_id:
            raise ForbiddenError("Acesso não permitido para cancelar este agendamento.")

        if appointment.status == AppointmentStatus.CANCELED:
            raise AppException("Este agendamento já foi cancelado.")

        appointment.status = AppointmentStatus.CANCELED
        return self.appointment_repo.update(appointment)

    # Consulta horarios disponiveis de um profissional em uma data especifica (08:00 as 18:00)
    def get_availability(self, professional_id: uuid.UUID, target_date: date) -> list[dict]:
        professional = self.user_repo.get_by_id(professional_id)
        if not professional or professional.role != UserRole.PROFESSIONAL:
            raise NotFoundError("Profissional não encontrado.")

        day_start = datetime.combine(target_date, time(8, 0)).replace(tzinfo=timezone.utc)
        day_end = datetime.combine(target_date, time(18, 0)).replace(tzinfo=timezone.utc)

        # Busca agendamentos ativos que caem nesse dia
        active_appointments = self.appointment_repo.list_active_by_professional_and_date_range(
            professional_id=professional_id,
            start_date=day_start,
            end_date=day_end,
        )

        # Gera blocos de 1 hora e verifica sobreposicoes
        slots = []
        current = day_start
        while current < day_end:
            slot_end = current + timedelta(hours=1)
            is_occupied = any(
                app.start_time < slot_end and app.end_time > current
                for app in active_appointments
            )
            slots.append({
                "start_time": current,
                "end_time": slot_end,
                "available": not is_occupied,
            })
            current = slot_end

        return slots
