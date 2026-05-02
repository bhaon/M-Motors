"""
Seed script — inserts the 12 M-Motors vehicles into the database.
Run: python scripts/seed.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.db.session import SessionLocal, engine, Base
from app.models.vehicle import Vehicle, VehicleOption, MoteurEnum
from app.models.user import User, RoleEnum
from app.core.security import hash_password

import app.models.vehicle  # noqa
import app.models.user     # noqa
import app.models.dossier  # noqa

Base.metadata.create_all(bind=engine)

VEHICLES_DATA = [
    dict(make="Renault", model="Clio V", year=2021, km=28000, moteur=MoteurEnum.essence,
         prix=13900, lld=True, mensualite=199,
         img="https://images.unsplash.com/photo-1609521263047-f8f205293f24?w=600&q=70",
         spec_carburant="Essence TCe 100", spec_boite="Manuelle 6v",
         spec_couleur="Rouge Flamme", spec_places=5, spec_puissance="100 ch",
         options=[("Assurance tous risques", 39), ("Assistance dépannage", 9), ("Entretien & SAV", 29), ("Contrôle technique", 5)]),
    dict(make="Peugeot", model="308 SW", year=2020, km=52000, moteur=MoteurEnum.diesel,
         prix=19500, lld=True, mensualite=269,
         img="https://images.unsplash.com/photo-1555215695-3004980ad54e?w=600&q=70",
         spec_carburant="BlueHDi 130", spec_boite="EAT8 automatique",
         spec_couleur="Gris Platinium", spec_places=5, spec_puissance="130 ch",
         options=[("Assurance tous risques", 45), ("Assistance dépannage", 9), ("Entretien & SAV", 35), ("Contrôle technique", 5)]),
    dict(make="Volkswagen", model="Golf 8", year=2022, km=18000, moteur=MoteurEnum.essence,
         prix=24900, lld=True, mensualite=319,
         img="https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?w=600&q=70",
         spec_carburant="TSI 150 Essence", spec_boite="DSG7 automatique",
         spec_couleur="Bleu Atlantis", spec_places=5, spec_puissance="150 ch",
         options=[("Assurance tous risques", 52), ("Assistance dépannage", 9), ("Entretien & SAV", 39), ("Contrôle technique", 5)]),
    dict(make="Toyota", model="Yaris", year=2021, km=33000, moteur=MoteurEnum.hybride,
         prix=16800, lld=False, mensualite=None,
         img="https://images.unsplash.com/photo-1571607388263-1044f9ea01dd?w=600&q=70",
         spec_carburant="Hybride 116 ch", spec_boite="CVT automatique",
         spec_couleur="Blanc Nacré", spec_places=5, spec_puissance="116 ch",
         options=[]),
    dict(make="BMW", model="Série 3", year=2020, km=61000, moteur=MoteurEnum.diesel,
         prix=31500, lld=True, mensualite=419,
         img="https://images.unsplash.com/photo-1555215695-3004980ad54e?w=600&q=70",
         spec_carburant="Diesel 190 xDrive", spec_boite="Steptronic 8",
         spec_couleur="Noir Saphir", spec_places=5, spec_puissance="190 ch",
         options=[("Assurance tous risques", 65), ("Assistance dépannage", 9), ("Entretien & SAV", 55), ("Contrôle technique", 5)]),
    dict(make="Citroën", model="C3 Aircross", year=2021, km=41000, moteur=MoteurEnum.essence,
         prix=17200, lld=True, mensualite=229,
         img="https://images.unsplash.com/photo-1609521263047-f8f205293f24?w=600&q=70",
         spec_carburant="PureTech 130", spec_boite="EAT6 automatique",
         spec_couleur="Orange Copper", spec_places=5, spec_puissance="130 ch",
         options=[("Assurance tous risques", 41), ("Assistance dépannage", 9), ("Entretien & SAV", 29), ("Contrôle technique", 5)]),
    dict(make="Tesla", model="Model 3", year=2022, km=22000, moteur=MoteurEnum.electrique,
         prix=38900, lld=True, mensualite=499,
         img="https://images.unsplash.com/photo-1551522435-a13afa10f103?w=600&q=70",
         spec_carburant="100% Électrique", spec_boite="Auto (1 vitesse)",
         spec_couleur="Blanc Perle", spec_places=5, spec_puissance="283 ch",
         options=[("Assurance tous risques", 72), ("Assistance dépannage", 9), ("Entretien & SAV", 45), ("Contrôle technique", 5)]),
    dict(make="Ford", model="Focus", year=2019, km=87000, moteur=MoteurEnum.diesel,
         prix=11900, lld=False, mensualite=None,
         img="https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?w=600&q=70",
         spec_carburant="EcoBlue 120 Diesel", spec_boite="Manuelle 6v",
         spec_couleur="Gris Magnétique", spec_places=5, spec_puissance="120 ch",
         options=[]),
    dict(make="Mercedes", model="Classe A", year=2021, km=29000, moteur=MoteurEnum.essence,
         prix=27800, lld=True, mensualite=359,
         img="https://images.unsplash.com/photo-1553440569-bcc63803a83d?w=600&q=70",
         spec_carburant="EQ Boost 163 ch", spec_boite="DCT7 automatique",
         spec_couleur="Blanc Polaire", spec_places=5, spec_puissance="163 ch",
         options=[("Assurance tous risques", 58), ("Assistance dépannage", 9), ("Entretien & SAV", 49), ("Contrôle technique", 5)]),
    dict(make="Dacia", model="Sandero", year=2022, km=15000, moteur=MoteurEnum.essence,
         prix=9900, lld=False, mensualite=None,
         img="https://images.unsplash.com/photo-1609521263047-f8f205293f24?w=600&q=70",
         spec_carburant="TCe 90 Essence", spec_boite="Manuelle 5v",
         spec_couleur="Vert Komodo", spec_places=5, spec_puissance="90 ch",
         options=[]),
    dict(make="Audi", model="A3 Sportback", year=2020, km=48000, moteur=MoteurEnum.essence,
         prix=26500, lld=True, mensualite=339,
         img="https://images.unsplash.com/photo-1542362567-b07e54358753?w=600&q=70",
         spec_carburant="TFSI 150 Essence", spec_boite="S-Tronic 7",
         spec_couleur="Gris Daytona", spec_places=5, spec_puissance="150 ch",
         options=[("Assurance tous risques", 55), ("Assistance dépannage", 9), ("Entretien & SAV", 45), ("Contrôle technique", 5)]),
    dict(make="Hyundai", model="Tucson", year=2021, km=37000, moteur=MoteurEnum.hybride,
         prix=28500, lld=True, mensualite=379,
         img="https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?w=600&q=70",
         spec_carburant="Hybride 48V 180 ch", spec_boite="DCT6 automatique",
         spec_couleur="Phantom Black", spec_places=5, spec_puissance="180 ch",
         options=[("Assurance tous risques", 59), ("Assistance dépannage", 9), ("Entretien & SAV", 42), ("Contrôle technique", 5)]),
]

USERS_DATA = [
    dict(email="admin@mmotors.fr",      password="Admin1234!", first_name="Admin",    last_name="M-Motors", role=RoleEnum.admin),
    dict(email="gestionnaire@mmotors.fr", password="Gest1234!", first_name="Sophie", last_name="Martin",   role=RoleEnum.gestionnaire),
    dict(email="superviseur@mmotors.fr",  password="Sup1234!",  first_name="Marc",   last_name="Dupont",   role=RoleEnum.superviseur),
    dict(email="client@mmotors.fr",       password="Client1234!", first_name="Jean", last_name="Durand",   role=RoleEnum.client),
]


def seed():
    db = SessionLocal()
    try:
        # Vehicles
        if db.query(Vehicle).count() == 0:
            for data in VEHICLES_DATA:
                options = data.pop("options")
                v = Vehicle(**data)
                db.add(v)
                db.flush()
                for name, surcharge in options:
                    db.add(VehicleOption(vehicle_id=v.id, name=name, surcharge=surcharge))
            print(f"✓ {len(VEHICLES_DATA)} véhicules insérés")
        else:
            print("→ Véhicules déjà présents, seed ignoré")

        # Users
        if db.query(User).count() == 0:
            for data in USERS_DATA:
                pwd = data.pop("password")
                u = User(hashed_password=hash_password(pwd), is_active=True, email_verified=True, **data)
                db.add(u)
            print(f"✓ {len(USERS_DATA)} utilisateurs créés")
        else:
            print("→ Utilisateurs déjà présents, seed ignoré")

        db.commit()
        print("\n✅ Seed terminé")
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur : {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
