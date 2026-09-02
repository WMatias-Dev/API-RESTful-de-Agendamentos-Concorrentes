import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.security import decode_access_token

# Esquema para ler o token do cabecalho Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

#Função para verificar se o usuário está autenticado
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    #cria exceção caso o token seja inválido
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token de autenticação inválido ou expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    #decodifica o token
    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception

    #pega o id do usuario
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise credentials_exception

    #converte o id do usuario para UUID
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    #busca o usuario no banco de dados
    user = UserRepository(db).get_by_id(user_id)
    if not user:
        raise credentials_exception

    return user
