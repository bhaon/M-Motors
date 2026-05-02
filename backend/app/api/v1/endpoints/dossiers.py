import secrets
import string
from datetime import datetime, timezone
from typing import cast
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_current_user, require_gestionnaire
from app.models.dossier import Dossier, DossierStatusEnum, DossierHistorique
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.dossier import DossierCreate, DossierOut, DossierListOut, DossierRejectIn

router = APIRouter(prefix="/dossiers", tags=["Dossiers"])


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


@router.post("", response_model=DossierOut, status_code=201, summary="US-03-01 — Créer un dossier")
def create_dossier(
    payload: DossierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
        raise HTTPException(status_code=404, detail="Véhicule introuvable")

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


@router.post("/{dossier_id}/soumettre", response_model=DossierOut, summary="US-03-04 — Soumettre le dossier")
def submit_dossier(
    dossier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dossier = _get_own_dossier(db, dossier_id, current_user)

    if dossier.status != DossierStatusEnum.brouillon:
        raise HTTPException(status_code=400, detail="Seul un dossier en brouillon peut être soumis")

    dossier.status = DossierStatusEnum.depose
    dossier.submitted_at = datetime.now(timezone.utc)
    _add_historique(db, dossier.id, "brouillon", "depose", operateur_id=current_user.id)
    db.commit()
    db.refresh(dossier)
    return dossier


# ──────────────────────────────────────────────
# EP-04 — Espace client
# ──────────────────────────────────────────────


@router.get("/mes-dossiers", response_model=DossierListOut, summary="US-04-01 — Tableau de bord client")
def list_my_dossiers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    dossiers = db.query(Dossier).filter(Dossier.client_id == current_user.id).order_by(Dossier.created_at.desc()).all()
    return DossierListOut(total=len(dossiers), items=cast(list[DossierOut], dossiers))


@router.get("/mes-dossiers/{dossier_id}", response_model=DossierOut, summary="US-04-02 — Détail dossier client")
def get_my_dossier(
    dossier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_own_dossier(db, dossier_id, current_user)


# ──────────────────────────────────────────────
# EP-06 — Instruction back-office (gestionnaire+)
# ──────────────────────────────────────────────


@router.get("", response_model=DossierListOut, summary="US-06-01 — Liste back-office")
def list_dossiers_bo(
    status: str = Query(None),
    type_contrat: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_gestionnaire),
):
    q = db.query(Dossier)
    if status:
        q = q.filter(Dossier.status == status)
    if type_contrat:
        q = q.filter(Dossier.type == type_contrat)
    total = q.count()
    items = q.order_by(Dossier.created_at.asc()).offset(skip).limit(limit).all()
    return DossierListOut(total=total, items=cast(list[DossierOut], items))


@router.get("/{dossier_id}", response_model=DossierOut, summary="US-06-03 — Détail dossier back-office")
def get_dossier_bo(
    dossier_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_gestionnaire),
):
    d = db.query(Dossier).filter(Dossier.id == dossier_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    return d


@router.post("/{dossier_id}/prendre-en-charge", response_model=DossierOut, summary="US-06-02 — Prise en charge")
def take_charge(
    dossier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_gestionnaire),
):
    d = db.query(Dossier).filter(Dossier.id == dossier_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    if d.status != DossierStatusEnum.depose:
        raise HTTPException(status_code=400, detail="Le dossier doit être à l'état 'déposé'")

    ancien = d.status.value
    d.status = DossierStatusEnum.en_instruction
    d.gestionnaire_id = current_user.id
    _add_historique(db, d.id, ancien, "en_instruction", operateur_id=current_user.id)
    db.commit()
    db.refresh(d)
    return d


@router.post("/{dossier_id}/valider", response_model=DossierOut, summary="US-06-04 — Valider un dossier")
def validate_dossier(
    dossier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_gestionnaire),
):
    d = db.query(Dossier).filter(Dossier.id == dossier_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    if d.status != DossierStatusEnum.en_instruction:
        raise HTTPException(status_code=400, detail="Le dossier doit être en instruction")

    ancien = d.status.value
    d.status = DossierStatusEnum.valide
    d.validated_at = datetime.now(timezone.utc)
    _add_historique(db, d.id, ancien, "valide", operateur_id=current_user.id)
    db.commit()
    db.refresh(d)
    return d


@router.post("/{dossier_id}/rejeter", response_model=DossierOut, summary="US-06-05 — Rejeter un dossier")
def reject_dossier(
    dossier_id: int,
    payload: DossierRejectIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_gestionnaire),
):
    if len(payload.motif.strip()) < 20:
        raise HTTPException(status_code=422, detail="Le motif doit comporter au moins 20 caractères")

    d = db.query(Dossier).filter(Dossier.id == dossier_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    if d.status not in (DossierStatusEnum.depose, DossierStatusEnum.en_instruction):
        raise HTTPException(status_code=400, detail="Statut incompatible avec un rejet")

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
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    return d
