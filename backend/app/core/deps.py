from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError
from app.db.session import get_db
from app.core.security import decode_token
from app.models.user import User, RoleEnum

bearer = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide ou expiré")

    user = db.query(User).filter(User.id == int(user_id), User.deleted_at.is_(None)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur inactif ou supprimé")
    return user


def require_role(*roles: RoleEnum):
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rôle requis : {[r.value for r in roles]}",
            )
        return current_user
    return checker


# Shortcut dependencies
require_gestionnaire = require_role(RoleEnum.gestionnaire, RoleEnum.superviseur, RoleEnum.admin)
require_superviseur   = require_role(RoleEnum.superviseur, RoleEnum.admin)
require_admin         = require_role(RoleEnum.admin)
