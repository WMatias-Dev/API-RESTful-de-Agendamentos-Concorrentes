import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from app.models.user import UserRole


# Schema para cadastro de novo usuario
class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)
    role: UserRole = UserRole.CLIENT


# Schema para requisicao de login
class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Schema de saida com dados do usuario
class UserResponse(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    role: UserRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Schema de resposta com o token JWT emitido
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
