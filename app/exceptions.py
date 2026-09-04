# Classe base de exceções personalizadas para a aplicação
class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

#classe de exceção para indicar que um usuário já está cadastrado
class UserAlreadyExistsError(AppException):
    def __init__(self, message: str = "Email já cadastrado."):
        super().__init__(message, status_code=409)

#classe de exceção para indicar credenciais inválidas
class InvalidCredentialsError(AppException):
    def __init__(self, message: str = "Email ou senha incorretos."):
        super().__init__(message, status_code=401)

#classe de exceção para indicar que um recurso não foi encontrado
class NotFoundError(AppException):
    def __init__(self, message: str = "Recurso não encontrado."):
        super().__init__(message, status_code=404)

#classe de exceção para indicar conflito de agendamento
class AppointmentConflictError(AppException):
    def __init__(self, message: str = "O horário solicitado não está disponível."):
        super().__init__(message, status_code=409)

#classe de exceção para indicar ação não permitida
class ForbiddenError(AppException):
    def __init__(self, message: str = "Acesso não permitido para este recurso."):
        super().__init__(message, status_code=403)

