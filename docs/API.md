# Documentation API Commercia

Cette documentation décrit tous les endpoints de l'API REST Commercia.

**Base URL**: `http://localhost:8000/api/v1`

**Documentation interactive**:
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

---

## 🔐 Authentication

Tous les endpoints (sauf `/auth/login` et `/auth/register`) nécessitent un token JWT dans le header:

```
Authorization: Bearer <votre_token>
```

### POST /auth/login
Connexion utilisateur

**Body**:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user_id": "uuid",
  "email": "user@example.com",
  "role": "admin",
  "store_id": "uuid"
}
```

### POST /auth/register
Créer un nouveau compte utilisateur

### GET /auth/me
Récupérer les informations de l'utilisateur connecté

### POST /auth/change-password
Changer le mot de passe

---

## 📦 Catégories

### POST /categories/
Créer une nouvelle catégorie

**Body**:
```json
{
  "name": "Électronique",
  "description": "Produits électroniques",
  "parent_id": "uuid (optionnel)",
  "store_id": "uuid",
  "image_url": "https://...",
  "display_order": 1,
  "is_active": true
}
```

### GET /categories/
Lister les catégories avec pagination

**Query params**:
- `page`: Numéro de page (défaut: 1)
- `page_size`: Taille de la page (défaut: 50, max: 100)
- `search`: Recherche dans nom/description
- `parent_id`: Filtrer par catégorie parente
- `is_active`: Filtrer par statut actif

**Response**:
```json
{
  "items": [...],
  "total": 50,
  "page": 1,
  "page_size": 50,
  "total_pages": 1
}
```

### GET /categories/tree
Récupérer l'arbre hiérarchique complet des catégories

**Query params**:
- `include_inactive`: Inclure les catégories inactives (défaut: false)

**Response**:
```json
{
  "categories": [
    {
      "id": "uuid",
      "name": "Parent",
      "children": [
        {
          "id": "uuid",
          "name": "Child 1",
          "children": [],
          "product_count": 5
        }
      ],
      "product_count": 10
    }
  ],
  "total_count": 15
}
```

### GET /categories/{category_id}
Récupérer une catégorie par ID avec ses sous-catégories

### PUT /categories/{category_id}
Mettre à jour une catégorie

### DELETE /categories/{category_id}
Supprimer une catégorie

**Query params**:
- `force`: Forcer la suppression même avec des produits (défaut: false)

### GET /categories/{category_id}/stats
Récupérer les statistiques d'une catégorie

---

## 🛍️ Produits

### POST /products/
Créer un nouveau produit

**Body**:
```json
{
  "name": "Laptop HP",
  "description": "Ordinateur portable HP Pavilion",
  "sku": "LAP-HP-001",
  "barcode": "1234567890123",
  "category_id": "uuid",
  "store_id": "uuid",
  "prix_achat": 500000,
  "prix_vente": 750000,
  "tva_rate": 18,
  "has_multiple_units": false,
  "primary_unit": "pièce",
  "secondary_unit": null,
  "units_per_primary": 1,
  "track_stock": true,
  "stock_alert_threshold": 5,
  "has_variants": false
}
```

### GET /products/
Lister les produits avec pagination et filtres

**Query params**:
- `page`, `page_size`: Pagination
- `search`: Recherche dans nom, SKU, code-barres, description
- `category_id`: Filtrer par catégorie
- `is_active`: Filtrer par statut actif
- `track_stock`: Filtrer produits suivis en stock
- `has_variants`: Filtrer produits avec variantes
- `in_stock_only`: Uniquement produits en stock
- `min_price`, `max_price`: Filtrer par prix
- `sort_by`: Tri (name, price, stock, created_at)
- `sort_order`: Ordre (asc, desc)

### GET /products/{product_id}
Récupérer un produit avec ses relations (catégorie, variantes)

### PUT /products/{product_id}
Mettre à jour un produit

### DELETE /products/{product_id}
Supprimer un produit

### POST /products/{product_id}/duplicate
Dupliquer un produit (avec variantes)

### PATCH /products/{product_id}/toggle-active
Activer/Désactiver un produit

---

## 🎨 Variantes de Produits

### POST /products/{product_id}/variants
Créer une variante de produit

**Body**:
```json
{
  "name": "T-Shirt Rouge M",
  "sku": "TSH-ROU-M",
  "attributes": {
    "couleur": "Rouge",
    "taille": "M"
  },
  "price": 10000,
  "cost_price": 5000,
  "stock_quantity": 50,
  "stock_alert_threshold": 10,
  "is_active": true
}
```

### GET /products/{product_id}/variants
Lister les variantes d'un produit

**Query params**:
- `include_inactive`: Inclure les variantes inactives

### PUT /products/{product_id}/variants/{variant_id}
Mettre à jour une variante

### DELETE /products/{product_id}/variants/{variant_id}
Supprimer une variante

---

## 👥 Clients

### POST /clients/
Créer un nouveau client

**Body**:
```json
{
  "first_name": "Jean",
  "last_name": "Dupont",
  "email": "jean.dupont@example.com",
  "phone": "221771234567",
  "address": "123 Rue de Dakar",
  "city": "Dakar",
  "country": "Sénégal",
  "store_id": "uuid",
  "loyalty_tier": "bronze",
  "credit_limit": 50000,
  "notes": "Client VIP"
}
```

**Response**: Le `client_code` est généré automatiquement (ex: CLI-001)

### GET /clients/
Lister les clients avec pagination et filtres

**Query params**:
- `page`, `page_size`: Pagination
- `search`: Recherche dans nom, prénom, email, téléphone, code
- `loyalty_tier`: Filtrer par niveau (bronze, silver, gold, platinum)
- `has_debt`: Filtrer clients avec dette
- `is_active`: Filtrer par statut actif
- `city`: Filtrer par ville
- `min_loyalty_points`: Points minimum
- `sort_by`: Tri (name, points, debt, last_purchase, created_at)
- `sort_order`: Ordre (asc, desc)

### GET /clients/search
Recherche rapide de clients (autocomplete)

**Query params**:
- `q`: Terme de recherche (min 2 caractères)
- `limit`: Nombre maximum de résultats (défaut: 10)

### GET /clients/{client_id}
Récupérer un client avec ses statistiques

**Response**:
```json
{
  "id": "uuid",
  "client_code": "CLI-001",
  "first_name": "Jean",
  "last_name": "Dupont",
  "email": "jean.dupont@example.com",
  "phone": "221771234567",
  "loyalty_points": 250,
  "loyalty_tier": "bronze",
  "total_debt": 0,
  "credit_limit": 50000,
  "total_orders": 15,
  "total_spent": 1500000,
  "average_order_value": 100000,
  "can_purchase_on_credit": true,
  "last_purchase_date": "2025-01-10T10:30:00Z",
  "created_at": "2024-12-01T08:00:00Z"
}
```

### PUT /clients/{client_id}
Mettre à jour un client

### DELETE /clients/{client_id}
Supprimer un client (uniquement sans commandes)

### PATCH /clients/{client_id}/toggle-active
Activer/Désactiver un client

---

## 🎁 Fidélité Client

### POST /clients/{client_id}/loyalty/adjust
Ajuster manuellement les points de fidélité

**Body**:
```json
{
  "points": 50,
  "reason": "Bonus anniversaire"
}
```

Points peut être négatif pour retirer des points.

### POST /clients/{client_id}/loyalty/redeem
Calculer la réduction pour un nombre de points

**Query params**:
- `points`: Nombre de points à utiliser

**Response**:
```json
{
  "points_to_redeem": 100,
  "discount_amount": 10000,
  "remaining_points": 150,
  "message": "100 points convertis en 10000 XOF de réduction"
}
```

**Taux**: 1 point = 100 XOF de réduction (configurable)

---

## 💳 Dette Client

### POST /clients/{client_id}/debt/pay
Enregistrer un paiement de dette

**Body**:
```json
{
  "amount": 25000,
  "payment_method": "Espèces",
  "notes": "Paiement partiel"
}
```

### GET /clients/{client_id}/stats
Récupérer les statistiques détaillées d'un client

**Response**:
```json
{
  "client_id": "uuid",
  "client_name": "Jean Dupont",
  "total_orders": 15,
  "total_spent": 1500000,
  "total_debt": 5000,
  "loyalty_points": 250,
  "loyalty_tier": "bronze",
  "average_order_value": 100000,
  "last_purchase_date": "2025-01-10T10:30:00Z",
  "orders_this_month": 3,
  "spent_this_month": 250000
}
```

---

## 📊 Gestion du Stock

### POST /stock/movements
Créer un mouvement de stock manuel

**Body**:
```json
{
  "store_id": "uuid",
  "product_id": "uuid",
  "variant_id": "uuid (optionnel)",
  "movement_type": "purchase",
  "quantity": 100,
  "unit": "pièce",
  "order_id": "uuid (optionnel)",
  "reference": "BON-001",
  "notes": "Réapprovisionnement"
}
```

**Types de mouvements**:
- `purchase`: Achat/Approvisionnement
- `sale`: Vente (généralement automatique)
- `return`: Retour client
- `adjustment_in`: Ajustement positif (inventaire)
- `adjustment_out`: Ajustement négatif (casse, vol)
- `transfer_in`: Transfert entrant
- `transfer_out`: Transfert sortant

### GET /stock/movements
Lister les mouvements de stock

**Query params**:
- `page`, `page_size`: Pagination
- `product_id`: Filtrer par produit
- `movement_type`: Filtrer par type
- `date_from`, `date_to`: Filtrer par période

### GET /stock/movements/{product_id}/history
Historique des mouvements d'un produit

**Query params**:
- `limit`: Nombre de mouvements (défaut: 50, max: 200)

---

## 📦 Ajustements de Stock

### POST /stock/adjust
Ajuster le stock d'un produit (inventaire)

**Body**:
```json
{
  "product_id": "uuid",
  "variant_id": "uuid (optionnel)",
  "new_quantity": 150,
  "reason": "Inventaire mensuel - correction",
  "unit": "pièce"
}
```

Crée automatiquement un mouvement `adjustment_in` ou `adjustment_out` selon la différence.

---

## 📈 État du Stock

### GET /stock/current
Récupérer l'état actuel du stock de tous les produits

**Query params**:
- `category_id`: Filtrer par catégorie
- `in_stock_only`: Uniquement produits en stock
- `low_stock_only`: Uniquement produits en stock faible
- `sort_by`: Tri (name, stock, value)

**Response**:
```json
[
  {
    "product_id": "uuid",
    "product_name": "Laptop HP",
    "product_sku": "LAP-HP-001",
    "category_name": "Électronique",
    "stock_quantity_primary": 15,
    "primary_unit": "pièce",
    "stock_quantity_secondary": 0,
    "secondary_unit": null,
    "stock_alert_threshold": 5,
    "is_below_threshold": false,
    "stock_status": "in_stock",
    "cost_price": 500000,
    "total_stock_value": 7500000,
    "last_movement_date": "2025-01-10T14:20:00Z",
    "has_variants": false,
    "track_stock": true
  }
]
```

**Stock Status**:
- `in_stock`: Stock suffisant
- `low_stock`: Stock faible (≤ seuil d'alerte)
- `out_of_stock`: Rupture de stock
- `not_tracked`: Produit non suivi en stock

### GET /stock/low-stock
Récupérer les alertes de stock faible

**Response**:
```json
[
  {
    "product_id": "uuid",
    "variant_id": null,
    "product_name": "Laptop HP",
    "variant_name": null,
    "current_stock": 3,
    "alert_threshold": 5,
    "shortage": 2,
    "unit": "pièce"
  }
]
```

### GET /stock/summary
Résumé global du stock

**Response**:
```json
{
  "total_products": 250,
  "products_in_stock": 200,
  "products_low_stock": 15,
  "products_out_of_stock": 35,
  "total_stock_value": 50000000,
  "products_with_variants": 30
}
```

---

## 🔄 Codes de Statut HTTP

- `200 OK`: Succès
- `201 Created`: Ressource créée
- `204 No Content`: Suppression réussie
- `400 Bad Request`: Données invalides
- `401 Unauthorized`: Non authentifié
- `403 Forbidden`: Non autorisé
- `404 Not Found`: Ressource non trouvée
- `422 Unprocessable Entity`: Erreur de validation
- `500 Internal Server Error`: Erreur serveur

---

## 📝 Notes Importantes

### Pagination
Tous les endpoints de liste supportent la pagination avec:
- `page`: Numéro de page (commence à 1)
- `page_size`: Taille de la page (max 100)

### Filtres et Recherche
- La recherche est insensible à la casse
- Les filtres peuvent être combinés
- Le tri est configurable sur la plupart des listes

### Multi-Store
Toutes les ressources sont liées à un `store_id`. Un utilisateur ne peut accéder qu'aux données de son magasin.

### Soft Delete
Préférez utiliser `is_active=false` plutôt que de supprimer les ressources pour conserver l'historique.

### Timestamps
Toutes les ressources ont `created_at` et `updated_at` (format ISO 8601 avec timezone UTC).

---

## 🧪 Tester l'API

### Avec curl
```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@commercia.com","password":"admin123"}'

# Créer un produit
curl -X POST http://localhost:8000/api/v1/products/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

### Avec Swagger UI
Accédez à `http://localhost:8000/api/docs` pour tester interactivement tous les endpoints.

---

## 🚀 Prochains Endpoints

Les modules suivants seront ajoutés prochainement:
- `/orders` - Gestion des commandes/ventes
- `/transactions` - Transactions et paiements
- `/cash-register` - Gestion de la caisse
- `/reservations` - Réservations clients
- `/reports` - Rapports et statistiques
- `/employees` - Gestion des employés
- `/suppliers` - Gestion des fournisseurs
