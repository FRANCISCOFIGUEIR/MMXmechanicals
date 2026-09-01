from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.core.security import decode_token
security = HTTPBearer()
async def get_current_user(credentials=Depends(security), db=Depends(get_db)):
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token invalido ou expirado")
    result = await db.execute(select(User).where(User.id == payload.get("sub")))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario inativo ou nao encontrado")
    return user
async def check_simulation_limit(user=Depends(get_current_user)):
    if user.simulations_used >= user.sim_limit:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Limite de simulacoes do plano atingido")
    return user
