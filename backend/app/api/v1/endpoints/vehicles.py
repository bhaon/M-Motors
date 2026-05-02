from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.deps import get_current_user, require_gestionnaire
from app.models.vehicle import Vehicle, MoteurEnum
from app.models.user import User
from app.schemas.vehicle import (
    VehicleOut, VehicleListOut, VehicleCreate, VehicleUpdate
)

router = APIRouter(prefix="/vehicules", tags=["Véhicules"])


# ──────────────────────────────────────────────
# EP-01 — Public (US-01-01 à US-01-05)
# ──────────────────────────────────────────────

@router.get("", response_model=VehicleListOut, summary="US-01-01/03 — Catalogue public avec filtres")
def list_vehicles(
    marque:  Optional[str]       = Query(None),
    modele:  Optional[str]       = Query(None),
    moteur:  Optional[MoteurEnum] = Query(None),
    km_max:  Optional[int]       = Query(None, alias="kmMax"),
    prix_max: Optional[float]    = Query(None, alias="prixMax"),
    type_contrat: Optional[str]  = Query(None, alias="type"),   # all | achat | lld
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(Vehicle).filter(
        Vehicle.archived == False,
        Vehicle.visible_catalogue == True,
    )
    if marque:
        q = q.filter(Vehicle.make.ilike(f"%{marque}%"))
    if modele:
        q = q.filter(Vehicle.model.ilike(f"%{modele}%"))
    if moteur:
        q = q.filter(Vehicle.moteur == moteur)
    if km_max is not None:
        q = q.filter(Vehicle.km <= km_max)
    if prix_max is not None:
        q = q.filter(Vehicle.prix <= prix_max)
    if type_contrat == "lld":
        q = q.filter(Vehicle.lld == True)
    elif type_contrat == "achat":
        q = q.filter(Vehicle.lld == False)

    total = q.count()
    vehicles = q.order_by(Vehicle.created_at.desc()).offset(skip).limit(limit).all()

    return VehicleListOut(
        total=total,
        items=[VehicleOut.from_orm_vehicle(v) for v in vehicles],
    )


@router.get("/marques", summary="US-01-03 — Liste des marques disponibles")
def list_marques(db: Session = Depends(get_db)):
    rows = (
        db.query(Vehicle.make)
        .filter(Vehicle.archived == False, Vehicle.visible_catalogue == True)
        .distinct()
        .order_by(Vehicle.make)
        .all()
    )
    return [r.make for r in rows]


@router.get("/{vehicle_id}", response_model=VehicleOut, summary="US-01-04 — Fiche détaillée")
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    v = db.query(Vehicle).filter(
        Vehicle.id == vehicle_id,
        Vehicle.archived == False,
    ).first()
    if not v:
        raise HTTPException(status_code=404, detail="Véhicule introuvable")
    return VehicleOut.from_orm_vehicle(v)


# ──────────────────────────────────────────────
# EP-05 — Back-office (gestionnaire+)
# ──────────────────────────────────────────────

@router.post("", response_model=VehicleOut, status_code=201, summary="US-05-01 — Créer un véhicule")
def create_vehicle(
    payload: VehicleCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_gestionnaire),
):
    v = Vehicle(**payload.model_dump())
    db.add(v)
    db.commit()
    db.refresh(v)
    return VehicleOut.from_orm_vehicle(v)


@router.patch("/{vehicle_id}", response_model=VehicleOut, summary="US-05-02 — Modifier un véhicule")
def update_vehicle(
    vehicle_id: int,
    payload: VehicleUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_gestionnaire),
):
    v = db.query(Vehicle).filter(Vehicle.id == vehicle_id, Vehicle.archived == False).first()
    if not v:
        raise HTTPException(status_code=404, detail="Véhicule introuvable")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(v, field, value)
    db.commit()
    db.refresh(v)
    return VehicleOut.from_orm_vehicle(v)


@router.post("/{vehicle_id}/toggle-lld", response_model=VehicleOut, summary="US-05-03 — Basculer Achat ↔ LLD")
def toggle_lld(
    vehicle_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_gestionnaire),
):
    v = db.query(Vehicle).filter(Vehicle.id == vehicle_id, Vehicle.archived == False).first()
    if not v:
        raise HTTPException(status_code=404, detail="Véhicule introuvable")
    v.lld = not v.lld
    if not v.lld:
        v.mensualite = None
    db.commit()
    db.refresh(v)
    return VehicleOut.from_orm_vehicle(v)


@router.delete("/{vehicle_id}", status_code=204, summary="US-05-04 — Archiver (soft delete)")
def archive_vehicle(
    vehicle_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_gestionnaire),
):
    from datetime import datetime, timezone
    v = db.query(Vehicle).filter(Vehicle.id == vehicle_id, Vehicle.archived == False).first()
    if not v:
        raise HTTPException(status_code=404, detail="Véhicule introuvable")
    v.archived = True
    v.archived_at = datetime.now(timezone.utc)
    v.visible_catalogue = False
    db.commit()
