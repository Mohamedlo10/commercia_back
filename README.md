# Commercia Backend API

API Backend pour le système de gestion commerciale Commercia - POS, Stock, Réservations et Locations.

## Table des matières

- [Technologies](#technologies)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration](#configuration)
- [Base de données](#base-de-données)
- [Démarrage](#démarrage)
- [Déploiement](#déploiement)
- [Documentation API](#documentation-api)
- [Structure du projet](#structure-du-projet)

## Technologies

- **FastAPI** - Framework web moderne et rapide
- **SQLAlchemy** - ORM avec support asynchrone
- **asyncpg** - Driver PostgreSQL asynchrone
- **PostgreSQL** (via Supabase) - Base de données
- **Pydantic** - Validation des données
- **JWT** - Authentification
- **Render** - Hébergement

## Prérequis

- Python 3.11+
- PostgreSQL 14+ (ou compte Supabase)
- pip ou poetry

## Installation

### 1. Cloner le repository

```bash
git clone https://github.com/votre-organisation/commercia.git
cd commercia
```

### 2. Créer un environnement virtuel

```bash
python -m venv venv

# Activer l'environnement
# Sur Windows:
venv\Scripts\activate

# Sur macOS/Linux:
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

## Configuration

### 1. Variables d'environnement

Copier le fichier `.env.example` vers `.env` :

```bash
cp .env.example .env
```

### 2. Configurer les variables dans `.env`

```env
# Application
PROJECT_NAME=Commercia API
ENVIRONMENT=development
DEBUG=true

# Sécurité
SECRET_KEY=your-super-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Base de données (Supabase)
DATABASE_URL=postgresql+asyncpg://user:password@host:port/database

# CORS
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## Base de données

### 1. Créer la base de données sur Supabase

1. Créez un compte sur [Supabase](https://supabase.com)
2. Créez un nouveau projet
3. Récupérez l'URL de connexion PostgreSQL

### 2. Exécuter le script SQL d'initialisation

Connectez-vous au SQL Editor de Supabase et exécutez le script :

```bash
database/init.sql
```

Ce script créera :
- ✅ Toutes les tables (20+ tables)
- ✅ Tous les triggers (8 triggers)
- ✅ Tous les indexes
- ✅ Row Level Security (RLS)

## Démarrage

### Développement

```bash
# Mode développement avec rechargement automatique
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production (locale)

```bash
# Avec Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker

```bash
# Build
docker build -t commercia-api .

# Run
docker run -p 8000:8000 --env-file .env commercia-api
```

## Déploiement

### Déploiement sur Render

1. Créez un compte sur [Render](https://render.com)
2. Connectez votre repository GitHub
3. Render détectera automatiquement le fichier `render.yaml`
4. Configurez les variables d'environnement
5. Déployez !

### Configuration Render

Le fichier `render.yaml` est déjà configuré avec :
- Service web Python
- Gunicorn avec 4 workers
- Health checks
- Autoscaling
- Variables d'environnement

## Documentation API

Une fois l'application démarrée, accédez à :

- **Swagger UI** : http://localhost:8000/api/docs
- **ReDoc** : http://localhost:8000/api/redoc
- **OpenAPI JSON** : http://localhost:8000/api/openapi.json

### Endpoints principaux

#### 🔐 Authentification
- `POST /api/v1/auth/login` - Connexion
- `POST /api/v1/auth/register` - Inscription
- `GET /api/v1/auth/me` - Utilisateur actuel
- `POST /api/v1/auth/change-password` - Changer mot de passe

#### 📦 Catégories (✅ Disponible)
- `POST /api/v1/categories/` - Créer une catégorie
- `GET /api/v1/categories/` - Lister les catégories (pagination + filtres)
- `GET /api/v1/categories/tree` - Arbre hiérarchique complet
- `GET /api/v1/categories/{id}` - Détails d'une catégorie
- `PUT /api/v1/categories/{id}` - Mettre à jour
- `DELETE /api/v1/categories/{id}` - Supprimer
- `GET /api/v1/categories/{id}/stats` - Statistiques

#### 🛍️ Produits (✅ Disponible)
- `POST /api/v1/products/` - Créer un produit
- `GET /api/v1/products/` - Lister les produits (pagination + filtres avancés)
- `GET /api/v1/products/{id}` - Détails d'un produit avec relations
- `PUT /api/v1/products/{id}` - Mettre à jour
- `DELETE /api/v1/products/{id}` - Supprimer
- `POST /api/v1/products/{id}/duplicate` - Dupliquer un produit
- `PATCH /api/v1/products/{id}/toggle-active` - Activer/Désactiver
- `POST /api/v1/products/{id}/variants` - Créer une variante
- `GET /api/v1/products/{id}/variants` - Lister les variantes
- `PUT /api/v1/products/{id}/variants/{variant_id}` - Modifier variante
- `DELETE /api/v1/products/{id}/variants/{variant_id}` - Supprimer variante

#### 👥 Clients (✅ Disponible)
- `POST /api/v1/clients/` - Créer un client
- `GET /api/v1/clients/` - Lister les clients (pagination + filtres)
- `GET /api/v1/clients/search` - Recherche rapide (autocomplete)
- `GET /api/v1/clients/{id}` - Détails avec statistiques
- `PUT /api/v1/clients/{id}` - Mettre à jour
- `DELETE /api/v1/clients/{id}` - Supprimer
- `POST /api/v1/clients/{id}/loyalty/adjust` - Ajuster points fidélité
- `POST /api/v1/clients/{id}/loyalty/redeem` - Calculer réduction
- `POST /api/v1/clients/{id}/debt/pay` - Paiement de dette
- `GET /api/v1/clients/{id}/stats` - Statistiques détaillées
- `PATCH /api/v1/clients/{id}/toggle-active` - Activer/Désactiver

#### 📊 Gestion du Stock (✅ Disponible)
- `POST /api/v1/stock/movements` - Créer un mouvement manuel
- `GET /api/v1/stock/movements` - Lister les mouvements
- `GET /api/v1/stock/movements/{product_id}/history` - Historique produit
- `POST /api/v1/stock/adjust` - Ajuster le stock (inventaire)
- `GET /api/v1/stock/current` - État actuel du stock
- `GET /api/v1/stock/low-stock` - Alertes stock faible
- `GET /api/v1/stock/summary` - Résumé global

#### 📄 Documentation complète
Consultez [docs/API.md](docs/API.md) pour la documentation détaillée de tous les endpoints.

#### 🚧 À venir
- `/api/v1/orders` - Gestion des commandes/ventes
- `/api/v1/transactions` - Transactions et paiements
- `/api/v1/cash-register` - Gestion de caisse
- `/api/v1/reservations` - Réservations et locations
- `/api/v1/reports` - Rapports et statistiques
- `/api/v1/employees` - Gestion des employés
- `/api/v1/suppliers` - Gestion des fournisseurs

## Structure du projet

```
commercia/
├── app/
│   ├── __init__.py
│   ├── main.py                 # Point d'entrée FastAPI
│   ├── core/
│   │   ├── config.py           # Configuration
│   │   ├── database.py         # Configuration DB
│   │   └── security.py         # JWT & Auth
│   ├── models/                 # Modèles SQLAlchemy
│   │   ├── base.py
│   │   ├── store.py
│   │   ├── user.py
│   │   ├── employee.py
│   │   ├── client.py
│   │   ├── product.py
│   │   ├── order.py
│   │   ├── transaction.py
│   │   ├── stock.py
│   │   ├── cash_register.py
│   │   └── reservation.py
│   ├── schemas/                # Schémas Pydantic
│   │   └── auth.py
│   └── api/
│       └── v1/
│           ├── api.py          # Router principal
│           └── endpoints/
│               └── auth.py     # Routes auth
├── database/
│   └── init.sql                # Script SQL complet
├── requirements.txt            # Dépendances
├── Dockerfile                  # Configuration Docker
├── render.yaml                 # Configuration Render
├── .env.example                # Exemple variables env
└── README.md
```

## Modules développés

✅ Configuration et structure de base
✅ Base de données complète (20+ tables, 8 triggers)
✅ Authentification JWT
✅ Modèles SQLAlchemy avec relations

### À développer (selon roadmap)

- [ ] CRUD Produits & Stocks
- [ ] Point de vente (POS)
- [ ] Gestion de caisse
- [ ] Clients & Fidélité
- [ ] Commandes & Ventes
- [ ] Réservations & Locations
- [ ] Codes promo
- [ ] Retours & Remboursements
- [ ] Module RH simple
- [ ] Rapports & Dashboard
- [ ] Intégration E-commerce

## Tests

```bash
# Installation des dépendances de test
pip install pytest pytest-asyncio httpx

# Lancer les tests
pytest
```

## Sécurité

- JWT pour l'authentification
- Bcrypt pour le hashing des mots de passe
- Row Level Security (RLS) sur Supabase
- CORS configuré
- Variables d'environnement pour les secrets
- Validation des données avec Pydantic

## Support

Pour toute question ou problème :
- Consultez la documentation API : `/api/docs`
- Ouvrez une issue sur GitHub
- Consultez les spécifications techniques : `SPECIFICATIONS_TECHNIQUES.md`

## Licence

Propriétaire - Tous droits réservés

---

**Version:** 1.0.0
**Date:** 2026-01-12
**Status:** En développement actif
# commercia_back
