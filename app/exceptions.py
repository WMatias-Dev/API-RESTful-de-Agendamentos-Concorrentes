class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class UserAlreadyExistsError(AppException):
    def __init__(self, message: str = "Email já cadastrado."):
        super().__init__(message, status_code=409)


class InvalidCredentialsError(AppException):
    def __init__(self, message: str = "Email ou senha incorretos."):
        super().__init__(message, status_code=401)


class NotFoundError(AppException):
    def __init__(self, message: str = "Recurso não encontrado."):
        super().__init__(message, status_code=404)


class AppointmentConflictError(AppException):
    def __init__(self, message: str = "O horário solicitado não está disponível."):
        super().__init__(message, status_code=409)
