"""Tests des endpoints d'authentification."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from tests.conftest import auth_header, create_user, unique_email


def test_register_et_login_ok(client: TestClient) -> None:
    """Inscription puis connexion renvoie un token et le profil."""
    email = unique_email()
    r = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "MotDePasseSecurise1!",
            "first_name": "Jean",
            "last_name": "Dupont",
        },
    )
    assert r.status_code == 201
    assert r.json()["email"] == email

    r2 = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "MotDePasseSecurise1!"},
    )
    assert r2.status_code == 200
    body = r2.json()
    assert "access_token" in body
    assert body["user"]["email"] == email


def test_register_doublon_409(client: TestClient, db: Session) -> None:
    """Deux inscriptions avec le même email renvoient 409."""
    email = unique_email()
    payload = {
        "email": email,
        "password": "MotDePasseSecurise1!",
        "first_name": "A",
        "last_name": "B",
    }
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    r = client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 409


def test_login_identifiants_invalides_401(client: TestClient, db: Session) -> None:
    """Email inconnu ou mot de passe erroné → 401 sans fuite d'information."""
    create_user(db, email="existant@example.com", password="BonMotDePasse1!")
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "existant@example.com", "password": "mauvais"},
    )
    assert r.status_code == 401


def test_login_compte_desactive_403(client: TestClient, db: Session) -> None:
    """Un compte désactivé ne peut pas se connecter."""
    u = create_user(db, email=unique_email(), is_active=False)
    r = client.post(
        "/api/v1/auth/login",
        json={"email": u.email, "password": "SecretMotDePasse1!"},
    )
    assert r.status_code == 403


def test_me_sans_token_403(client: TestClient) -> None:
    """GET /auth/me sans Bearer renvoie 403 (schéma HTTPBearer)."""
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 403


def test_me_token_invalide_401(client: TestClient) -> None:
    """Un JWT illisible renvoie 401."""
    r = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-valid-jwt"})
    assert r.status_code == 401


def test_me_utilisateur_inconnu_401(client: TestClient) -> None:
    """Un JWT valide pour un id utilisateur absent renvoie 401."""
    token = create_access_token(subject="999999", role="client")
    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_me_patch_delete(client: TestClient, db: Session) -> None:
    """Profil courant, mise à jour puis soft-delete RGPD."""
    u = create_user(db)
    h = auth_header(u)

    r = client.get("/api/v1/auth/me", headers=h)
    assert r.status_code == 200
    assert r.json()["first_name"] == "Test"

    r2 = client.patch("/api/v1/auth/me", headers=h, json={"first_name": "Nouveau"})
    assert r2.status_code == 200
    assert r2.json()["first_name"] == "Nouveau"

    r3 = client.delete("/api/v1/auth/me", headers=h)
    assert r3.status_code == 204

    db.refresh(u)
    assert u.is_active is False
    assert u.deleted_at is not None

    assert client.get("/api/v1/auth/me", headers=h).status_code == 401
