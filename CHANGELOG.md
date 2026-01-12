# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [Non publié]

### Fonctionnalités à venir
- CRUD complet des produits
- Gestion du point de vente (POS)
- Gestion de caisse avec sessions
- Module clients et fidélité
- Gestion des commandes
- Réservations et locations
- Codes promo
- Retours et remboursements
- Module RH simple
- Rapports et dashboard
- Intégration e-commerce

## [1.0.0] - 2026-01-12

### Ajouté
- 🎉 Version initiale du backend Commercia
- ✅ Configuration FastAPI avec structure professionnelle
- ✅ Authentification JWT complète
- ✅ 20+ modèles SQLAlchemy avec relations
- ✅ Base de données PostgreSQL complète via Supabase
- ✅ 8 triggers SQL automatiques :
  - Auto-génération des codes clients
  - Auto-génération des numéros de commande
  - Gestion automatique du statut de paiement
  - Déduction automatique du stock
  - Réintégration du stock après remboursement
  - Attribution automatique des points de fidélité
  - Gestion de la dette client
  - Mise à jour des timestamps
- ✅ Configuration Render pour déploiement
- ✅ Dockerfile optimisé pour production
- ✅ Tests unitaires avec pytest
- ✅ Documentation complète (README, DEPLOYMENT)
- ✅ Scripts de démarrage (run.sh, Makefile)

### Sécurité
- ✅ Hashing des mots de passe avec bcrypt
- ✅ JWT pour l'authentification
- ✅ CORS configuré
- ✅ Row Level Security (RLS) sur Supabase
- ✅ Validation des données avec Pydantic

### Infrastructure
- ✅ SQLAlchemy avec asyncpg pour PostgreSQL asynchrone
- ✅ Structure en couches (models, schemas, api)
- ✅ Configuration via variables d'environnement
- ✅ Logging configuré
- ✅ Health checks

### Endpoints API v1
- `POST /api/v1/auth/login` - Connexion
- `POST /api/v1/auth/register` - Inscription
- `GET /api/v1/auth/me` - Utilisateur actuel
- `POST /api/v1/auth/change-password` - Changer mot de passe
- `POST /api/v1/auth/logout` - Déconnexion

### Base de données
- Table `stores` - Magasins
- Table `users` - Utilisateurs
- Table `employees` - Employés
- Table `clients` - Clients
- Table `categories` - Catégories
- Table `products` - Produits
- Table `product_variants` - Variantes de produits
- Table `orders` - Commandes
- Table `order_items` - Articles de commande
- Table `transactions` - Transactions
- Table `payment_methods` - Méthodes de paiement
- Table `stock_movements` - Mouvements de stock
- Table `cash_register_sessions` - Sessions de caisse
- Table `cash_register_details` - Détails de caisse
- Table `reservations` - Réservations
- Table `reservation_items` - Articles de réservation
- Table `promo_codes` - Codes promo (schéma créé)
- Table `audit_logs` - Logs d'audit

## Types de changements

- `Ajouté` pour les nouvelles fonctionnalités
- `Modifié` pour les changements aux fonctionnalités existantes
- `Obsolète` pour les fonctionnalités qui seront bientôt supprimées
- `Supprimé` pour les fonctionnalités supprimées
- `Corrigé` pour les corrections de bugs
- `Sécurité` pour inviter les utilisateurs à mettre à jour en cas de vulnérabilités

---

**Note**: Les versions suivent le format MAJOR.MINOR.PATCH
- MAJOR : Changements incompatibles avec les versions précédentes
- MINOR : Ajout de fonctionnalités rétrocompatibles
- PATCH : Corrections de bugs rétrocompatibles
