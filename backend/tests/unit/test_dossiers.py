"""Tests des endpoints dossiers (client et back-office)."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import RoleEnum
from tests.conftest import auth_header, create_user, create_vehicle


def test_create_dossier_vehicule_inconnu(client: TestClient, db: Session) -> None:
    """Création de dossier sur véhicule absent → 404."""
    u = create_user(db)
    r = client.post(
        "/api/v1/dossiers",
        json={"vehicle_id": 99999, "type": "achat"},
        headers=auth_header(u),
    )
    assert r.status_code == 404


def test_create_soumettre_et_liste_client(client: TestClient, db: Session) -> None:
    """Flux client : création brouillon, soumission, liste et détail."""
    u = create_user(db)
    v = create_vehicle(db)
    h = auth_header(u)

    r = client.post("/api/v1/dossiers", json={"vehicle_id": v.id, "type": "lld"}, headers=h)
    assert r.status_code == 201
    did = r.json()["id"]
    assert r.json()["status"] == "brouillon"

    r2 = client.post(f"/api/v1/dossiers/{did}/soumettre", headers=h)
    assert r2.status_code == 200
    assert r2.json()["status"] == "depose"

    r3 = client.get("/api/v1/dossiers/mes-dossiers", headers=h)
    assert r3.status_code == 200
    assert r3.json()["total"] == 1

    r4 = client.get(f"/api/v1/dossiers/mes-dossiers/{did}", headers=h)
    assert r4.status_code == 200
    assert r4.json()["reference"].startswith("DOS-")


def test_soumettre_mauvais_statut(client: TestClient, db: Session) -> None:
    """Double soumission → 400."""
    u = create_user(db)
    v = create_vehicle(db)
    h = auth_header(u)
    r = client.post("/api/v1/dossiers", json={"vehicle_id": v.id, "type": "achat"}, headers=h)
    did = r.json()["id"]
    assert client.post(f"/api/v1/dossiers/{did}/soumettre", headers=h).status_code == 200
    r2 = client.post(f"/api/v1/dossiers/{did}/soumettre", headers=h)
    assert r2.status_code == 400


def test_mes_dossiers_introuvable(client: TestClient, db: Session) -> None:
    """Détail d'un dossier qui n'appartient pas au client → 404."""
    u = create_user(db)
    h = auth_header(u)
    assert client.get("/api/v1/dossiers/mes-dossiers/999", headers=h).status_code == 404


def test_bo_liste_et_detail(client: TestClient, db: Session) -> None:
    """Liste back-office et filtre par statut."""
    g = create_user(db, role=RoleEnum.gestionnaire)
    c = create_user(db)
    v = create_vehicle(db)
    h_c = auth_header(c)
    r_create = client.post("/api/v1/dossiers", json={"vehicle_id": v.id, "type": "achat"}, headers=h_c)
    did = r_create.json()["id"]
    client.post(f"/api/v1/dossiers/{did}/soumettre", headers=h_c)

    gh = auth_header(g)
    r = client.get("/api/v1/dossiers", headers=gh)
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    r2 = client.get("/api/v1/dossiers", params={"status": "depose"}, headers=gh)
    assert r2.status_code == 200

    r2b = client.get("/api/v1/dossiers", params={"type": "achat"}, headers=gh)
    assert r2b.status_code == 200

    r3 = client.get(f"/api/v1/dossiers/{did}", headers=gh)
    assert r3.status_code == 200

    assert client.get("/api/v1/dossiers", headers=h_c).status_code == 403


def test_bo_detail_404(client: TestClient, db: Session) -> None:
    """Détail BO inexistant."""
    g = create_user(db, role=RoleEnum.gestionnaire)
    assert client.get("/api/v1/dossiers/999999", headers=auth_header(g)).status_code == 404


def test_instruction_complete(client: TestClient, db: Session) -> None:
    """Prise en charge, validation."""
    g = create_user(db, role=RoleEnum.gestionnaire)
    c = create_user(db)
    v = create_vehicle(db)
    h_c = auth_header(c)
    h_g = auth_header(g)

    r = client.post("/api/v1/dossiers", json={"vehicle_id": v.id, "type": "achat"}, headers=h_c)
    did = r.json()["id"]
    client.post(f"/api/v1/dossiers/{did}/soumettre", headers=h_c)

    r2 = client.post(f"/api/v1/dossiers/{did}/prendre-en-charge", headers=h_g)
    assert r2.status_code == 200
    assert r2.json()["status"] == "en_instruction"

    r3 = client.post(f"/api/v1/dossiers/{did}/valider", headers=h_g)
    assert r3.status_code == 200
    assert r3.json()["status"] == "valide"


def test_instruction_erreurs_metier(client: TestClient, db: Session) -> None:
    """Prise en charge sur mauvais statut, validation hors instruction."""
    g = create_user(db, role=RoleEnum.gestionnaire)
    c = create_user(db)
    v = create_vehicle(db)
    h_c = auth_header(c)
    h_g = auth_header(g)

    r = client.post("/api/v1/dossiers", json={"vehicle_id": v.id, "type": "achat"}, headers=h_c)
    did = r.json()["id"]
    # brouillon : prendre en charge interdit
    assert client.post(f"/api/v1/dossiers/{did}/prendre-en-charge", headers=h_g).status_code == 400

    client.post(f"/api/v1/dossiers/{did}/soumettre", headers=h_c)
    client.post(f"/api/v1/dossiers/{did}/prendre-en-charge", headers=h_g)
    assert client.post(f"/api/v1/dossiers/{did}/valider", headers=h_g).status_code == 200
    # second valider alors que le dossier est déjà validé → 400
    assert client.post(f"/api/v1/dossiers/{did}/valider", headers=h_g).status_code == 400


def test_rejet(client: TestClient, db: Session) -> None:
    """Rejet avec motif court (422) puis motif valide (200)."""
    g = create_user(db, role=RoleEnum.gestionnaire)
    c = create_user(db)
    v = create_vehicle(db)
    h_c = auth_header(c)
    h_g = auth_header(g)

    r = client.post("/api/v1/dossiers", json={"vehicle_id": v.id, "type": "achat"}, headers=h_c)
    did = r.json()["id"]
    client.post(f"/api/v1/dossiers/{did}/soumettre", headers=h_c)

    r_bad = client.post(
        f"/api/v1/dossiers/{did}/rejeter",
        json={"motif": "trop court"},
        headers=h_g,
    )
    assert r_bad.status_code == 422

    motif = "Motif de rejet détaillé pour respecter la contrainte métier."
    r_ok = client.post(f"/api/v1/dossiers/{did}/rejeter", json={"motif": motif}, headers=h_g)
    assert r_ok.status_code == 200
    assert r_ok.json()["status"] == "rejete"


def test_rejet_statut_incompatible_400(client: TestClient, db: Session) -> None:
    """Rejet impossible tant que le dossier est encore en brouillon."""
    g = create_user(db, role=RoleEnum.gestionnaire)
    c = create_user(db)
    v = create_vehicle(db)
    h_c = auth_header(c)
    h_g = auth_header(g)
    r = client.post("/api/v1/dossiers", json={"vehicle_id": v.id, "type": "achat"}, headers=h_c)
    did = r.json()["id"]
    motif = "x" * 25
    r2 = client.post(f"/api/v1/dossiers/{did}/rejeter", json={"motif": motif}, headers=h_g)
    assert r2.status_code == 400


def test_rejet_take_charge_404(client: TestClient, db: Session) -> None:
    """Actions BO sur id inconnu → 404."""
    g = create_user(db, role=RoleEnum.gestionnaire)
    h = auth_header(g)
    long_motif = "x" * 25
    assert client.post("/api/v1/dossiers/999/prendre-en-charge", headers=h).status_code == 404
    assert client.post("/api/v1/dossiers/999/valider", headers=h).status_code == 404
    assert client.post("/api/v1/dossiers/999/rejeter", json={"motif": long_motif}, headers=h).status_code == 404
