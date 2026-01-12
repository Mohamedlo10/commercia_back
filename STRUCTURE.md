# Structure du Projet Commercia Backend

Arborescence complète du projet avec descriptions.

```
commercia/
│
├── 📁 app/                              # Application principale
│   ├── __init__.py                      # Initialisation du package
│   ├── main.py                          # Point d'entrée FastAPI ⭐
│   │
│   ├── 📁 core/                         # Configuration et utils de base
│   │   ├── __init__.py
│   │   ├── config.py                    # Variables d'environnement
│   │   ├── database.py                  # Configuration SQLAlchemy + asyncpg
│   │   └── security.py                  # JWT, hashing, authentification
│   │
│   ├── 📁 models/                       # Modèles SQLAlchemy (ORM)
│   │   ├── __init__.py                  # Exports tous les modèles
│   │   ├── base.py                      # Modèle de base abstrait
│   │   ├── store.py                     # Magasins
│   │   ├── user.py                      # Utilisateurs
│   │   ├── employee.py                  # Employés (RH)
│   │   ├── client.py                    # Clients
│   │   ├── category.py                  # Catégories de produits
│   │   ├── product.py                   # Produits et variantes
│   │   ├── order.py                     # Commandes et articles
│   │   ├── transaction.py               # Transactions et paiements
│   │   ├── stock.py                     # Mouvements de stock
│   │   ├── cash_register.py             # Sessions de caisse
│   │   └── reservation.py               # Réservations/Locations
│   │
│   ├── 📁 schemas/                      # Schémas Pydantic (validation)
│   │   ├── __init__.py
│   │   └── auth.py                      # Schémas d'authentification
│   │
│   └── 📁 api/                          # Routes API
│       ├── __init__.py
│       └── 📁 v1/                       # Version 1 de l'API
│           ├── __init__.py
│           ├── api.py                   # Router principal qui agrège tout
│           └── 📁 endpoints/            # Endpoints par module
│               ├── __init__.py
│               └── auth.py              # Routes d'authentification ✅
│
├── 📁 database/                         # Scripts SQL
│   └── init.sql                         # Script SQL complet ⭐ (20+ tables, 8 triggers)
│
├── 📁 tests/                            # Tests automatisés
│   ├── __init__.py
│   ├── conftest.py                      # Configuration pytest et fixtures
│   └── test_auth.py                     # Tests d'authentification ✅
│
├── 📄 requirements.txt                  # Dépendances Python ✅
├── 📄 Dockerfile                        # Configuration Docker ✅
├── 📄 render.yaml                       # Configuration Render ✅
├── 📄 .env.example                      # Exemple de variables d'environnement ✅
├── 📄 .dockerignore                     # Fichiers ignorés par Docker
├── 📄 .gitignore                        # Fichiers ignorés par Git
├── 📄 pytest.ini                        # Configuration pytest
├── 📄 Makefile                          # Commandes make simplifiées ✅
├── 📄 run.sh                            # Script de démarrage rapide ✅
│
├── 📚 README.md                         # Documentation principale ✅
├── 📚 DEPLOYMENT.md                     # Guide de déploiement détaillé ✅
├── 📚 CHANGELOG.md                      # Historique des versions ✅
├── 📚 STRUCTURE.md                      # Ce fichier
└── 📚 SPECIFICATIONS_TECHNIQUES.md      # Spécifications complètes (déjà existant)
```

## Modules implémentés ✅

### 1. Infrastructure de base
- ✅ FastAPI avec lifespan events
- ✅ SQLAlchemy async avec asyncpg
- ✅ Configuration via Pydantic Settings
- ✅ CORS configuré
- ✅ Middleware de logging
- ✅ Gestionnaire d'erreurs global
- ✅ Health check endpoint

### 2. Sécurité
- ✅ JWT avec python-jose
- ✅ Hashing bcrypt avec passlib
- ✅ HTTPBearer authentication
- ✅ Dépendances de sécurité (get_current_user)
- ✅ Permission checker (préparé)

### 3. Base de données
- ✅ 15 modèles SQLAlchemy avec relations
- ✅ Script SQL complet avec :
  - 20+ tables
  - 8 triggers automatiques
  - Indexes optimisés
  - RLS activé
- ✅ Gestion async des sessions
- ✅ Connection pooling configuré

### 4. API Authentification
- ✅ POST /auth/login
- ✅ POST /auth/register
- ✅ GET /auth/me
- ✅ POST /auth/change-password
- ✅ POST /auth/logout

### 5. Tests
- ✅ Configuration pytest avec fixtures
- ✅ Tests d'authentification complets
- ✅ Base de données de test isolée
- ✅ Client HTTP async pour tests

### 6. Déploiement
- ✅ Dockerfile optimisé
- ✅ Configuration Render (render.yaml)
- ✅ Variables d'environnement documentées
- ✅ Guide de déploiement détaillé

### 7. Outillage
- ✅ Makefile avec 15+ commandes
- ✅ Script run.sh pour démarrage rapide
- ✅ pytest.ini configuré
- ✅ .gitignore et .dockerignore

## Modules à développer 🚧

### Phase 1 : Produits (Semaine 1-2)
- [ ] CRUD Produits
- [ ] CRUD Catégories
- [ ] Gestion des variantes
- [ ] Gestion du stock
- [ ] Import/Export Excel

### Phase 2 : Clients (Semaine 3)
- [ ] CRUD Clients
- [ ] Gestion de la fidélité
- [ ] Gestion des dettes

### Phase 3 : Point de Vente (Semaine 4-5)
- [ ] Création de commande
- [ ] Calcul du panier
- [ ] Application des promos
- [ ] Multi-méthodes de paiement

### Phase 4 : Caisse (Semaine 6)
- [ ] Ouverture/Fermeture session
- [ ] Rapport de caisse
- [ ] Réconciliation

### Phase 5 : Réservations (Semaine 7)
- [ ] CRUD Réservations
- [ ] Gestion des disponibilités
- [ ] Cautions et paiements

### Phase 6-10 : Fonctionnalités avancées
- [ ] Codes promo
- [ ] Retours/Remboursements
- [ ] Module RH
- [ ] Dashboard
- [ ] Rapports
- [ ] Permissions avancées
- [ ] Intégration e-commerce

## Commandes utiles

```bash
# Installation
make install              # Installe les dépendances
make install-dev          # Installe deps + outils dev

# Développement
make dev                  # Démarre en mode dev
./run.sh dev              # Alternative avec run.sh

# Tests
make test                 # Lance les tests
make test-cov             # Tests avec couverture

# Code quality
make format               # Formate avec Black
make lint                 # Vérifie avec flake8
make check                # Tous les checks

# Docker
make docker-build         # Build l'image
make docker-run           # Run le container

# Production
make prod                 # Démarre en mode prod
./run.sh prod             # Alternative avec run.sh

# Nettoyage
make clean                # Nettoie les fichiers temp
```

## Variables d'environnement clés

```env
# Required
DATABASE_URL=postgresql+asyncpg://...    # Connexion Supabase
SECRET_KEY=...                           # Clé JWT (auto-généré sur Render)

# Important
ENVIRONMENT=production                   # development, staging, production
DEBUG=false                              # false en production
BACKEND_CORS_ORIGINS=["https://..."]    # URLs frontend autorisées

# Optionnel
ACCESS_TOKEN_EXPIRE_MINUTES=10080       # 7 jours par défaut
LOYALTY_POINTS_RATE=1000                # 1 point par 1000 XOF
```

## Documentation API

Une fois démarré :
- **Swagger** : http://localhost:8000/api/docs
- **ReDoc** : http://localhost:8000/api/redoc
- **OpenAPI** : http://localhost:8000/api/openapi.json

## Architecture

```
┌─────────────┐
│   Frontend  │  (Vercel - Next.js par Lovable)
│   Vercel    │
└──────┬──────┘
       │ HTTPS + JWT
       ▼
┌─────────────┐
│   Backend   │  (Render - FastAPI par Claude Code) ⭐ VOUS ÊTES ICI
│   FastAPI   │
└──────┬──────┘
       │ PostgreSQL + asyncpg
       ▼
┌─────────────┐
│  Database   │  (Supabase - PostgreSQL)
│  Supabase   │
└─────────────┘
```

## État du projet

- ✅ Infrastructure complète
- ✅ Base de données complète
- ✅ Authentification fonctionnelle
- ✅ Prêt pour le déploiement
- 🚧 Endpoints métier à développer (selon roadmap)

## Prochaines étapes

1. **Déployer sur Render** (suivre DEPLOYMENT.md)
2. **Développer les endpoints Produits**
3. **Développer les endpoints Clients**
4. **Développer le POS**
5. **Intégrer avec le frontend**

---

**Note** : Les fichiers marqués ⭐ sont les plus importants
**Note** : Les éléments ✅ sont complètement terminés
**Note** : Les éléments 🚧 sont en cours ou à développer
