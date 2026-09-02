from sqlalchemy.orm import Session
from app.api.schemas.auth import UserCreate, UserLogin, TokenResponse
from app.exceptions import UserAlreadyExistsError, InvalidCredentialsError
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.security import hash_password, verify_password, create_access_token


class AuthService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)

    def register(self, user_data: UserCreate) -> User:
        # Impede o cadastro de usuarios com o mesmo e-mail
        existing_user = self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise UserAlreadyExistsError()

        hashed_password = hash_password(user_data.password)

        new_user = User(
            name=user_data.name,
            email=user_data.email,
            password_hash=hashed_password,
            role=user_data.role,
        )

        return self.user_repo.create(new_user)

    def authenticate(self, login_data: UserLogin) -> TokenResponse:
        # Busca o usuario por e-mail e confere a senha
        user = self.user_repo.get_by_email(login_data.email)
        if not user or not verify_password(login_data.password, user.password_hash):
            raise InvalidCredentialsError()

        # Monta os dados do payload do JWT
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
        }

        access_token = create_access_token(payload)
        return TokenResponse(access_token=access_token)
