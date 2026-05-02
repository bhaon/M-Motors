from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, status

from app.api.v1.openapi_responses import openapi_http_error
from app.core.deps import CurrentUser, DbSession
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User, RoleEnum
from app.schemas.user import LoginIn, TokenOut, UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/auth", tags=["Authentification"])

_R401 = openapi_http_error(
    status.HTTP_401_UNAUTHORIZED,
    "Authentification requise ou token invalide / expiré",
    "Token invalide",
)


@router.post(
    "/register",
    response_model=UserOut,
    status_code=201,
    summary="US-02-01 — Inscription",
    responses={
        status.HTTP_409_CONFLICT: {
            "description": "Email déjà utilisé — un compte existe avec cette adresse",
            "content": {
                "application/json": {
                    "example": {"detail": "Un compte existe déjà avec cet email"},
                },
            },
        },
    },
)
def register(payload: Annotated[UserCreate, Body()], db: DbSession):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un compte existe déjà avec cet email",
        )

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        phone=payload.phone,
        role=RoleEnum.client,
        email_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post(
    "/login",
    response_model=TokenOut,
    summary="US-02-02 — Connexion",
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Identifiants incorrects (message volontairement générique)",
            "content": {
                "application/json": {
                    "example": {"detail": "Identifiants incorrects"},
                },
            },
        },
        status.HTTP_403_FORBIDDEN: {
            "description": "Compte désactivé",
            "content": {
                "application/json": {
                    "example": {"detail": "Compte désactivé"},
                },
            },
        },
    },
)
def login(payload: Annotated[LoginIn, Body()], db: DbSession):
    user = (
        db.query(User)
        .filter(
            User.email == payload.email,
            User.deleted_at.is_(None),
        )
        .first()
    )

    # Message générique (US-02-02 — ne pas indiquer si c'est l'email ou le mdp)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé",
        )

    token = create_access_token(subject=str(user.id), role=user.role.value)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.get(
    "/me",
    response_model=UserOut,
    summary="US-02-04 — Profil courant",
    responses={**_R401},
)
def get_me(current_user: CurrentUser):
    return current_user


@router.patch(
    "/me",
    response_model=UserOut,
    summary="US-02-04 — Modifier le profil",
    responses={**_R401},
)
def update_me(
    payload: Annotated[UserUpdate, Body()],
    db: DbSession,
    current_user: CurrentUser,
):
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete(
    "/me",
    status_code=204,
    summary="US-11-05 — Droit à l'effacement RGPD",
    responses={**_R401},
)
def delete_me(
    db: DbSession,
    current_user: CurrentUser,
):
    from datetime import datetime, timezone

    current_user.deleted_at = datetime.now(timezone.utc)
    current_user.is_active = False
    db.commit()
