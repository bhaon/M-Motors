# M-Motors — Documentation du pipeline CI/CD

> **Fichier :** `.github/workflows/m-motors-CICD.yaml`  
> **Stack :** Next.js · FastAPI/Python · PostgreSQL · Redis  
> **Registry :** GitHub Container Registry (GHCR)  
> **Déploiement :** (optionnel) Docker Compose via SSH — jobs de déploiement actuellement **commentés** dans le workflow

---

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Déclencheurs et entrées manuelles](#2-déclencheurs-et-entrées-manuelles)
3. [Variables globales et configuration](#3-variables-globales-et-configuration)
4. [Concurrence](#4-concurrence)
5. [Schéma du pipeline](#5-schéma-du-pipeline)
6. [Description détaillée des jobs](#6-description-détaillée-des-jobs)
7. [Jobs désactivés (template dans le YAML)](#7-jobs-désactivés-template-dans-le-yaml)
8. [Secrets et variables à configurer](#8-secrets-et-variables-à-configurer)
9. [Fichiers requis côté serveur](#9-fichiers-requis-côté-serveur)
10. [Stratégie de branches](#10-stratégie-de-branches)
11. [Rollback](#11-rollback)
12. [Critères de qualité (DoD)](#12-critères-de-qualité-dod)

---

## 1. Vue d'ensemble

Le pipeline automatise la qualité du code (lint, tests, analyse), la construction des images Docker et leur publication sur **GHCR**, puis un **scan Trivy** des images et une **notification Slack** en fin de run.

Les jobs de **déploiement SSH** (staging / production) et de **tests E2E Playwright** sont **présents en commentaires** dans le YAML : ils servent de modèle à réactiver quand l’infrastructure est prête. Tant qu’ils restent commentés, seul le parcours **CI + build + scan** s’exécute.

**Ordre logique :** test SSH (optionnel de confiance) → détection des changements → lint / tests (selon chemins + `skip_tests`) → build Next → SonarCloud → build & push images → Trivy → Slack.

---

## 2. Déclencheurs et entrées manuelles

| Source | Comportement actuel (fichier YAML) |
|--------|------------------------------------|
| `workflow_dispatch` | **Seul déclencheur actif** — lancement manuel depuis l’onglet *Actions* de GitHub. |
| `push` / `pull_request` | **Commentés** dans le workflow. Pour activer la CI sur chaque push, décommenter la section `on:` en tête de fichier (et ajuster `paths-ignore` si besoin). |

### Entrées `workflow_dispatch`

| Entrée | Type | Défaut | Rôle |
|--------|------|--------|------|
| `environment` | choix | `staging` | Cible documentaire (`staging` \| `production`) — utile quand les jobs de déploiement seront réactivés. |
| `skip_tests` | booléen | `false` | Si `true`, les jobs `test-backend-unit`, `test-backend-integration` et `test-frontend-unit` sont **ignorés** (urgence uniquement). |

> Les fichiers `**.md`, `.gitignore` et `docs/**` étaient prévus en `paths-ignore` sur `push` — actuellement sans effet tant que le `push` reste commenté.

---

## 3. Variables globales et configuration

| Variable | Valeur / source | Rôle |
|----------|-----------------|------|
| `REGISTRY` | `ghcr.io` | Registry des images. |
| `IMAGE_FRONTEND` | `ghcr.io/${{ github.repository_owner }}/mmotors-frontend` | Nom de l’image frontend. |
| `IMAGE_BACKEND` | `ghcr.io/${{ github.repository_owner }}/mmotors-backend` | Nom de l’image backend. |
| `SONAR_PROJECT_KEY` | `vars.SONAR_PROJECT_KEY` ou défaut `mmotors` | Clé projet SonarCloud. |
| `SONAR_ORGANIZATION` | `vars.SONAR_ORGANIZATION` ou `github.repository_owner` | Organisation SonarCloud. |
| `NODE_VERSION` | `22` | Node.js (lint, tests, build frontend). |
| `PYTHON_VERSION` | `3.12` | Python (lint, tests backend). |

---

## 4. Concurrence

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

Un nouveau run sur la même branche **annule** le run précédent encore en cours, pour éviter des déploiements ou images qui se chevauchent.

---

## 5. Schéma du pipeline

```
  test-ssh-staging (optionnel)
           │
  ┌────────▼────────┐
  │     changes     │  paths-filter (frontend / backend / compose)
  └────────┬────────┘
           ├──────────────────────┬──────────────────────┐
  ┌────────▼────────┐   ┌────────▼────────┐   (si skip_tests: certains tests sautés)
  │ lint-frontend   │   │  lint-backend   │
  └────────┬────────┘   └────────┬────────┘
  ┌────────▼────────┐   ┌────────┴────────┬───────────────────┐
  │test-frontend    │   │test-backend     │  test-backend     │
  │    -unit        │   │   -unit         │  -integration     │
  └────────┬────────┘   └────────┬────────┘  (PG + Redis)     │
           │           ┌─────────┴─────────┬──────────────────┘
  ┌────────▼────────┐  │  sonarqube (SAST) │  (rapports couverture)
  │ build-frontend  │  └─────────┬─────────┘
  │  (next build) │              │
  └────────┬────────┘            │
           └──────────┬──────────┘
                      ▼
              ┌───────────────┐
              │ build-images  │  Docker build + push GHCR (branches / dispatch)
              └───────┬───────┘
                      ▼
              ┌───────────────┐
              │  trivy-scan   │  SARIF → Security tab (exit-code 0)
              └───────┬───────┘
                      ▼
              ┌───────────────┐
              │    notify     │  Slack (résultat Trivy / fin de pipeline)
              └───────────────┘
```

Les blocs **déploiement staging**, **E2E**, **déploiement production** ne figurent pas dans ce schéma tant qu’ils restent commentés dans le YAML (voir [§7](#7-jobs-désactivés-template-dans-le-yaml)).

---

## 6. Description détaillée des jobs

### Job 0 — Test SSH Connection Staging (`test-ssh-staging`)

- **But :** Vérifier que le runner peut joindre le serveur staging (clé SSH, chemin de déploiement).
- **Étapes :** extraction du **hostname** depuis la variable de dépôt `STAGING_URL` (script Python + `urllib`), puis `appleboy/ssh-action` (`whoami`, `docker info`, `ls /opt/mmotors/staging/`).
- **Prérequis :** `STAGING_URL`, `STAGING_SSH_USER`, `STAGING_SSH_KEY`.

---

### Job 1 — Détection des changements (`changes`)

- **Action :** `dorny/paths-filter@v3`
- **Filtres :**
  - `frontend` : `frontend/**`
  - `backend` : `backend/**`, `requirements*.txt`, `alembic/**`
  - `compose` : `docker-compose*.yml`, `.env.example`, `.github/workflows/**`

Les jobs de lint ne s’exécutent que si le bon filtre est à `true`, **sauf** sur `workflow_dispatch` où le lint frontend/backend tourne toujours (`if` avec `github.event_name == 'workflow_dispatch'`).

---

### Job 2 — Lint Frontend (`lint-frontend`)

- **Condition :** `frontend == true` **ou** `workflow_dispatch`
- **Répertoire :** `frontend/`
- **Étapes :** `npm ci` → `npm run type-check` (`tsc --noEmit`) → `npm run lint` → `npm run format:check` (Prettier)

---

### Job 3 — Lint Backend (`lint-backend`)

- **Condition :** `backend == true` **ou** `workflow_dispatch`
- **Env :** `DATABASE_URL` et `SECRET_KEY` (valeurs factices CI) pour permettre l’import de `app.core.config` (notamment pour Mypy).
- **Étapes :** `pip install -r requirements-dev.txt` → **Ruff** (`check` + `format --check`) → **Mypy** (`mypy -p app --ignore-missing-imports --explicit-package-bases`) → **Bandit** (rapport JSON, `continue-on-error: true`, artefact `bandit-report` 14 jours)

---

### Job 4 — Tests unitaires Backend (`test-backend-unit`)

- **Dépend de :** `lint-backend`
- **Condition :** `skip_tests` est faux
- **Base :** SQLite fichier (`DATABASE_URL=sqlite:///./test.db`)
- **Commande :** `pytest tests/unit/` avec couverture `--cov=app`, `--cov-fail-under=80`, JUnit XML
- **Artefacts :** `pytest-unit-results.xml`, `coverage.xml`

---

### Job 5 — Tests d’intégration Backend (`test-backend-integration`)

- **Dépend de :** `lint-backend` (en **parallèle** du job 4 après lint)
- **Condition :** `skip_tests` est faux
- **Services :** PostgreSQL 16 + Redis 7 (ports exposés, healthchecks)
- **Étapes :** `alembic upgrade head` puis `pytest tests/integration/` (timeout 60 s par test via pytest-timeout)
- **Artefact :** `pytest-integration-results.xml`

---

### Job 6 — Tests unitaires Frontend (`test-frontend-unit`)

- **Dépend de :** `lint-frontend`
- **Condition :** `skip_tests` est faux
- **Commande :** `npm run test:ci` (Jest + couverture `lcov`)
- **Artefact :** `frontend/coverage/lcov.info`

---

### Job 7 — Build Frontend (`build-frontend`)

- **Dépend de :** `lint-frontend` **et** `test-frontend-unit`
- **Condition :** `always() && !failure() && !cancelled()` — le build peut tourner si les jobs requis se terminent sans échec « dur » (voir comportement GitHub sur les dépendances `skipped`).
- **Commande :** `npm run build`
- **Env :** `NODE_ENV=production`, `NEXT_PUBLIC_APP_ENV` = `production` si branche `main`, sinon `staging`

---

### Job 8 — Analyse SonarQube / SonarCloud (`sonarqube`)

- **Dépend de :** `test-backend-unit` **et** `test-frontend-unit`
- **Condition :** `always() && !cancelled()`
- **Checkout :** `fetch-depth: 0` pour l’historique
- **Artefacts :** télécharge `pytest-unit-results` et `frontend-coverage` (`continue-on-error: true` si absents)
- **Si `secrets.SONAR_TOKEN` est absent :** l’analyse Sonar est **ignorée** (step conditionnelle `sonar-config`)
- **Action :** `SonarSource/sonarcloud-github-action@master` avec sources `frontend/src`, `backend/app`, rapports de couverture Python/JS, **quality gate** en attente (`-Dsonar.qualitygate.wait=true`)

---

### Job 9 — Build & Push images Docker (`build-images`)

- **Dépend de :** `build-frontend`, `test-backend-integration`, `sonarqube`
- **Condition :** succès global (`always() && !failure() && !cancelled()`) **et** (`main` **ou** `develop` **ou** `workflow_dispatch`)
- **Permissions :** `packages: write`, `actions: read`
- **Étapes :** calcul `short-sha` → `docker/setup-buildx-action` → login GHCR (`GITHUB_TOKEN`) → **metadata-action** (tags branche + `sha-<short>` + `latest` si `main`) → **build-push-action** avec cache **GHA** (`cache-from` / `cache-to`), contextes `./frontend` et `./backend`

> Il n’y a **pas** de build multi-plateforme explicite (`linux/arm64`) dans le workflow actuel — images construites pour l’architecture du runner (amd64 par défaut).

---

### Job 10 — Scan Trivy (`trivy-scan`)

- **Dépend de :** `build-images`
- **Images scannées :** `${IMAGE_FRONTEND}:sha-<short-sha>` et `${IMAGE_BACKEND}:sha-<short-sha>`
- **Gravité :** CRITICAL, HIGH — **`exit-code: "0"`** : le scan **ne fait pas échouer** le job sur présence de vulnérabilités ; les résultats sont remontés en **SARIF** vers l’onglet **Security / Code scanning** (`upload-sarif`).
- **Cache :** base de données Trivy via `actions/cache`

---

### Job 11 — Notification Slack (`notify`)

- **Dépend de :** `trivy-scan`
- **Condition :** `always()`
- **Logique :** message vert si `trivy-scan` est en succès, sinon message d’échec (le pipeline CI/images/Trivy est la référence tant que les jobs de déploiement sont commentés).
- **Secret :** `SLACK_WEBHOOK_URL` (webhook entrant Slack)

---

## 7. Jobs désactivés (template dans le YAML)

Les blocs suivants sont **entièrement commentés** dans `m-motors-CICD.yaml` ; ils documentent la cible produit (à décommenter progressivement) :

| Bloc commenté | Rôle prévu |
|---------------|------------|
| `deploy-staging` | SSH vers serveur staging, `git pull`, `.env.staging`, login GHCR, `docker compose pull`, `alembic upgrade head`, `up -d --wait`, smoke `curl` sur `/api/health` |
| `test-e2e` | Playwright contre `vars.STAGING_URL`, après déploiement staging |
| `deploy-production` | SSH prod, sauvegarde PostgreSQL, déploiement, smoke tests, rollback automatique sur échec |

Pour réactiver la chaîne complète : décommenter ces jobs, ajuster les `needs` (ex. `notify` pourrait à nouveau dépendre de `deploy-staging` / `deploy-production`) et vérifier les secrets serveur.

---

## 8. Secrets et variables à configurer

### Variables de dépôt (*Settings → Secrets and variables → Actions → Variables*)

| Variable | Description |
|----------|-------------|
| `STAGING_URL` | URL de base de l’app staging (smoke tests, Playwright, extraction hostname SSH) |
| `PRODUCTION_URL` | URL de base en production |
| `SONAR_PROJECT_KEY` | (optionnel) Clé projet SonarCloud |
| `SONAR_ORGANIZATION` | (optionnel) Organisation SonarCloud |

### Secrets

| Secret | Usage dans le workflow actif |
|--------|------------------------------|
| `GITHUB_TOKEN` | Fourni par GitHub — push GHCR, Trivy login |
| `SONAR_TOKEN` | Analyse SonarCloud (sinon analyse sautée) |
| `STAGING_SSH_USER`, `STAGING_SSH_KEY` | Job `test-ssh-staging` (et futurs déploiements) |
| `SLACK_WEBHOOK_URL` | Job `notify` |
| `GHCR_TOKEN` | Prévu pour `docker login` **sur le serveur** dans les jobs de déploiement commentés |

Les secrets `PROD_*`, chemins de déploiement, etc. sont décrits dans les sections commentées du YAML pour la production.

### Génération de clés SSH (pour déploiement futur)

```bash
ssh-keygen -t ed25519 -C "github-actions-mmotors" -f ~/.ssh/mmotors_deploy
ssh-copy-id -i ~/.ssh/mmotors_deploy.pub deploy@<HOST>
cat ~/.ssh/mmotors_deploy   # à coller dans STAGING_SSH_KEY / PROD_SSH_KEY
```

---

## 9. Fichiers requis côté serveur

Inchangé pour une stack Compose déployée par SSH : répertoires `staging` / `production`, fichiers `.env.staging` / `.env.production`, fichiers `docker-compose*.yml`, dossier `backups/` pour les dumps PostgreSQL (voir les scripts commentés dans le workflow pour les commandes exactes).

---

## 10. Stratégie de branches

| Branche / événement | Comportement dans le YAML actuel |
|---------------------|----------------------------------|
| `workflow_dispatch` | CI complète (selon entrées) + build images si branche `main`/`develop` ou déclenchement manuel |
| `main` / `develop` (push) | Non activés tant que `on.push` est commenté |
| Images GHCR | Tags branche + `sha-*` + `latest` sur `main` (voir `metadata-action`) |

---

## 11. Rollback

Les procédures de rollback **automatisées** (production) sont décrites dans le bloc commenté `deploy-production`. En l’absence de déploiement automatisé, rollback manuel : SSH, checkout Git d’un SHA stable, `IMAGE_TAG=sha-… docker compose up -d`, restauration base depuis `backups/` si nécessaire.

---

## 12. Critères de qualité (DoD)

| Critère | Mécanisme dans le workflow |
|---------|----------------------------|
| Couverture backend ≥ 80 % | `pytest --cov-fail-under=80` (job unitaire) |
| Tests d’intégration | PostgreSQL + Redis + Alembic |
| Lint / types | ESLint, TypeScript, Ruff, Mypy |
| Build Next.js | `npm run build` en production |
| SAST application | Bandit (rapport), SonarCloud si token configuré |
| Images | Build + push GHCR, scan Trivy (CRITICAL/HIGH remontés en SARIF, job vert avec `exit-code: 0`) |

---

*Dernière mise à jour : alignée sur `m-motors-CICD.yaml` (jobs actifs, dépendances, entrées manuelles, jobs commentés, Node 22, Trivy séparé, notification Slack après Trivy).*
