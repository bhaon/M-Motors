from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from app.models.dossier import DossierTypeEnum, DossierStatusEnum


class PieceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    type_piece: str
    filename: str
    uploaded_at: datetime


class HistoriqueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ancien_status: Optional[str]
    nouveau_status: str
    commentaire: Optional[str]
    created_at: datetime


class DossierCreate(BaseModel):
    vehicle_id: int
    type: DossierTypeEnum


class DossierOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    reference: str
    type: DossierTypeEnum
    status: DossierStatusEnum
    vehicle_id: int
    motif_rejet: Optional[str]
    submitted_at: Optional[datetime]
    validated_at: Optional[datetime]
    rejected_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    pieces: List[PieceOut] = []
    historique: List[HistoriqueOut] = []


class DossierRejectIn(BaseModel):
    motif: str  # min 20 chars enforced in endpoint


class DossierListOut(BaseModel):
    total: int
    items: List[DossierOut]
