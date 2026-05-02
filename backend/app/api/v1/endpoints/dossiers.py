import secrets
import string
from datetime import datetime, timezone
from typing import Annotated, cast

from fastapi import APIRouter, Body, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.v1.openapi_responses import openapi_http_error
from app.core.deps import CurrentUser, DbSession, GestionnaireUser
from app.models.dossier import Dossier, DossierHistorique, DossierStatusEnum
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.dossier import DossierCreate, DossierListOut, DossierOut, DossierRejectIn

router = APIRouter(prefix="/dossiers", tags=["Dossiers"])

_R401 = openapi_http_error(
    status.HTTP_401_UNAUTHORIZED,
    "Authentification requise ou token invalide / expiré",
    "Token invalide",
)
_R403_BO = openapi_http_error(
    status.HTTP_403_FORBIDDEN,
    "Rôle gestionnaire, superviseur ou admin requis",
    "Rôle requis : ['gestionnaire', 'superviseur', 'admin']",
)


def _generate_reference() -> str:
    """Construit une référence unique DOS-AAAA-NNNNN (suffixe via PRNG cryptographique)."""
    year = datetime.now().year
    suffix = "".join(secrets.choice(string.digits) for _ in range(5))
    return f"DOS-{year}-{suffix}"


def _add_historique(db, dossier_id, ancien, nouveau, commentaire=None, operateur_id=None):
    db.add(
        DossierHistorique(
            dossier_id=dossier_id,
            ancien_status=ancien,
            nouveau_status=nouveau,
            commentaire=commentaire,
            operateur_id=operateur_id,
        )
    )


# ──────────────────────────────────────────────
# EP-03 — Dépôt de dossier (client)
# ──────────────────────────────────────────────


@router.post(
    "",
    response_model=DossierOut,
    status_code=201,
    summary="US-03-01 — Créer un dossier",
    responses={
        **_R401,
        **openapi_http_error(
            status.HTTP_404_NOT_FOUND,
            "Véhicule inexistant, archivé ou hors périmètre",
            "Véhicule introuvable",
        ),
    },
)
def create_dossier(
    payload: Annotated[DossierCreate, Body()],
    db: DbSession,
    current_user: CurrentUser,
):
    vehicle = (
        db.query(Vehicle)
        .filter(
            Vehicle.id == payload.vehicle_id,
            Vehicle.archived == False,
        )
        .first()
    )
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Véhicule introuvable",
        )

    ref = _generate_reference()
    while db.query(Dossier).filter(Dossier.reference == ref).first():
        ref = _generate_reference()

    dossier = Dossier(
        reference=ref,
        type=payload.type,
        status=DossierStatusEnum.brouillon,
        client_id=current_user.id,
        vehicle_id=payload.vehicle_id,
    )
    db.add(dossier)
    db.flush()
    _add_historique(db, dossier.id, None, "brouillon", operateur_id=current_user.id)
    db.commit()
    db.refresh(dossier)
    return dossier


@router.post(
    "/{dossier_id}/soumettre",
    response_model=DossierOut,
    summary="US-03-04 — Soumettre le dossier",
    responses={
        **_R401,
        **openapi_http_error(
            status.HTTP_404_NOT_FOUND,
            "Dossier introuvable ou n’appartenant pas au client",
            "Dossier introuvable",
        ),
        **openapi_http_error(
            status.HTTP_400_BAD_REQUEST,
            "Le dossier n’est pas en brouillon",
            "Seul un dossier en brouillon peut être soumis",
        ),
    },
)
def submit_dossier(
    dossier_id: int,
    db: DbSession,
    current_user: CurrentUser,
):
    dossier = _get_own_dossier(db, dossier_id, current_user)

    if dossier.status != DossierStatusEnum.brouillon:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seul un dossier en brouillon peut être soumis",
        )

    dossier.status = DossierStatusEnum.depose
    dossier.submitted_at = datetime.now(timezone.utc)
    _add_historique(db, dossier.id, "brouillon", "depose", operateur_id=current_user.id)
    db.commit()
    db.refresh(dossier)
    return dossier


# ──────────────────────────────────────────────
# EP-04 — Espace client
# ──────────────────────────────────────────────


@router.get(
    "/mes-dossiers",
    response_model=DossierListOut,
    summary="US-04-01 — Tableau de bord client",
    responses={**_R401},
)
def list_my_dossiers(
    db: DbSession,
    current_user: CurrentUser,
):
    dossiers = db.query(Dossier).filter(Dossier.client_id == current_user.id).order_by(Dossier.created_at.desc()).all()
    return DossierListOut(total=len(dossiers), items=cast(list[DossierOut], dossiers))


@router.get(
    "/mes-dossiers/{dossier_id}",
    response_model=DossierOut,
    summary="US-04-02 — Détail dossier client",
    responses={
        **_R401,
        **openapi_http_error(
            status.HTTP_404_NOT_FOUND,
            "Dossier introuvable ou n’appartenant pas au client",
            "Dossier introuvable",
        ),
    },
)
def get_my_dossier(
    dossier_id: int,
    db: DbSession,
    current_user: CurrentUser,
):
    return _get_own_dossier(db, dossier_id, current_user)


# ──────────────────────────────────────────────
# EP-06 — Instruction back-office (gestionnaire+)
# ──────────────────────────────────────────────


@router.get(
    "",
    response_model=DossierListOut,
    summary="US-06-01 — Liste back-office",
    responses={**_R403_BO},
)
def list_dossiers_bo(
    db: DbSession,
    _: GestionnaireUser,
    status: Annotated[str | None, Query()] = None,
    type_contrat: Annotated[str | None, Query()] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
):
    q = db.query(Dossier)
    if status:
        q = q.filter(Dossier.status == status)
    if type_contrat:
        q = q.filter(Dossier.type == type_contrat)
    total = q.count()
    items = q.order_by(Dossier.created_at.asc()).offset(skip).limit(limit).all()
    return DossierListOut(total=total, items=cast(list[DossierOut], items))


@router.get(
    "/{dossier_id}",
    response_model=DossierOut,
    summary="US-06-03 — Détail dossier back-office",
    responses={
        **_R403_BO,
        **openapi_http_error(
            status.HTTP_404_NOT_FOUND,
            "Aucun dossier pour cet identifiant",
            "Dossier introuvable",
        ),
    },
)
def get_dossier_bo(
    dossier_id: int,
    db: DbSession,
    _: GestionnaireUser,
):
    d = db.query(Dossier).filter(Dossier.id == dossier_id).first()
    if not d:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dossier introuvable",
        )
    return d


@router.post(
    "/{dossier_id}/prendre-en-charge",
    response_model=DossierOut,
    summary="US-06-02 — Prise en charge",
    responses={
        **_R403_BO,
        **openapi_http_error(
            status.HTTP_404_NOT_FOUND,
            "Aucun dossier pour cet identifiant",
            "Dossier introuvable",
        ),
        **openapi_http_error(
            status.HTTP_400_BAD_REQUEST,
            "Le dossier doit être à l’état « déposé »",
            "Le dossier doit être à l'état 'déposé'",
        ),
    },
)
def take_charge(
    dossier_id: int,
    db: DbSession,
    current_user: GestionnaireUser,
):
    d = db.query(Dossier).filter(Dossier.id == dossier_id).first()
    if not d:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dossier introuvable",
        )
    if d.status != DossierStatusEnum.depose:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le dossier doit être à l'état 'déposé'",
        )

    ancien = d.status.value
    d.status = DossierStatusEnum.en_instruction
    d.gestionnaire_id = current_user.id
    _add_historique(db, d.id, ancien, "en_instruction", operateur_id=current_user.id)
    db.commit()
    db.refresh(d)
    return d


@router.post(
    "/{dossier_id}/valider",
    response_model=DossierOut,
    summary="US-06-04 — Valider un dossier",
    responses={
        **_R403_BO,
        **openapi_http_error(
            status.HTTP_404_NOT_FOUND,
            "Aucun dossier pour cet identifiant",
            "Dossier introuvable",
        ),
        **openapi_http_error(
            status.HTTP_400_BAD_REQUEST,
            "Le dossier doit être en instruction",
            "Le dossier doit être en instruction",
        ),
    },
)
def validate_dossier(
    dossier_id: int,
    db: DbSession,
    current_user: GestionnaireUser,
):
    d = db.query(Dossier).filter(Dossier.id == dossier_id).first()
    if not d:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dossier introuvable",
        )
    if d.status != DossierStatusEnum.en_instruction:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le dossier doit être en instruction",
        )

    ancien = d.status.value
    d.status = DossierStatusEnum.valide
    d.validated_at = datetime.now(timezone.utc)
    _add_historique(db, d.id, ancien, "valide", operateur_id=current_user.id)
    db.commit()
    db.refresh(d)
    return d


@router.post(
    "/{dossier_id}/rejeter",
    response_model=DossierOut,
    summary="US-06-05 — Rejeter un dossier",
    responses={
        **_R403_BO,
        **openapi_http_error(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Motif de rejet trop court",
            "Le motif doit comporter au moins 20 caractères",
        ),
        **openapi_http_error(
            status.HTTP_404_NOT_FOUND,
            "Aucun dossier pour cet identifiant",
            "Dossier introuvable",
        ),
        **openapi_http_error(
            status.HTTP_400_BAD_REQUEST,
            "Statut du dossier incompatible avec un rejet",
            "Statut incompatible avec un rejet",
        ),
    },
)
def reject_dossier(
    dossier_id: int,
    payload: Annotated[DossierRejectIn, Body()],
    db: DbSession,
    current_user: GestionnaireUser,
):
    if len(payload.motif.strip()) < 20:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Le motif doit comporter au moins 20 caractères",
        )

    d = db.query(Dossier).filter(Dossier.id == dossier_id).first()
    if not d:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dossier introuvable",
        )
    if d.status not in (DossierStatusEnum.depose, DossierStatusEnum.en_instruction):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Statut incompatible avec un rejet",
        )

    ancien = d.status.value
    d.status = DossierStatusEnum.rejete
    d.motif_rejet = payload.motif
    d.rejected_at = datetime.now(timezone.utc)
    _add_historique(db, d.id, ancien, "rejete", commentaire=payload.motif, operateur_id=current_user.id)
    db.commit()
    db.refresh(d)
    return d


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────


def _get_own_dossier(db: Session, dossier_id: int, user: User) -> Dossier:
    d = (
        db.query(Dossier)
        .filter(
            Dossier.id == dossier_id,
            Dossier.client_id == user.id,
        )
        .first()
    )
    if not d:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dossier introuvable",
        )
    return d
