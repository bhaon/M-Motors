# M-Motors — Documentation du pipeline CI/CD

> **Fichier :** `.github/workflows/m-motors-CICD.yaml`  
> **Stack :** Next.js · FastAPI/Python · PostgreSQL · Redis  
> **Registry :** GitHub Container Registry (GHCR)  
> **Déploiement :** Docker Compose via SSH (serveur local)

---

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Déclencheurs](#2-déclencheurs)
3. [Variables globales et configuration](#3-variables-globales-et-configuration)
4. [Schéma du pipeline](#4-schéma-du-pipeline)
5. [Description détaillée des jobs](#5-description-détaillée-des-jobs)
   - [Job 1 — Détection des changements](#job-1--détection-des-changements)
   - [Job 2 — Lint Frontend](#job-2--lint-frontend)
   - [Job 3 — Lint Backend](#job-3--lint-backend)
   - [Job 4 — Tests unitaires Backend](#job-4--tests-unitaires-backend)
   - [Job 5 — Tests d'intégration Backend](#job-5--tests-dintégration-backend)
   - [Job 6 — Tests unitaires Frontend](#job-6--tests-unitaires-frontend)
   - [Job 7 — Build Frontend](#job-7--build-frontend)
   - [Job 8 — Analyse SonarQube](#job-8--analyse-sonarqube)
   - [Job 9 — Build & Push Docker Images](#job-9--build--push-docker-images)
   - [Job 10 — Déploiement Staging](#job-10--déploiement-staging)
   - [Job 11 — Tests E2E Playwright](#job-11--tests-e2e-playwright)
   - [Job 12 — Déploiement Production](#job-12--déploiement-production)
   - [Job 13 — Notification Slack](#job-13--notification-slack)
6. [Secrets à configurer](#6-secrets-à-configurer)
7. [Fichiers requis côté serveur](#7-fichiers-requis-côté-serveur)
8. [Stratégie de branches](#8-stratégie-de-branches)
9. [Rollback](#9-rollback)
10. [Critères de qualité (DoD)](#10-critères-de-qualité-dod)

---

## 1. Vue d'ensemble

Le pipeline M-Motors automatise l'intégralité du cycle de vie du code, de la vérification syntaxique jusqu'au déploiement en production. Il repose sur **13 jobs** organisés en 5 phases séquentielles avec des dépendances explicites entre chaque étape.

```
Lint & Types  →  Tests  →  Build  →  Sécurité  →  Images Docker  →  Déploiement
```

Les images Docker sont publiées sur le **GitHub Container Registry (GHCR)** et tirées depuis le serveur de destination via SSH. Aucune clé AWS, aucun orchestrateur Kubernetes n'est nécessaire pour cette phase — un serveur disposant de Docker Engine suffit.

---

## 2. Déclencheurs

Le workflow se déclenche dans trois situations :

| Événement | Branches concernées | Effet |
|---|---|---|
| `push` | `main`, `develop` | Lance le pipeline complet |
| `pull_request` | `main`, `develop` | Lance CI uniquement (pas de déploiement) |
| `workflow_dispatch` | — | Déclenchement manuel depuis l'UI GitHub |

Le déclenchement manuel (`workflow_dispatch`) expose deux paramètres :

- **`environment`** : choix entre `staging` et `production`
- **`skip_tests`** : booléen pour bypasser les tests en cas d'urgence (à utiliser avec précaution)

Les fichiers `**.md`, `.gitignore` et `docs/**` sont exclus du déclenchement sur `push` — modifier la documentation ne relance pas le pipeline.

La directive `concurrency` annule automatiquement tout run en cours sur la même branche lorsqu'un nouveau commit est poussé, évitant ainsi des déploiements croisés.

---

## 3. Variables globales et configuration

Les variables d'environnement définies au niveau `env:` sont accessibles par tous les jobs :

| Variable | Valeur | Rôle |
|---|---|---|
| `REGISTRY` | `ghcr.io` | URL du registry Docker |
| `IMAGE_FRONTEND` | `ghcr.io/<owner>/mmotors-frontend` | Nom complet de l'image frontend |
| `IMAGE_BACKEND` | `ghcr.io/<owner>/mmotors-backend` | Nom complet de l'image backend |
| `NODE_VERSION` | `20` | Version Node.js LTS utilisée partout |
| `PYTHON_VERSION` | `3.12` | Version Python utilisée partout |

---

## 4. Schéma du pipeline

```
                        ┌─────────────┐
                        │  changes    │  Job 1 — paths-filter
                        └──────┬──────┘
              ┌─────────────────┴──────────────────┐
              │                                    │
     ┌────────▼────────┐                  ┌────────▼────────┐
     │  lint-frontend  │  Job 2           │  lint-backend   │  Job 3
     └────────┬────────┘                  └────────┬────────┘
              │                        ┌───────────┴───────────┐
     ┌────────▼────────┐      ┌────────▼────────┐   ┌─────────▼────────┐
     │test-frontend    │  J6  │test-backend     │J4 │test-backend      │J5
     │unit (Jest)      │      │unit (Pytest)    │   │integration (PG)  │
     └────────┬────────┘      └────────┬────────┘   └─────────┬────────┘
              │                        │                       │
     ┌────────▼────────┐      ┌────────▼───────────────────────▼────────┐
     │ build-frontend  │  J7  │           sonarqube (SAST)              │  J8
     └────────┬────────┘      └───────────────────┬─────────────────────┘
              │                                   │
              └─────────────────┬─────────────────┘
                       ┌────────▼────────┐
                       │  build-images   │  Job 9 — Build + Push GHCR + Trivy
                       └────────┬────────┘
                    ┌───────────┴────────────┐
                    │ (develop)              │ (main)
           ┌────────▼────────┐     ┌────────▼────────┐
           │ deploy-staging  │ J10 │                 │
           └────────┬────────┘     │  (attend E2E)   │
           ┌────────▼────────┐     │                 │
           │   test-e2e      │ J11 │                 │
           │  (Playwright)   │     │                 │
           └────────┬────────┘     └────────┬────────┘
                    └───────────┬───────────┘
                       ┌────────▼────────┐
                       │deploy-production│  Job 12 — Approbation manuelle
                       └────────┬────────┘
                       ┌────────▼────────┐
                       │     notify      │  Job 13 — Slack
                       └─────────────────┘
```

---

## 5. Description détaillée des jobs

### Job 1 — Détection des changements

**Action utilisée :** `dorny/paths-filter@v3`

Ce job analyse les fichiers modifiés dans le commit et expose trois outputs booléens (`frontend`, `backend`, `compose`) qui conditionnent l'exécution des jobs suivants. Un push qui ne touche que le backend ne déclenche pas les jobs de lint et test frontend, ce qui réduit le temps d'exécution global et la consommation de minutes GitHub Actions.

```
frontend → frontend/**
backend  → backend/**, requirements*.txt, alembic/**
compose  → docker-compose*.yml, .env.example, .github/workflows/**
```

---

### Job 2 — Lint Frontend

**Dépend de :** `changes` (si `frontend == true`)  
**Répertoire de travail :** `frontend/`

Trois vérifications s'exécutent en séquence :

1. **TypeScript strict** (`tsc --noEmit`) — vérifie que le code compile sans erreur de typage sans produire de fichiers de sortie
2. **ESLint** — analyse statique des règles de qualité et de style définies dans `.eslintrc`
3. **Prettier** — vérifie que le formatage est conforme (`--check` uniquement, sans réécriture)

Si l'une des trois étapes échoue, le job est marqué en erreur et bloque tous les jobs en aval qui en dépendent.

---

### Job 3 — Lint Backend

**Dépend de :** `changes` (si `backend == true`)  
**Répertoire de travail :** `backend/`

Trois outils s'exécutent :

1. **Ruff** — linter Python ultra-rapide (remplace Flake8 + isort + pyupgrade) avec vérification du formatage (`ruff format --check`)
2. **Mypy** en mode `--strict` — vérification statique des types Python, bloquant
3. **Bandit** — détection de patterns de sécurité dangereux dans le code Python (SQL injection, use of `subprocess`, secrets hardcodés, etc.). Le rapport JSON est uploadé comme artefact même en cas d'échec (`continue-on-error: true`) pour ne pas bloquer le pipeline sur des faux positifs

---

### Job 4 — Tests unitaires Backend

**Dépend de :** `lint-backend`  
**Base de données :** SQLite in-memory (pas de service externe)

Exécute la suite `tests/unit/` avec Pytest. La couverture de code est mesurée et un seuil minimum de **80 %** est enforced (`--cov-fail-under=80`) — c'est le critère de DoD défini dans le CDC M-Motors.

Les rapports produits (JUnit XML + couverture XML) sont uploadés comme artefacts et récupérés plus tard par le job SonarQube.

---

### Job 5 — Tests d'intégration Backend

**Dépend de :** `lint-backend`  
**Services GitHub Actions :** PostgreSQL 16-alpine + Redis 7-alpine

GitHub Actions instancie les deux services dans des containers sidecar avec des healthchecks. Les tests d'intégration s'exécutent contre une vraie base PostgreSQL et un vrai Redis, contrairement aux tests unitaires qui utilisent SQLite.

Les migrations Alembic sont exécutées avant les tests (`alembic upgrade head`) pour s'assurer que le schéma est à jour. Un timeout de 60 secondes par test évite les blocages sur des appels réseau.

---

### Job 6 — Tests unitaires Frontend

**Dépend de :** `lint-frontend`

Lance la suite Jest en mode CI (`--ci`) avec génération du rapport de couverture au format `lcov`. Le flag `--ci` désactive le mode watch et traite tous les tests échoués comme bloquants.

---

### Job 7 — Build Frontend

**Dépend de :** `lint-frontend` + `test-frontend-unit`

Exécute `next build` pour valider que le projet compile en mode production. Cette étape détecte les erreurs de build (imports manquants, pages mal configurées, erreurs d'optimisation d'images) qui ne seraient pas captées par TypeScript seul.

La variable `NEXT_PUBLIC_APP_ENV` est positionnée dynamiquement selon la branche (`main` → `production`, autre → `staging`).

---

### Job 8 — Analyse SonarQube

**Dépend de :** `test-backend-unit` + `test-frontend-unit`  
**Action utilisée :** `SonarSource/sonarcloud-github-action@master`

SonarCloud analyse les sources frontend (`frontend/src`) et backend (`backend/app`) en combinant :

- Les rapports de couverture récupérés depuis les artefacts des jobs précédents
- L'historique Git complet (`fetch-depth: 0`) pour les métriques de duplication et d'évolution

Le **Quality Gate** est configuré en mode bloquant (`-Dsonar.qualitygate.wait=true`) — si le gate échoue (couverture insuffisante, nouvelles vulnérabilités critiques, trop de code smell), le pipeline s'arrête et le build ne passe pas en phase image.

---

### Job 9 — Build & Push Docker Images

**Dépend de :** `build-frontend` + `test-backend-integration` + `sonarqube`  
**Permissions requises :** `packages: write`

Ce job s'exécute uniquement sur les branches `main` et `develop` (pas sur les PR). Il effectue dans l'ordre :

**Tagging des images** via `docker/metadata-action` — chaque image reçoit trois tags simultanément :
- `sha-<short-sha>` — tag immuable lié au commit exact
- `develop` ou `main` — tag de branche mis à jour à chaque push
- `latest` — uniquement sur `main`

**Build multi-arch** via `docker/build-push-action` avec `docker/setup-buildx-action` — les images sont construites pour `linux/amd64` et `linux/arm64`. Le cache GitHub Actions (`type=gha`) est utilisé pour éviter de reconstruire les layers inchangés.

**Scan de sécurité Trivy** — chaque image est scannée après le push à la recherche de vulnérabilités `CRITICAL` ou `HIGH` dans les packages OS et les dépendances applicatives. Un résultat positif (`exit-code: 1`) bloque le pipeline. Les rapports SARIF sont uploadés dans le Security tab de GitHub.

---

### Job 10 — Déploiement Staging

**Dépend de :** `build-images`  
**Condition :** branche `develop` uniquement  
**Action SSH :** `appleboy/ssh-action@v1`

Le job se connecte en SSH au serveur staging et exécute le script de déploiement en une seule session :

```
git fetch + reset  →  copie .env.staging  →  login GHCR  →  docker compose pull
→  alembic upgrade head  →  docker compose up -d --wait  →  docker image prune
```

Le flag `--wait` de `docker compose up` est critique : il attend que les healthchecks définis dans le `docker-compose.yml` soient au vert avant de rendre la main. Si un container reste en `unhealthy`, la commande échoue et le job passe en erreur.

Après le déploiement SSH, un smoke test HTTP est lancé depuis le runner GitHub avec `curl --retry 5` pour confirmer que l'API répond bien.

---

### Job 11 — Tests E2E Playwright

**Dépend de :** `deploy-staging`  
**Navigateurs :** Chromium + Firefox

Playwright exécute les tests end-to-end directement contre l'environnement staging fraîchement déployé (`PLAYWRIGHT_BASE_URL` pointe vers le serveur staging). Cela garantit que les tests couvrent le comportement réel de l'application déployée et non un environnement simulé.

Le rapport HTML Playwright est uploadé comme artefact (conservé 14 jours) et visible dans l'UI GitHub Actions via l'onglet **Artifacts**.

---

### Job 12 — Déploiement Production

**Dépend de :** `build-images` + `test-e2e`  
**Condition :** branche `main` ou `workflow_dispatch` avec `environment=production`  
**Approbation manuelle requise** via GitHub Environment protection rules

Ce job ajoute deux étapes de sécurité absentes du déploiement staging :

**Dump PostgreSQL pré-déploiement** — un `pg_dump` est exécuté via `docker compose exec` et sauvegardé dans `backups/` sur le serveur. Les 10 dumps les plus récents sont conservés, les plus anciens sont supprimés automatiquement.

**Sauvegarde du SHA Git** — le SHA du commit actuellement en production est écrit dans `.last-stable-sha` avant toute modification, permettant un rollback précis.

Le déploiement suit ensuite le même enchaînement que staging, suivi d'un smoke test double (frontend + API). En cas d'échec, le **rollback automatique** checkout le SHA sauvegardé et relance `docker compose up`.

> **Note :** L'approbation manuelle est configurée dans **Settings → Environments → production** sur GitHub. Ajouter les reviewers autorisés et optionnellement un délai d'attente minimum.

---

### Job 13 — Notification Slack

**Dépend de :** `deploy-staging` + `deploy-production`  
**Condition :** `always()` — s'exécute même en cas d'échec

Le job détermine le statut global du pipeline et envoie une notification Slack avec les informations clés : environnement déployé, branche, auteur, SHA du commit et lien direct vers le run GitHub Actions.

| Résultat | Emoji | Couleur Slack |
|---|---|---|
| Production déployée | ✅ | Vert |
| Staging déployé | 🚀 | Vert |
| Échec | 🔴 | Rouge |

---

## 6. Secrets à configurer

À créer dans **GitHub → Settings → Secrets and variables → Actions** :

### Secrets serveur Staging

| Secret | Description | Exemple |
|---|---|---|
| `STAGING_HOST` | IP ou hostname du serveur | `192.168.1.50` |
| `STAGING_SSH_USER` | Utilisateur SSH | `deploy` |
| `STAGING_SSH_KEY` | Contenu de la clé privée SSH | `-----BEGIN OPENSSH...` |
| `STAGING_SSH_PORT` | Port SSH (optionnel, défaut : 22) | `22` |
| `STAGING_DEPLOY_PATH` | Répertoire du projet sur le serveur | `/opt/mmotors/staging` |

### Secrets serveur Production

| Secret | Description |
|---|---|
| `PROD_HOST` | IP ou hostname du serveur de production |
| `PROD_SSH_USER` | Utilisateur SSH |
| `PROD_SSH_KEY` | Clé privée SSH |
| `PROD_SSH_PORT` | Port SSH (optionnel) |
| `PROD_DEPLOY_PATH` | Répertoire de déploiement |

### Secrets applicatifs

| Secret | Description |
|---|---|
| `GHCR_TOKEN` | Personal Access Token GitHub avec scope `read:packages` |
| `SONAR_TOKEN` | Token d'authentification SonarCloud |
| `SLACK_WEBHOOK_URL` | URL du webhook Slack entrant (optionnel) |

### Générer la paire de clés SSH pour le déploiement

```bash
# Sur la machine locale
ssh-keygen -t ed25519 -C "github-actions-mmotors" -f ~/.ssh/mmotors_deploy

# Copier la clé publique sur le serveur cible
ssh-copy-id -i ~/.ssh/mmotors_deploy.pub deploy@<STAGING_HOST>

# Copier le contenu de la clé privée dans le secret GitHub
cat ~/.ssh/mmotors_deploy
```

---

## 7. Fichiers requis côté serveur

Les fichiers suivants doivent être présents manuellement sur chaque serveur — ils ne transitent **jamais** par Git pour des raisons de sécurité.

### Structure attendue

```
/opt/mmotors/staging/
├── .env.staging              ← variables d'environnement staging
├── docker-compose.yml        ← composition de base (commune)
├── docker-compose.staging.yml ← override staging (ports, replicas, IMAGE_TAG)
└── backups/                  ← créé automatiquement par le pipeline

/opt/mmotors/production/
├── .env.production           ← variables d'environnement production
├── docker-compose.yml
├── docker-compose.production.yml ← override production
└── backups/
```

### Exemple de `docker-compose.staging.yml`

```yaml
services:
  frontend:
    image: ghcr.io/<owner>/mmotors-frontend:${IMAGE_TAG:-develop}
    ports:
      - "3000:3000"

  backend:
    image: ghcr.io/<owner>/mmotors-backend:${IMAGE_TAG:-develop}
    ports:
      - "8000:8000"
    environment:
      - ENV=staging
```

### Exemple de `.env.staging`

```dotenv
DATABASE_URL=postgresql+asyncpg://mmotors:password@postgres:5432/mmotors
REDIS_URL=redis://redis:6379/0
SECRET_KEY=<clé-secrète-staging>
NEXT_PUBLIC_API_URL=http://192.168.1.50:8000
```

---

## 8. Stratégie de branches

```
feature/*  ──┐
             ├──► develop  ──► [CI + deploy staging + E2E]  ──► main  ──► [CI + deploy prod]
fix/*      ──┘
```

| Branche | CI | Deploy | Tests E2E |
|---|---|---|---|
| `feature/*` | ✅ sur PR vers `develop` | ✗ | ✗ |
| `develop` | ✅ | Staging automatique | ✅ sur staging |
| `main` | ✅ | Production (approbation) | ✅ requis avant prod |

---

## 9. Rollback

### Rollback automatique (production uniquement)

Si le smoke test post-déploiement échoue, le job `deploy-production` déclenche automatiquement un rollback vers le SHA Git précédent :

```bash
git checkout $(cat .last-stable-sha)
docker compose up -d --remove-orphans --wait
```

### Rollback manuel

En cas de problème détecté après le passage du smoke test, se connecter en SSH et exécuter :

```bash
cd /opt/mmotors/production

# Voir les versions disponibles
git log --oneline -10

# Revenir à un commit précis
git checkout <sha>
IMAGE_TAG=sha-<short-sha> docker compose -f docker-compose.yml \
  -f docker-compose.production.yml up -d --wait

# Restaurer la base de données si nécessaire
docker compose exec -T postgres \
  psql -U mmotors mmotors < backups/mmotors_<timestamp>.sql
```

---

## 10. Critères de qualité (DoD)

Le pipeline enforce automatiquement les critères de **Definition of Done** définis dans le CDC M-Motors :

| Critère DoD | Mécanisme dans le pipeline |
|---|---|
| Code reviewé | PR obligatoire vers `main`/`develop` (branch protection) |
| Tests unitaires ≥ 80 % de couverture | `--cov-fail-under=80` dans Pytest |
| Tests d'intégration | Job 5 bloquant avec PostgreSQL + Redis réels |
| Validation CI/CD verte | Tous les jobs en amont doivent être `success` |
| Déploiement staging validé | Job 10 + smoke test avant prod |
| Tests E2E passants | Job 11 Playwright bloquant avant déploiement prod |
| Analyse sécurité | Bandit (SAST) + Trivy (images) + SonarQube (quality gate) |
| Pas de vulnérabilité CRITICAL/HIGH | `exit-code: 1` sur Trivy |