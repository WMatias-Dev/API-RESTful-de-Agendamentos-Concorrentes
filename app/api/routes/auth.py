from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.api.dependencies import get_current_user
from app.api.schemas.auth import UserCreate, UserLogin, UserResponse, TokenResponse
from app.database import get_db
from app.models.user import User
from app.services.auth_service import AuthService

#cria o router para autenticação
router = APIRouter(prefix="/auth", tags=["Autenticação"])

#Endpoint para cadastro de novo usuario
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return auth_service.register(user_data)

#Endpoint para login
@router.post("/login", response_model=TokenResponse)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    auth_service = AuthService(db)
    return auth_service.authenticate(login_data)

#Endpoint para obter informações do usuario atual
@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
