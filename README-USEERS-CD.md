# M-Motors — Gestion des utilisateurs Ubuntu pour le déploiement CD

> **Contexte :** Configuration sécurisée des comptes système sur les serveurs de déploiement  
> **OS cible :** Ubuntu 22.04 LTS / 24.04 LTS  
> **Applicable à :** Serveur staging (`217.154.126.103`) · Serveur production  
> **Principe directeur :** Moindre privilège — un utilisateur dédié par application, aucun accès root

---

## Table des matières

1. [Principe fondamental](#1-principe-fondamental)
2. [Création de l'utilisateur système](#2-création-de-lutilisateur-système)
3. [Authentification SSH par clé](#3-authentification-ssh-par-clé)
4. [Durcissement de la configuration SSH](#4-durcissement-de-la-configuration-ssh)
5. [Permissions Docker](#5-permissions-docker)
6. [Permissions sur les répertoires de déploiement](#6-permissions-sur-les-répertoires-de-déploiement)
7. [Restriction des commandes SSH (ForceCommand)](#7-restriction-des-commandes-ssh-forcecommand)
8. [Option avancée — Rootless Docker](#8-option-avancée--rootless-docker)
9. [Intégration avec GitHub Actions](#9-intégration-avec-github-actions)
10. [Vérification et audit](#10-vérification-et-audit)
11. [Récapitulatif des règles](#11-récapitulatif-des-règles)

---

## 1. Principe fondamental

Ne jamais utiliser le compte `root` ni un compte personnel pour les opérations de déploiement automatisé. Un pipeline CD (GitHub Actions, GitLab CI, Jenkins…) qui se connecte à un serveur doit le faire via un **compte système dédié**, sans droits superutilisateur, dont le périmètre d'action est strictement limité au répertoire de l'application.

Ce principe repose sur trois règles :

- **Isolation** — les actions du pipeline n'affectent que l'application concernée, pas le reste du système
- **Traçabilité** — les logs système (`/var/log/auth.log`) identifient clairement les connexions du pipeline
- **Limitation des dégâts** — en cas de compromission de la clé SSH ou du pipeline, l'attaquant ne dispose que des droits de l'utilisateur de déploiement

```
❌ À ne jamais faire          ✅ Bonne pratique
─────────────────────         ──────────────────────────────
root                          deploy-mmotors  (compte système)
ubuntu (compte par défaut)    UID < 1000, shell bash restreint
compte personnel d'un dev     clé SSH dédiée au pipeline
```

---

## 2. Création de l'utilisateur système

### Commande de création

```bash
sudo useradd \
  --system \
  --create-home \
  --home-dir /opt/mmotors \
  --shell /bin/bash \
  --comment "M-Motors CD deploy user" \
  deploy-mmotors
```

### Explication des options

| Option | Valeur | Rôle |
|---|---|---|
| `--system` | — | Attribue un UID < 1000, identifie le compte comme service |
| `--create-home` | — | Crée le répertoire home s'il n'existe pas |
| `--home-dir` | `/opt/mmotors` | Home = répertoire de déploiement (pas `/home/deploy-mmotors`) |
| `--shell` | `/bin/bash` | Shell nécessaire pour exécuter les scripts de déploiement |
| `--comment` | description | Documenté dans `/etc/passwd` pour la lisibilité |

### Pourquoi `--system` ?

Un compte système (UID < 1000) est exclu de certaines politiques PAM appliquées aux comptes humains (expiration de mot de passe, restrictions de connexion interactive, etc.). Il signale également clairement dans les outils d'administration (`getent passwd`, `who`, `last`) que ce compte n'est pas un utilisateur humain.

### Désactiver le mot de passe

Un compte de déploiement n'a pas besoin de mot de passe — l'authentification se fait exclusivement par clé SSH.

```bash
# Verrouiller le mot de passe (empêche toute auth par mot de passe)
sudo passwd --lock deploy-mmotors

# Vérifier
sudo passwd --status deploy-mmotors
# → deploy-mmotors L ... (L = Locked)
```

---

## 3. Authentification SSH par clé

### Générer la paire de clés (sur la machine locale ou dans GitHub Actions)

```bash
# Générer une clé Ed25519 dédiée au pipeline M-Motors
ssh-keygen -t ed25519 \
           -C "github-actions-mmotors-deploy" \
           -f ~/.ssh/mmotors_deploy \
           -N ""   # pas de passphrase (automatisation)

# Deux fichiers sont créés :
# ~/.ssh/mmotors_deploy      → clé PRIVÉE  (→ secret GitHub)
# ~/.ssh/mmotors_deploy.pub  → clé PUBLIQUE (→ serveur)
```

> **Important :** Ne jamais committer la clé privée dans le repository. Elle doit uniquement exister dans les secrets GitHub Actions (`STAGING_SSH_KEY`, `PROD_SSH_KEY`).

### Déposer la clé publique sur le serveur

```bash
# Créer le répertoire .ssh avec les bonnes permissions
sudo mkdir -p /opt/mmotors/.ssh
sudo chmod 700 /opt/mmotors/.ssh

# Copier la clé publique
sudo tee /opt/mmotors/.ssh/authorized_keys <<EOF
$(cat ~/.ssh/mmotors_deploy.pub)
EOF

# Appliquer les permissions strictes requises par SSH
sudo chmod 600 /opt/mmotors/.ssh/authorized_keys
sudo chown -R deploy-mmotors:deploy-mmotors /opt/mmotors/.ssh
```

### Vérifier les permissions (SSH refuse de fonctionner si trop permissives)

```bash
stat /opt/mmotors/.ssh
# → Access: (0700/drwx------) Uid: (deploy-mmotors)

stat /opt/mmotors/.ssh/authorized_keys
# → Access: (0600/-rw-------) Uid: (deploy-mmotors)
```

### Tester la connexion depuis la machine locale

```bash
ssh -i ~/.ssh/mmotors_deploy \
    -o StrictHostKeyChecking=no \
    deploy-mmotors@<STAGING_HOST> \
    "echo 'Connexion OK'"
```

---

## 4. Durcissement de la configuration SSH

Éditer `/etc/ssh/sshd_config` pour renforcer la sécurité du serveur :

```bash
sudo nano /etc/ssh/sshd_config
```

### Paramètres à vérifier ou ajouter

```sshd_config
# Désactiver l'authentification par mot de passe (vecteur d'attaque principal)
PasswordAuthentication no
ChallengeResponseAuthentication no
KbdInteractiveAuthentication no

# Interdire la connexion directe en root
PermitRootLogin no

# Activer l'authentification par clé publique
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys

# Restreindre les protocoles et algorithmes
Protocol 2
KexAlgorithms curve25519-sha256,diffie-hellman-group14-sha256
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com
MACs hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com

# Délai de connexion et tentatives
LoginGraceTime 30
MaxAuthTries 3
MaxSessions 5

# Désactiver les fonctionnalités non nécessaires
X11Forwarding no
AllowAgentForwarding no
AllowTcpForwarding no
PrintMotd no
```

### Appliquer la configuration

```bash
# Vérifier la syntaxe avant de recharger (évite de se couper l'accès)
sudo sshd -t && echo "Configuration valide"

# Recharger le service
sudo systemctl reload sshd
```

> **Attention :** Avant de désactiver `PasswordAuthentication`, s'assurer que la connexion par clé fonctionne depuis une autre session SSH ouverte. Ne pas fermer la session actuelle tant que ce n'est pas validé.

---

## 5. Permissions Docker

### Ajouter l'utilisateur au groupe docker

```bash
sudo usermod -aG docker deploy-mmotors

# Vérifier
groups deploy-mmotors
# → deploy-mmotors : deploy-mmotors docker
```

L'appartenance au groupe `docker` permet d'exécuter `docker` et `docker compose` sans `sudo`, ce qui est nécessaire pour les scripts de déploiement automatisés.

### Risque connu et accepté

> ⚠️ **Appartenir au groupe `docker` est équivalent à avoir les droits `root`** sur la machine hôte. Un container peut en effet monter `/etc/` en écriture, modifier les fichiers système ou créer un container privilégié.
>
> Ce risque est **acceptable** dans les conditions suivantes :
> - Le serveur est dédié au déploiement de l'application M-Motors
> - La clé SSH est protégée (stockée uniquement dans les secrets GitHub, jamais commitée)
> - Aucun autre utilisateur non fiable n'a accès au serveur
>
> Si ces conditions ne sont pas réunies, utiliser **Rootless Docker** (section 8).

### Appliquer le nouveau groupe sans redémarrage

Le changement de groupe est effectif à la prochaine connexion SSH. Pour l'appliquer immédiatement dans une session existante :

```bash
sudo -u deploy-mmotors newgrp docker
```

---

## 6. Permissions sur les répertoires de déploiement

### Créer la structure de répertoires

```bash
sudo mkdir -p \
  /opt/mmotors/staging/backups \
  /opt/mmotors/production/backups

# Attribuer la propriété complète à l'utilisateur de déploiement
sudo chown -R deploy-mmotors:deploy-mmotors /opt/mmotors/

# Permissions : rwxr-x--- (propriétaire full, groupe lecture, autres rien)
sudo chmod -R 750 /opt/mmotors/
```

### Structure attendue après configuration

```
/opt/mmotors/                          ← home de deploy-mmotors
├── .ssh/
│   └── authorized_keys               (600)
├── staging/
│   ├── .env.staging                  ← jamais dans Git
│   ├── docker-compose.yml
│   ├── docker-compose.staging.yml
│   ├── .last-stable-sha              ← écrit par le pipeline
│   └── backups/
│       └── mmotors_20260501_143022.sql
└── production/
    ├── .env.production               ← jamais dans Git
    ├── docker-compose.yml
    ├── docker-compose.production.yml
    ├── .last-stable-sha
    └── backups/
```

### Ne pas étendre les permissions au-delà de /opt/mmotors

```bash
# Vérifier que deploy-mmotors ne peut pas écrire ailleurs
sudo -u deploy-mmotors touch /etc/test 2>&1
# → touch: cannot touch '/etc/test': Permission denied ✅

sudo -u deploy-mmotors touch /var/test 2>&1
# → touch: cannot touch '/var/test': Permission denied ✅
```

---

## 7. Restriction des commandes SSH (ForceCommand)

Pour les environnements à haute sensibilité, il est possible d'interdire tout shell interactif et de n'autoriser que l'exécution d'un script de déploiement prédéfini.

### Créer le script de déploiement

```bash
sudo mkdir -p /opt/mmotors/scripts
sudo tee /opt/mmotors/scripts/deploy.sh <<'EOF'
#!/bin/bash
# Script de déploiement autorisé pour deploy-mmotors
# Seules les commandes ci-dessous peuvent être exécutées via SSH

set -euo pipefail

case "${1:-}" in
  staging)
    cd /opt/mmotors/staging
    docker compose -f docker-compose.yml -f docker-compose.staging.yml pull
    docker compose -f docker-compose.yml -f docker-compose.staging.yml up -d --wait
    ;;
  production)
    cd /opt/mmotors/production
    docker compose -f docker-compose.yml -f docker-compose.production.yml pull
    docker compose -f docker-compose.yml -f docker-compose.production.yml up -d --wait
    ;;
  *)
    echo "Usage: deploy.sh [staging|production]" >&2
    exit 1
    ;;
esac
EOF

sudo chmod 750 /opt/mmotors/scripts/deploy.sh
sudo chown deploy-mmotors:deploy-mmotors /opt/mmotors/scripts/deploy.sh
```

### Appliquer ForceCommand dans sshd_config

```sshd_config
Match User deploy-mmotors
    ForceCommand /opt/mmotors/scripts/deploy.sh
    AllowTcpForwarding no
    X11Forwarding no
    PermitTTY no
```

> **Note pour M-Motors :** Le workflow GitHub Actions actuel exécute plusieurs commandes dans une même session SSH (git pull, alembic, docker compose…). `ForceCommand` est incompatible avec cette approche sans réécrire le script de déploiement. À considérer pour une phase ultérieure de durcissement.

---

## 8. Option avancée — Rootless Docker

Rootless Docker fait tourner le daemon Docker sous l'UID de l'utilisateur, sans aucun accès root sur l'hôte. C'est la meilleure pratique pour la production sérieuse ou les serveurs multi-locataires.

### Prérequis

```bash
# Installer les paquets requis
sudo apt install -y docker-ce-rootless-extras uidmap

# Vérifier que l'utilisateur a des plages uid/gid subordonnées
grep deploy-mmotors /etc/subuid /etc/subgid
# Si absent, les créer :
sudo usermod --add-subuids 100000-165535 deploy-mmotors
sudo usermod --add-subgids 100000-165535 deploy-mmotors
```

### Installation du mode rootless

```bash
# Activer le linger (permet au daemon de tourner sans session active)
sudo loginctl enable-linger deploy-mmotors

# Basculer vers l'utilisateur de déploiement
sudo -u deploy-mmotors bash --login

# Installer Docker rootless
dockerd-rootless-setuptool.sh install

# Configurer les variables d'environnement dans le shell de deploy-mmotors
echo 'export DOCKER_HOST=unix:///run/user/$(id -u)/docker.sock' \
  >> /opt/mmotors/.bashrc
echo 'export PATH=$HOME/bin:$PATH' \
  >> /opt/mmotors/.bashrc

# Quitter et tester
exit
sudo -u deploy-mmotors docker info
```

### Comparaison groupe docker vs rootless

| Critère | Groupe `docker` | Rootless Docker |
|---|---|---|
| Complexité de mise en place | Faible | Moyenne |
| Risque d'escalade de privilèges | Élevé (équiv. root) | Aucun |
| Compatibilité `docker compose` | Totale | Totale |
| Ports < 1024 accessibles | Oui | Non (sauf `sysctl`) |
| Recommandé pour | Dev / staging local | Production |
| Contexte M-Motors | Phase initiale ✅ | Phase production ✅ |

---

## 9. Intégration avec GitHub Actions

### Correspondance secrets GitHub ↔ configuration serveur

| Secret GitHub | Valeur à renseigner |
|---|---|
| `STAGING_SSH_USER` | `deploy-mmotors` |
| `STAGING_SSH_KEY` | Contenu de `~/.ssh/mmotors_deploy` (clé privée) |
| `STAGING_HOST` | IP ou hostname du serveur staging |
| `STAGING_SSH_PORT` | `22` (ou port personnalisé) |
| `STAGING_DEPLOY_PATH` | `/opt/mmotors/staging` |
| `PROD_SSH_USER` | `deploy-mmotors` |
| `PROD_SSH_KEY` | Clé privée dédiée production (générer une paire séparée) |
| `PROD_HOST` | IP ou hostname du serveur production |
| `PROD_DEPLOY_PATH` | `/opt/mmotors/production` |

> **Bonne pratique :** Générer des paires de clés **distinctes** pour staging et production. En cas de compromission de la clé staging, la production reste protégée.

### Vérifier la connexion depuis le runner GitHub Actions

Ajouter temporairement ce job de diagnostic dans le workflow :

```yaml
test-ssh:
  runs-on: ubuntu-latest
  steps:
    - name: Test connexion SSH staging
      uses: appleboy/ssh-action@v1
      with:
        host:     ${{ secrets.STAGING_HOST }}
        username: ${{ secrets.STAGING_SSH_USER }}
        key:      ${{ secrets.STAGING_SSH_KEY }}
        script:   |
          whoami
          pwd
          docker info | grep "Server Version"
          ls /opt/mmotors/staging/
```

---

## 10. Vérification et audit

### Contrôles post-configuration

```bash
# 1. Vérifier l'utilisateur dans /etc/passwd
getent passwd deploy-mmotors
# → deploy-mmotors:x:999:999:M-Motors CD deploy user:/opt/mmotors:/bin/bash

# 2. Vérifier le verrouillage du mot de passe
sudo passwd --status deploy-mmotors
# → deploy-mmotors L ... (L = Locked)

# 3. Vérifier l'appartenance au groupe docker
groups deploy-mmotors
# → deploy-mmotors : deploy-mmotors docker

# 4. Vérifier les permissions SSH
stat /opt/mmotors/.ssh /opt/mmotors/.ssh/authorized_keys

# 5. Vérifier que docker fonctionne sans sudo
sudo -u deploy-mmotors docker ps

# 6. Vérifier l'isolation système
sudo -u deploy-mmotors ls /root 2>&1
# → ls: cannot open directory '/root': Permission denied ✅
```

### Surveiller les connexions du pipeline

```bash
# Connexions SSH récentes de l'utilisateur de déploiement
sudo grep "deploy-mmotors" /var/log/auth.log | tail -20

# Dernières connexions
last deploy-mmotors

# Sessions actives
who | grep deploy-mmotors
```

### Rotation des clés SSH

Il est recommandé de faire tourner les clés SSH tous les 6 à 12 mois ou immédiatement en cas de départ d'un membre de l'équipe ayant eu accès aux secrets GitHub :

```bash
# 1. Générer une nouvelle paire de clés
ssh-keygen -t ed25519 -C "github-actions-mmotors-deploy-v2" \
           -f ~/.ssh/mmotors_deploy_v2 -N ""

# 2. Ajouter la nouvelle clé publique au serveur (sans supprimer l'ancienne)
sudo tee -a /opt/mmotors/.ssh/authorized_keys <<EOF
$(cat ~/.ssh/mmotors_deploy_v2.pub)
EOF

# 3. Mettre à jour le secret GitHub avec la nouvelle clé privée
# (Settings → Secrets → STAGING_SSH_KEY → Update)

# 4. Tester la nouvelle clé via le pipeline

# 5. Supprimer l'ancienne clé du authorized_keys une fois validé
sudo nano /opt/mmotors/.ssh/authorized_keys
```

---

## 11. Récapitulatif des règles

| Règle | Commande / Paramètre | Raison |
|---|---|---|
| Compte système dédié | `useradd --system` | Isolation, UID < 1000, hors politiques PAM humaines |
| Pas de mot de passe | `passwd --lock` | Supprime l'auth par mot de passe |
| Clé SSH Ed25519 | `ssh-keygen -t ed25519` | Algorithme moderne, résistant aux attaques brute-force |
| Permissions `.ssh` strictes | `chmod 700 .ssh` / `600 authorized_keys` | Requis par SSH, refus de connexion sinon |
| `PasswordAuthentication no` | `/etc/ssh/sshd_config` | Supprime le principal vecteur d'attaque SSH |
| `PermitRootLogin no` | `/etc/ssh/sshd_config` | Interdit la connexion directe en root |
| Groupe `docker` sans sudo | `usermod -aG docker` | Moindre privilège — pas de sudo ouvert |
| Home = répertoire applicatif | `--home-dir /opt/mmotors` | Contient le périmètre d'action au répertoire de l'app |
| Isolation système vérifiée | `sudo -u deploy-mmotors ls /root` | Valider l'impossibilité d'accéder aux zones système |
| Clés distinctes par environnement | Deux paires staging / prod | Compromission staging n'affecte pas la production |
| Rotation des clés | Tous les 6-12 mois | Limite la fenêtre d'exposition en cas de fuite |
| Rootless Docker en prod critique | `dockerd-rootless-setuptool.sh` | Élimine le risque d'escalade de privilèges root |