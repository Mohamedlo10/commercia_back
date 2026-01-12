# SPECIFICATIONS TECHNIQUES - COMMERCIA
## Document de référence pour le développement

---

## 📋 TABLE DES MATIÈRES

1. [Vue d'ensemble du projet](#vue-densemble-du-projet)
2. [Architecture technique](#architecture-technique)
3. [Modules fonctionnels](#modules-fonctionnels)
4. [Schéma de base de données](#schéma-de-base-de-données)
5. [Flux métier critiques](#flux-métier-critiques)
6. [Manquements et ambiguïtés identifiés](#manquements-et-ambiguïtés-identifiés)
7. [Recommandations techniques](#recommandations-techniques)
8. [Feuille de route de développement](#feuille-de-route-de-développement)

---

## 🎯 VUE D'ENSEMBLE DU PROJET

### Objectif
Commercia est une plateforme de gestion commerciale omnicanal destinée aux commerces de détail (produits physiques) et aux services de réservation/location. Elle digitalise les opérations, facilite l'encaissement, optimise la gestion des stocks et offre un pilotage temps réel.

### Positionnement
Déclinaison de Mafalia pour:
- **Produits physiques**: Vêtements, Électronique, Quincaillerie, Beauté, Auto/Moto, Maison, Sport, Supermarché
- **Réservation/Location**: Hôtels, Location voitures, Événements, Restaurants, Fitness, Santé

### Périmètre confirmé
- **Utilisateurs simultanés**: 50 max
- **Architecture**: Mono-magasin (pas de multi-sites)
- **Mode**: En ligne uniquement (pas de mode hors-ligne)
- **Déploiement**: Cloud (Vercel)

---

## 🏗️ ARCHITECTURE TECHNIQUE

### Stack technique validée

| Couche | Technologie | Justification |
|--------|-------------|---------------|
| **Frontend** | Next.js (via Lovable) | Framework React moderne, SSR, optimisé SEO |
| **Backend** | FastAPI (via Claude Code) | Async Python, performances élevées, documentation auto |
| **Base de données** | Supabase (PostgreSQL) | BaaS, auth intégrée, temps réel, Row Level Security |
| **Déploiement** | Vercel | CI/CD automatique, edge functions, optimisé Next.js |
| **Stockage fichiers** | Supabase Storage | Intégré, gestion des images produits/tickets PDF |

### Architecture applicative

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │Dashboard │  │ Products │  │   POS    │  │ Reports  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↕ REST API
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Auth    │  │ Products │  │  Orders  │  │  Cash    │  │
│  │ Service  │  │ Service  │  │ Service  │  │ Register │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
                            ↕ SQL
┌─────────────────────────────────────────────────────────────┐
│              SUPABASE (PostgreSQL + Storage)                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Products │  │  Orders  │  │   Cash   │  │   Users  │  │
│  │ Variants │  │  Trans-  │  │ Sessions │  │  Clients │  │
│  │  Stock   │  │  actions │  │ Payments │  │ Loyalty  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Contraintes techniques
- **Scalabilité**: 50 utilisateurs simultanés max (architecture légère suffisante)
- **Pas de synchronisation hors-ligne**: Connexion internet obligatoire
- **Mono-tenant**: Un magasin = une instance isolée de données
- **Export/Import**: Format Excel uniquement pour catalogues produits

---

## 📦 MODULES FONCTIONNELS

### 1. 📊 Dashboard (Pilotage temps réel)

**Fonctionnalités confirmées:**
- Filtres temporels: Jour / Semaine / Mois / Intervalle personnalisé
- Sélection point de vente (si futur multi-magasins)
- **KPIs principaux:**
  - Chiffre d'Affaires (CA)
  - Panier Moyen
  - Dépenses
  - Solde de Caisse
- **Graphiques:**
  - Évolution revenus/commandes/dépenses
  - Meilleures ventes (top produits)
  - Pick meal (heures de pointe)
  - Balance canaux (pickup vs livraison)
- **Activités récentes:**
  - Dernières commandes
  - Historique sessions de caisse
- **Répartition:**
  - Par moyens de paiement
  - Par types de commande

**Rapports avancés (au-delà du dashboard):**
- Rapport d'inventaire (stocks, alertes seuils)
- Rapport de marge (par produit/catégorie)
- Analyse ABC (classification produits)
- Rapport de ventes détaillé
- Rapport de fidélité client
- Rapport de performance (par employé/canal)
- Rapport d'activité (anomalies, annulations)

---

### 2. 🛍️ Gestion Produits & Stocks

#### 2.1 Flow de création produits scalable

**Principe:** Flow adaptatif selon le type de produit (voir [info_process.md](info_process.md))

**Étapes de création:**
1. **Sélection du type de produit:**
   - Commerce de détail général
   - Vêtements & Mode
   - Électronique
   - Quincaillerie/Matériel
   - Beauté & Cosmétiques
   - Autres...

2. **Taxonomie spécifique au type:**
   - Catégorie → Sous-catégorie → Marque
   - Exemple: Électronique → Smartphones → Samsung

3. **Formulaire adaptatif selon classification:**
   - **Détail général:** Unités principales/secondaires, conversion auto
   - **Vêtements:** Variantes (tailles, couleurs), collections saisonnières
   - **Électronique:** Numéros de série, garanties, lots
   - **Quincaillerie:** Unités multiples (lot/pièce)

#### 2.2 Gestion des variantes

**Solution technique:**
- Table `products` (produit parent)
- Table `product_variants` (clé étrangère `product_id`)
- **Champs variantes:**
  - `size`, `color`, `material`, `format`
  - `sku` (auto-généré selon pattern: `{PRODUIT}-{TAILLE}-{COULEUR}`)
  - `stock_quantity` (stock par variante)
  - `price_adjustment` (ajustement prix si différent du parent)

**Exemple:**
```
Product: T-shirt Coton (id: 123)
├─ Variant: TS-M-RED (taille: M, couleur: Rouge, stock: 10)
├─ Variant: TS-L-RED (taille: L, couleur: Rouge, stock: 5)
└─ Variant: TS-M-BLU (taille: M, couleur: Bleu, stock: 8)
```

#### 2.3 Génération automatique des SKU

**Règles selon type de produit:**
- **Détail général:** `{CATEGORIE}{CODE_PRODUIT}` (ex: CRAY12)
- **Vêtements:** `{PRODUIT}-{TAILLE}-{COULEUR}` (ex: TS-M-RED)
- **Électronique:** `{MARQUE}-{MODELE}` (ex: SM-X100)
- **Quincaillerie:** `{TYPE}{QUANTITE}` (ex: VIS100)

#### 2.4 Gestion unités multiples

**Conversion automatique:**
- Unité principale: Boîte de 12 crayons
- Unité secondaire: Crayon individuel
- Facteur de conversion: 1 boîte = 12 crayons
- Stock: 50 boîtes = 600 crayons

**Ajustement automatique à la vente:**
- Vente 1 crayon → stock: 599 crayons, 50 boîtes
- Vente 1 boîte → stock: 49 boîtes, 588 crayons

#### 2.5 Import/Export Excel

**Fonctionnalités:**
- **Import:** Téléchargement template Excel avec colonnes obligatoires
  - Validation des données (SKU uniques, prix > 0, etc.)
  - Création en masse avec preview avant confirmation
- **Export:** Téléchargement catalogue complet au format Excel
  - Filtres: catégorie, marque, stock, statut

#### 2.6 Gestion stocks

**Fonctionnalités:**
- Stock en temps réel par produit/variante
- Alertes seuil minimum configurable
- Historique mouvements de stock:
  - Entrée (réception fournisseur)
  - Sortie (vente)
  - Ajustement manuel (inventaire)
  - Type: ajout/retrait/transfert/inventaire
- Inventaire physique avec écarts

**Pas de fonctionnalités (confirmé):**
- ❌ Transferts inter-magasins (mono-magasin)
- ❌ Réservation de stock
- ❌ Stock en transit

---

### 3. 💰 POS – Point de Vente Omnicanal

#### 3.1 Types de commandes

- **Pickup (à récupérer):** Client vient chercher
- **Livraison:** Nécessite adresse + téléphone + mode livraison (rapide/standard)

**Pas de gestion de tables** (différence avec Mafalia restauration)

#### 3.2 Workflow de création de commande

**Étape 1: Sélection du type**
- Choix: Pickup ou Livraison
- Si Livraison → saisie adresse + téléphone + mode

**Étape 2: Constitution du panier**
- Recherche produit (nom, SKU, scan barcode)
- Ajout quantités
- Sélection variantes (taille, couleur)
- Ajout extras/suppléments si applicable
- Notes spéciales

**Étape 3: Information client**
- Recherche client existant (nom, téléphone)
- Création rapide nouveau client
- Type client (régulier, VIP, etc.)

**Étape 4: Application réductions**
- Remises manuelles (montant ou %)
- Codes promo
- Utilisation points de fidélité

**Étape 5: Paiement** (voir section suivante)

#### 3.3 Gestion des paiements

**Méthodes de paiement:**
- Table `payment_methods` avec:
  - Nom (Espèces, Wave, Orange Money, MTN, Carte bancaire, Chèque, TPE)
  - Code système
  - Icône
  - Statut actif/inactif
  - Champs formulaire spécifiques

**Important:** Pas d'intégration API pour le moment
- Enregistrement manuel des paiements Wave/Orange Money
- Pas de vérification automatique
- Futur: intégration API quand comptes marchands disponibles

**Scénarios de paiement:**

**A. Paiement complet immédiat:**
```
1. Vérification session caisse ouverte
2. Création commande (status_commande: "confirme")
3. Création transaction (type: "sale", statut: "completed")
4. Mise à jour commande (statut_paiement: "Payer")
5. Déduction points fidélité si utilisés
6. Ajout vente à session caisse
7. Génération ticket PDF
```

**B. Vente à crédit (paiement différé/partiel):**
```
1. Création commande (status_commande: "confirme", statut_paiement: "Non Payer")
2. Enregistrement champs:
   - montant_total
   - montant_paye: 0
   - montant_restant: montant_total
3. Pas de transaction immédiate
4. Paiements ultérieurs → créations transactions successives
5. Trigger automatique MAJ (montant_paye, montant_restant)
6. Quand montant_paye = montant_total → statut_paiement: "Payer"
```

**Règle critique:** Session caisse ouverte OBLIGATOIRE pour tout paiement

#### 3.4 QR Code / Token paiement

**Statut:** ⏸️ EN STANDBY
- Fonctionnalité à concevoir ultérieurement
- Idée: génération QR code pour paiement mobile client
- Nécessite intégration API opérateurs

#### 3.5 Tickets de caisse

**Format:** PDF uniquement (pas d'impression papier pour le moment)
- Génération automatique après paiement complet
- Contenu:
  - Informations magasin (nom, adresse, téléphone)
  - Numéro ticket unique
  - Date et heure
  - Détails produits (nom, quantité, prix unitaire, sous-total)
  - Remises appliquées
  - Points fidélité utilisés/gagnés
  - Montant total
  - Méthode de paiement
  - Informations fiscales (TVA si applicable)
- Export/téléchargement PDF
- Envoi email client (optionnel)

---

### 4. 💵 Module Caisse (Cash Register)

**Inspiration:** Système Mafalia (voir [info_sur_mafalia.md](info_sur_mafalia.md))

#### 4.1 Sessions de caisse

**Contrainte:** UNE SEULE session active par magasin à la fois

**Ouverture de session:**
1. Vérification: aucune session déjà ouverte
2. Sélection caissier (si utilisateur n'est pas caissier)
3. Saisie montant initial (fond de caisse)
4. Création session:
   - `montant_initial`
   - `total_ventes: 0`
   - `total_depenses: 0`
   - `solde_theorique: montant_initial`
   - `statut: "ouvert"`
   - `heure_ouverture`

**Enregistrement des transactions:**
- Chaque vente payée → création transaction:
  - `type: "sale"`
  - `montant`
  - `methode_paiement_id`
  - `order_reference`
  - `client_nom`, `client_telephone`
  - `numero_transaction` (unique)
  - `statut: "completed"`
- Mise à jour automatique session:
  - `total_ventes += montant`
  - `montant_final += montant`

**Suivi temps réel:**
- Total ventes du jour/période
- Nombre de transactions
- Répartition par méthode de paiement:
  - Espèces (montant + nombre)
  - Mobile Money (Wave, OM, MTN)
  - Carte, Chèque, TPE

**Fermeture de session:**
1. Saisie montant réel (comptage physique)
2. Notes optionnelles
3. Calcul automatique:
   ```
   Solde théorique = montant_initial + total_ventes - total_depenses
   Écart = montant_reel - solde_theorique
   ```
4. Résultat:
   - Écart positif: surplus
   - Écart négatif: manque
5. Session verrouillée (statut: "closed")
6. Traçabilité complète pour audit

#### 4.2 Règles métier strictes

- ✅ Une seule session ouverte par magasin
- ✅ Session obligatoire pour tout paiement
- ✅ Sessions verrouillées après fermeture (immuable)
- ✅ Transactions liées: impossible de supprimer sans traçabilité

---

### 5. 👥 Gestion Clients & Fidélité

#### 5.1 Profil client

**Informations de base:**
- Nom complet
- Téléphone (identifiant unique)
- Email (optionnel)
- Adresse (optionnel)
- Type client (Régulier, VIP, Professionnel)
- Date de création
- Date dernière commande

**Statistiques automatiques:**
- Nombre total de commandes
- Montant total dépensé
- Panier moyen
- Fréquence d'achat

#### 5.2 Programme de fidélité

**Principe:** Attribution de points après chaque commande payée

**Logique d'attribution:**
- Règle configurable: X points pour Y FCFA dépensés
  - Exemple: 1 point pour 1000 FCFA
- Attribution automatique après paiement complet
- Historique des points (gain/utilisation)

**Utilisation des points:**
- Conversion points → réduction
  - Exemple: 100 points = 1000 FCFA de réduction
- Déduction lors du paiement
- Validation: points suffisants
- Mise à jour automatique après utilisation

**Tableau de bord fidélité:**
- Solde points actuel
- Historique mouvements
- Points expirés (si règle d'expiration)
- Niveau client (Bronze/Silver/Gold selon points)

#### 5.3 Historique d'achats

- Liste complète des commandes client
- Filtres: date, statut, montant
- Détails par commande:
  - Produits achetés
  - Montant payé
  - Méthode de paiement
  - Points gagnés/utilisés

#### 5.4 Gestion des crédits

**Workflow simplifié:**
1. Création commande avec statut_paiement: "Non Payer"
2. Champs tracking:
   - `montant_total`
   - `montant_paye: 0`
   - `montant_restant: montant_total`
3. Client effectue paiement partiel:
   - Création transaction
   - Trigger MAJ:
     ```sql
     montant_paye += montant_transaction
     montant_restant = montant_total - montant_paye
     ```
4. Si `montant_paye >= montant_total`:
   - `statut_paiement = "Payer"`

**Pas de:**
- ❌ Limite de crédit par client (pour le moment)
- ❌ Échéancier de remboursement
- ❌ Relances automatiques (à venir)

**Vue "Dettes clients":**
- Liste clients avec solde impayé
- Montant total dû par client
- Ancienneté de la dette
- Historique paiements partiels

---

### 6. 🏨 Réservations & Locations

#### 6.1 Types de services

- Hôtels & Hébergements
- Location de voitures
- Événements & Loisirs
- Restaurants (réservation de tables)
- Fitness & Bien-être (créneaux cours)
- Santé & Services médicaux (rendez-vous)

#### 6.2 Solution proposée: Système unifié de créneaux

**Architecture recommandée:**

**Table `services`:**
- Nom du service
- Type (hôtel, voiture, table, créneau cours, RDV)
- Description
- Catégorie
- Tarif de base
- Durée standard (si applicable)
- Capacité (si applicable)

**Table `service_availability`:**
- `service_id`
- `date_debut`
- `date_fin`
- `heure_debut` (si créneau horaire)
- `heure_fin`
- `capacite_max` (nombre de réservations simultanées possibles)
- `statut` (disponible/indisponible)

**Table `reservations`:**
- `service_id`
- `client_id`
- `date_reservation`
- `creneau_debut`
- `creneau_fin`
- `nombre_personnes` (si applicable)
- `statut` (confirmée/en attente/annulée/terminée)
- `montant_total`
- `montant_acompte` (si caution/acompte requis)
- `montant_paye`
- `montant_restant`
- `notes`

#### 6.3 Gestion des créneaux horaires

**Principe:** Éviter les conflits de réservation

**Validation à la création:**
```python
def check_availability(service_id, date, heure_debut, heure_fin):
    # Vérifier capacité maximale pour ce créneau
    reservations_existantes = count_reservations(service_id, date, heure_debut, heure_fin)
    capacite_max = get_service_capacity(service_id)

    if reservations_existantes < capacite_max:
        return True
    else:
        return False  # Créneau complet
```

**Gestion de l'overbooking:**
- **Par défaut:** Interdit (validation stricte capacité)
- **Option:** Paramètre `allow_overbooking` par service
  - Si activé: capacité_max + marge (ex: 10%)
  - Alerte visuelle pour le gestionnaire

#### 6.4 Cautions & Acomptes

**Workflow proposé:**

**Pour locations de voitures:**
1. Lors de la réservation:
   - Saisie `montant_caution` (ex: 50 000 FCFA)
   - Saisie `montant_acompte` (ex: 20% du tarif)
   - Enregistrement caution comme transaction "pending"
2. Lors de la restitution:
   - Vérification état véhicule
   - Si OK: remboursement caution (transaction "refunded")
   - Si dommages: déduction caution (transaction "deducted", création dépense)

**Pour hôtels/événements:**
- Acompte à la réservation (transaction immédiate)
- Solde à payer à la fin (création transaction solde)
- Annulation: politique de remboursement configurable

**Champs transaction:**
- `type: "deposit" | "caution" | "refund" | "deduction" | "final_payment"`
- `reservation_id`
- `statut: "pending" | "completed" | "refunded"`

---

### 7. ��‍💼 Gestion Utilisateurs & Rôles

#### 7.1 Architecture utilisateurs

**Principe:** Un utilisateur peut être dans UN SEUL magasin avec des rôles différents

**Rôles proposés:**
- **Admin/Propriétaire:** Tous les droits, accès paramètres
- **Gérant:** Gestion produits, stocks, rapports, utilisateurs
- **Vendeur:** POS, création commandes, consultation stocks
- **Caissier:** Ouverture/fermeture caisse, encaissements
- **Inventoriste:** Gestion stocks, inventaires

**Permissions par rôle:**

| Fonctionnalité | Admin | Gérant | Vendeur | Caissier | Inventoriste |
|----------------|-------|--------|---------|----------|--------------|
| Dashboard complet | ✅ | ✅ | ⚠️ | ⚠️ | ❌ |
| Gestion produits | ✅ | ✅ | ❌ | ❌ | ✅ |
| POS (ventes) | ✅ | ✅ | ✅ | ✅ | ❌ |
| Caisse | ✅ | ✅ | ❌ | ✅ | ❌ |
| Rapports | ✅ | ✅ | ⚠️ | ⚠️ | ❌ |
| Paramètres | ✅ | ⚠️ | ❌ | ❌ | ❌ |
| Utilisateurs | ✅ | ⚠️ | ❌ | ❌ | ❌ |

⚠️ = Accès partiel/limité

#### 7.2 Authentification

**Via Supabase Auth:**
- Email + Mot de passe
- Magic Link (optionnel)
- Reset mot de passe
- Sessions sécurisées

**Row Level Security (RLS):**
- Isolation des données par magasin
- Vérification rôle pour chaque requête
- Politiques PostgreSQL

---

### 8. 🔌 Intégration Fournisseurs (externe)

**Statut:** Module développé par une autre personne

**Endpoints attendus (à exposer):**
- `GET /suppliers` - Liste des fournisseurs
- `GET /suppliers/{id}` - Détails fournisseur
- `POST /purchase-orders` - Création bon de commande
- `GET /purchase-orders` - Liste bons de commande
- `PUT /purchase-orders/{id}/receive` - Réception marchandises
- `GET /suppliers/{id}/products` - Produits du fournisseur

**Intégration côté Commercia:**
- Appels API lors de la réception de stocks
- Mise à jour automatique stock après réception
- Liaison produits fournisseurs

---

### 9. 🧾 Fiscalité & Conformité

#### 9.1 Configuration TVA & Taxes

**Paramètres magasin:**
- Activer/désactiver TVA
- Taux de TVA (%, ex: 18%)
- Autres taxes configurables (nom + taux)
- Numéro identification fiscale magasin

#### 9.2 Application sur produits

**Champs produit:**
- `taxable: boolean` (produit soumis à TVA)
- `tax_rate: decimal` (taux spécifique ou hérité des paramètres)

**Calcul automatique:**
```
Prix HT = Prix de vente / (1 + taux_TVA)
Montant TVA = Prix de vente - Prix HT
Prix TTC = Prix de vente (affiché)
```

#### 9.3 Tickets et factures

**Mentions obligatoires:**
- Raison sociale magasin
- Numéro identification fiscale
- Adresse
- Détail TVA:
  - Base HT
  - Montant TVA
  - Total TTC
- Numéro séquentiel de facture

---

## 🗄️ SCHÉMA DE BASE DE DONNÉES

### Entités principales et relations

```sql
-- MAGASINS
CREATE TABLE stores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    address TEXT,
    phone VARCHAR(20),
    email VARCHAR(255),
    tax_id VARCHAR(50),
    vat_enabled BOOLEAN DEFAULT false,
    vat_rate DECIMAL(5,2) DEFAULT 0,
    currency VARCHAR(3) DEFAULT 'XOF',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- UTILISATEURS
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    role VARCHAR(50) NOT NULL, -- admin, manager, cashier, salesperson, inventorist
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- CLIENTS
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id),
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    email VARCHAR(255),
    address TEXT,
    client_type VARCHAR(50) DEFAULT 'regular', -- regular, vip, professional
    loyalty_points INT DEFAULT 0,
    total_orders INT DEFAULT 0,
    total_spent DECIMAL(15,2) DEFAULT 0,
    last_order_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- CATÉGORIES PRODUITS
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id),
    name VARCHAR(255) NOT NULL,
    parent_id UUID REFERENCES categories(id), -- pour sous-catégories
    product_type VARCHAR(50) NOT NULL, -- retail, clothing, electronics, hardware, etc.
    created_at TIMESTAMP DEFAULT NOW()
);

-- MARQUES
CREATE TABLE brands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- PRODUITS
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id),
    category_id UUID REFERENCES categories(id),
    brand_id UUID REFERENCES brands(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    sku VARCHAR(100) UNIQUE NOT NULL,
    product_type VARCHAR(50) NOT NULL, -- retail, clothing, electronics, hardware

    -- Prix
    price DECIMAL(15,2) NOT NULL,
    cost_price DECIMAL(15,2),
    taxable BOOLEAN DEFAULT true,
    tax_rate DECIMAL(5,2),

    -- Unités multiples (pour retail/hardware)
    has_multiple_units BOOLEAN DEFAULT false,
    primary_unit VARCHAR(50), -- ex: "boîte"
    secondary_unit VARCHAR(50), -- ex: "pièce"
    conversion_factor INT, -- 1 boîte = 12 pièces

    -- Stock
    track_stock BOOLEAN DEFAULT true,
    stock_quantity INT DEFAULT 0,
    stock_secondary_unit INT DEFAULT 0, -- stock en unité secondaire
    stock_alert_threshold INT,

    -- Électronique
    has_serial_number BOOLEAN DEFAULT false,
    has_warranty BOOLEAN DEFAULT false,
    warranty_months INT,

    -- Statut
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- VARIANTES PRODUITS
CREATE TABLE product_variants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID REFERENCES products(id) ON DELETE CASCADE,
    sku VARCHAR(100) UNIQUE NOT NULL,

    -- Attributs variantes
    size VARCHAR(50),
    color VARCHAR(50),
    material VARCHAR(50),
    format VARCHAR(50),

    -- Prix et stock spécifiques
    price_adjustment DECIMAL(15,2) DEFAULT 0,
    stock_quantity INT DEFAULT 0,

    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- MOUVEMENTS DE STOCK
CREATE TABLE stock_movements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id),
    product_id UUID REFERENCES products(id),
    variant_id UUID REFERENCES product_variants(id),

    movement_type VARCHAR(50) NOT NULL, -- in, out, adjustment, inventory
    quantity INT NOT NULL,
    unit VARCHAR(50), -- primary ou secondary

    reference_type VARCHAR(50), -- order, purchase, adjustment
    reference_id UUID,

    notes TEXT,
    user_id UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- MÉTHODES DE PAIEMENT
CREATE TABLE payment_methods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL, -- cash, wave, orange_money, mtn, card, check
    icon VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- SESSIONS DE CAISSE
CREATE TABLE cash_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id),
    cashier_id UUID REFERENCES users(id),

    status VARCHAR(50) NOT NULL, -- open, closed

    opening_amount DECIMAL(15,2) NOT NULL,
    opening_time TIMESTAMP NOT NULL,
    opening_notes TEXT,

    total_sales DECIMAL(15,2) DEFAULT 0,
    total_expenses DECIMAL(15,2) DEFAULT 0,
    theoretical_balance DECIMAL(15,2),

    closing_amount DECIMAL(15,2),
    closing_time TIMESTAMP,
    closing_notes TEXT,

    difference DECIMAL(15,2), -- écart

    created_at TIMESTAMP DEFAULT NOW()
);

-- COMMANDES
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id),
    order_number VARCHAR(50) UNIQUE NOT NULL,

    -- Client
    client_id UUID REFERENCES clients(id),
    client_name VARCHAR(255),
    client_phone VARCHAR(20),

    -- Type
    order_type VARCHAR(50) NOT NULL, -- pickup, delivery
    delivery_address TEXT,
    delivery_mode VARCHAR(50), -- fast, standard

    -- Montants
    subtotal DECIMAL(15,2) NOT NULL,
    discount_amount DECIMAL(15,2) DEFAULT 0,
    loyalty_points_used INT DEFAULT 0,
    loyalty_discount DECIMAL(15,2) DEFAULT 0,
    tax_amount DECIMAL(15,2) DEFAULT 0,
    total_amount DECIMAL(15,2) NOT NULL,

    -- Paiement
    statut_paiement VARCHAR(50) NOT NULL, -- "Payer", "Non Payer", "Partiellement"
    montant_paye DECIMAL(15,2) DEFAULT 0,
    montant_restant DECIMAL(15,2),

    -- Statut commande
    status_commande VARCHAR(50) NOT NULL, -- confirme, pret, terminee, livree

    -- Autres
    notes TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ARTICLES COMMANDE
CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES orders(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id),
    variant_id UUID REFERENCES product_variants(id),

    product_name VARCHAR(255) NOT NULL,
    variant_description TEXT,

    quantity INT NOT NULL,
    unit VARCHAR(50), -- primary ou secondary
    unit_price DECIMAL(15,2) NOT NULL,
    subtotal DECIMAL(15,2) NOT NULL,

    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- TRANSACTIONS
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id),
    cash_session_id UUID REFERENCES cash_sessions(id),
    order_id UUID REFERENCES orders(id),

    transaction_number VARCHAR(50) UNIQUE NOT NULL,
    transaction_type VARCHAR(50) NOT NULL, -- sale, refund, expense, deposit, caution

    amount DECIMAL(15,2) NOT NULL,
    payment_method_id UUID REFERENCES payment_methods(id),

    client_name VARCHAR(255),
    client_phone VARCHAR(20),

    status VARCHAR(50) NOT NULL, -- completed, pending, refunded, cancelled
    notes TEXT,

    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- HISTORIQUE POINTS FIDÉLITÉ
CREATE TABLE loyalty_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id),
    order_id UUID REFERENCES orders(id),

    transaction_type VARCHAR(50) NOT NULL, -- earned, redeemed, expired
    points INT NOT NULL,
    balance_after INT NOT NULL,

    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- SERVICES (Réservations/Locations)
CREATE TABLE services (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id),

    name VARCHAR(255) NOT NULL,
    service_type VARCHAR(50) NOT NULL, -- hotel, car_rental, table, class, appointment
    description TEXT,
    category VARCHAR(100),

    base_price DECIMAL(15,2) NOT NULL,
    standard_duration INT, -- en minutes
    capacity INT, -- nombre de réservations simultanées possibles

    requires_deposit BOOLEAN DEFAULT false,
    deposit_amount DECIMAL(15,2),

    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- DISPONIBILITÉS SERVICES
CREATE TABLE service_availability (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_id UUID REFERENCES services(id),

    date_start DATE NOT NULL,
    date_end DATE NOT NULL,
    time_start TIME,
    time_end TIME,

    max_capacity INT,
    status VARCHAR(50) DEFAULT 'available', -- available, unavailable

    created_at TIMESTAMP DEFAULT NOW()
);

-- RÉSERVATIONS
CREATE TABLE reservations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id),
    service_id UUID REFERENCES services(id),
    client_id UUID REFERENCES clients(id),

    reservation_number VARCHAR(50) UNIQUE NOT NULL,

    reservation_date DATE NOT NULL,
    time_start TIME,
    time_end TIME,

    number_of_people INT,

    -- Montants
    total_amount DECIMAL(15,2) NOT NULL,
    deposit_amount DECIMAL(15,2) DEFAULT 0,
    montant_paye DECIMAL(15,2) DEFAULT 0,
    montant_restant DECIMAL(15,2),

    status VARCHAR(50) NOT NULL, -- confirmed, pending, cancelled, completed
    notes TEXT,

    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- CODES PROMO
CREATE TABLE promo_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    store_id UUID REFERENCES stores(id),

    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,

    discount_type VARCHAR(20) NOT NULL, -- percentage, fixed_amount
    discount_value DECIMAL(15,2) NOT NULL,

    min_order_amount DECIMAL(15,2), -- montant minimum de commande

    start_date DATE NOT NULL,
    end_date DATE NOT NULL,

    max_uses INT, -- nombre max d'utilisations global
    max_uses_per_client INT, -- nombre max d'utilisations par client
    current_uses INT DEFAULT 0,

    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- HISTORIQUE UTILISATION CODES PROMO
CREATE TABLE promo_code_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    promo_code_id UUID REFERENCES promo_codes(id),
    order_id UUID REFERENCES orders(id),
    client_id UUID REFERENCES clients(id),

    discount_applied DECIMAL(15,2) NOT NULL,
    used_at TIMESTAMP DEFAULT NOW()
);

-- EMPLOYÉS (extension de users avec infos RH)
CREATE TABLE employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    store_id UUID REFERENCES stores(id),

    -- Informations personnelles
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    national_id VARCHAR(50), -- CIN/CNI

    -- Contact
    phone VARCHAR(20),
    email VARCHAR(255),
    address TEXT,

    -- Emploi
    position VARCHAR(100) NOT NULL, -- Vendeur, Caissier, Gérant, etc.
    hire_date DATE NOT NULL,
    base_salary DECIMAL(15,2),

    -- Statut
    status VARCHAR(50) DEFAULT 'active', -- active, on_leave, inactive

    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Triggers importants

```sql
-- Trigger: Mise à jour automatique montant_paye et montant_restant commande
CREATE OR REPLACE FUNCTION update_order_payment_status()
RETURNS TRIGGER AS $$
DECLARE
    v_total_paid DECIMAL(15,2);
    v_total_refunded DECIMAL(15,2);
    v_net_paid DECIMAL(15,2);
    v_order_total DECIMAL(15,2);
BEGIN
    -- Récupérer le montant total de la commande
    SELECT total_amount INTO v_order_total FROM orders WHERE id = NEW.order_id;

    -- Calculer le montant total payé (ventes)
    SELECT COALESCE(SUM(amount), 0) INTO v_total_paid
    FROM transactions
    WHERE order_id = NEW.order_id
    AND transaction_type = 'sale'
    AND status = 'completed';

    -- Calculer le montant total remboursé
    SELECT COALESCE(SUM(ABS(amount)), 0) INTO v_total_refunded
    FROM transactions
    WHERE order_id = NEW.order_id
    AND transaction_type = 'refund'
    AND status = 'completed';

    -- Calculer le montant net payé
    v_net_paid := v_total_paid - v_total_refunded;

    -- Mettre à jour la commande
    UPDATE orders
    SET
        montant_paye = v_net_paid,
        montant_restant = v_order_total - v_net_paid,
        statut_paiement = CASE
            WHEN v_total_refunded >= v_order_total THEN 'Rembourser'
            WHEN v_total_refunded > 0 AND v_net_paid > 0 THEN 'Partiellement Rembourser'
            WHEN v_net_paid >= v_order_total THEN 'Payer'
            WHEN v_net_paid > 0 THEN 'Partiellement'
            ELSE 'Non Payer'
        END,
        updated_at = NOW()
    WHERE id = NEW.order_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_order_payment
AFTER INSERT ON transactions
FOR EACH ROW
WHEN (NEW.order_id IS NOT NULL)
EXECUTE FUNCTION update_order_payment_status();

-- Trigger: Mise à jour session caisse après transaction
CREATE OR REPLACE FUNCTION update_cash_session_totals()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.transaction_type = 'sale' THEN
        UPDATE cash_sessions
        SET
            total_sales = total_sales + NEW.amount,
            theoretical_balance = opening_amount + total_sales - total_expenses
        WHERE id = NEW.cash_session_id;
    ELSIF NEW.transaction_type = 'expense' THEN
        UPDATE cash_sessions
        SET
            total_depenses = total_depenses + NEW.amount,
            theoretical_balance = opening_amount + total_sales - total_depenses
        WHERE id = NEW.cash_session_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_cash_session
AFTER INSERT ON transactions
FOR EACH ROW
EXECUTE FUNCTION update_cash_session_totals();

-- Trigger: Ajustement automatique stock après vente
CREATE OR REPLACE FUNCTION adjust_stock_after_sale()
RETURNS TRIGGER AS $$
DECLARE
    v_product RECORD;
BEGIN
    -- Récupérer infos produit
    SELECT * INTO v_product FROM products WHERE id = NEW.product_id;

    IF v_product.track_stock THEN
        IF NEW.variant_id IS NOT NULL THEN
            -- Ajuster stock variante
            UPDATE product_variants
            SET stock_quantity = stock_quantity - NEW.quantity
            WHERE id = NEW.variant_id;
        ELSE
            -- Ajuster stock produit principal
            IF v_product.has_multiple_units AND NEW.unit = v_product.secondary_unit THEN
                -- Vente en unité secondaire
                UPDATE products
                SET
                    stock_secondary_unit = stock_secondary_unit - NEW.quantity,
                    stock_quantity = stock_secondary_unit / conversion_factor
                WHERE id = NEW.product_id;
            ELSE
                -- Vente en unité principale
                UPDATE products
                SET
                    stock_quantity = stock_quantity - NEW.quantity,
                    stock_secondary_unit = stock_quantity * conversion_factor
                WHERE id = NEW.product_id;
            END IF;
        END IF;

        -- Enregistrer mouvement de stock
        INSERT INTO stock_movements (
            store_id, product_id, variant_id, movement_type, quantity, unit, reference_type, reference_id
        ) VALUES (
            (SELECT store_id FROM orders WHERE id = NEW.order_id),
            NEW.product_id,
            NEW.variant_id,
            'out',
            NEW.quantity,
            NEW.unit,
            'order',
            NEW.order_id
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_adjust_stock_after_sale
AFTER INSERT ON order_items
FOR EACH ROW
EXECUTE FUNCTION adjust_stock_after_sale();

-- Trigger: Attribution points fidélité après commande payée
CREATE OR REPLACE FUNCTION award_loyalty_points()
RETURNS TRIGGER AS $$
DECLARE
    v_points_earned INT;
    v_points_rate DECIMAL := 0.001; -- 1 point pour 1000 FCFA (configurable)
BEGIN
    IF NEW.statut_paiement = 'Payer' AND OLD.statut_paiement != 'Payer' THEN
        -- Calculer points
        v_points_earned := FLOOR(NEW.total_amount * v_points_rate);

        -- Mettre à jour client
        UPDATE clients
        SET
            loyalty_points = loyalty_points + v_points_earned,
            total_orders = total_orders + 1,
            total_spent = total_spent + NEW.total_amount,
            last_order_date = NEW.created_at
        WHERE id = NEW.client_id;

        -- Historique points
        INSERT INTO loyalty_history (client_id, order_id, transaction_type, points, balance_after)
        VALUES (
            NEW.client_id,
            NEW.id,
            'earned',
            v_points_earned,
            (SELECT loyalty_points FROM clients WHERE id = NEW.client_id)
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_award_loyalty_points
AFTER UPDATE ON orders
FOR EACH ROW
EXECUTE FUNCTION award_loyalty_points();

-- Trigger: Réintégration stock après remboursement
CREATE OR REPLACE FUNCTION restock_after_refund()
RETURNS TRIGGER AS $$
DECLARE
    v_order RECORD;
    v_item RECORD;
BEGIN
    -- Vérifier que c'est un remboursement
    IF NEW.transaction_type = 'refund' AND NEW.status = 'completed' THEN
        -- Récupérer les articles de la commande
        FOR v_item IN
            SELECT * FROM order_items WHERE order_id = NEW.order_id
        LOOP
            -- Réintégrer le stock
            IF v_item.variant_id IS NOT NULL THEN
                -- Produit avec variante
                UPDATE product_variants
                SET stock_quantity = stock_quantity + v_item.quantity
                WHERE id = v_item.variant_id;
            ELSE
                -- Produit simple ou avec unités multiples
                DECLARE
                    v_product RECORD;
                BEGIN
                    SELECT * INTO v_product FROM products WHERE id = v_item.product_id;

                    IF v_product.has_multiple_units AND v_item.unit = v_product.secondary_unit THEN
                        -- Réintégration en unité secondaire
                        UPDATE products
                        SET
                            stock_secondary_unit = stock_secondary_unit + v_item.quantity,
                            stock_quantity = stock_secondary_unit / conversion_factor
                        WHERE id = v_item.product_id;
                    ELSE
                        -- Réintégration en unité principale
                        UPDATE products
                        SET
                            stock_quantity = stock_quantity + v_item.quantity,
                            stock_secondary_unit = stock_quantity * COALESCE(conversion_factor, 1)
                        WHERE id = v_item.product_id;
                    END IF;
                END;
            END IF;

            -- Enregistrer mouvement de stock
            INSERT INTO stock_movements (
                store_id, product_id, variant_id, movement_type, quantity, unit, reference_type, reference_id
            ) VALUES (
                (SELECT store_id FROM orders WHERE id = NEW.order_id),
                v_item.product_id,
                v_item.variant_id,
                'in',
                v_item.quantity,
                v_item.unit,
                'refund',
                NEW.id
            );
        END LOOP;

        -- Déduire les points de fidélité si gagnés sur cette commande
        UPDATE clients
        SET loyalty_points = loyalty_points - COALESCE(
            (SELECT points FROM loyalty_history
             WHERE order_id = NEW.order_id
             AND transaction_type = 'earned'
             LIMIT 1),
            0
        )
        WHERE id = (SELECT client_id FROM orders WHERE id = NEW.order_id);

        -- Historique points (déduction)
        INSERT INTO loyalty_history (client_id, order_id, transaction_type, points, balance_after)
        SELECT
            client_id,
            NEW.order_id,
            'refunded',
            -COALESCE(points, 0),
            (SELECT loyalty_points FROM clients WHERE id = orders.client_id)
        FROM orders
        LEFT JOIN loyalty_history ON loyalty_history.order_id = orders.id AND loyalty_history.transaction_type = 'earned'
        WHERE orders.id = NEW.order_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_restock_after_refund
AFTER INSERT ON transactions
FOR EACH ROW
WHEN (NEW.transaction_type = 'refund')
EXECUTE FUNCTION restock_after_refund();
```

---

## 🔄 FLUX MÉTIER CRITIQUES

### 1. Flux de vente complète (avec paiement immédiat)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. VÉRIFICATIONS PRÉALABLES                                 │
├─────────────────────────────────────────────────────────────┤
│ • Session caisse ouverte? → OUI/NON (bloquant)             │
│ • Stock suffisant pour tous les produits? → OUI/NON         │
│ • Points fidélité suffisants si utilisés? → OUI/NON         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. CRÉATION COMMANDE                                         │
├─────────────────────────────────────────────────────────────┤
│ • Insertion table orders                                     │
│   - order_number: auto-généré (ex: ORD-20250112-001)       │
│   - status_commande: "confirme"                             │
│   - statut_paiement: "Payer" (car paiement immédiat)       │
│   - montant_paye: total_amount                              │
│   - montant_restant: 0                                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. ENREGISTREMENT ARTICLES                                   │
├─────────────────────────────────────────────────────────────┤
│ • Insertion table order_items (pour chaque produit)         │
│ • TRIGGER: adjust_stock_after_sale                          │
│   - Déduction stock produit/variante                        │
│   - Création stock_movement (type: out)                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. CRÉATION TRANSACTION                                      │
├─────────────────────────────────────────────────────────────┤
│ • Insertion table transactions                               │
│   - transaction_type: "sale"                                │
│   - amount: total_amount                                    │
│   - payment_method_id: sélectionné par caissier            │
│   - cash_session_id: session active                         │
│   - order_id: commande créée                                │
│   - status: "completed"                                     │
│ • TRIGGER: update_cash_session_totals                       │
│   - total_sales += amount                                   │
│   - theoretical_balance recalculé                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. GESTION FIDÉLITÉ                                          │
├─────────────────────────────────────────────────────────────┤
│ • Si points utilisés:                                        │
│   - clients.loyalty_points -= points_used                   │
│   - loyalty_history (type: "redeemed")                      │
│ • TRIGGER: award_loyalty_points                             │
│   - Calcul points gagnés (ex: 1pt/1000 FCFA)               │
│   - clients.loyalty_points += points_earned                 │
│   - loyalty_history (type: "earned")                        │
│ • Mise à jour statistiques client:                          │
│   - total_orders += 1                                       │
│   - total_spent += total_amount                             │
│   - last_order_date = NOW()                                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. GÉNÉRATION TICKET PDF                                     │
├─────────────────────────────────────────────────────────────┤
│ • Template PDF avec:                                         │
│   - Infos magasin + numéro fiscal                           │
│   - Numéro ticket unique                                    │
│   - Détails articles (nom, qté, prix, sous-total)          │
│   - Remises/points utilisés                                 │
│   - Détail TVA (Base HT + Montant TVA + Total TTC)         │
│   - Méthode de paiement                                     │
│   - Points gagnés                                           │
│ • Upload Supabase Storage                                   │
│ • Retour URL téléchargement                                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 7. RETOUR INTERFACE                                          │
├─────────────────────────────────────────────────────────────┤
│ • Message succès                                             │
│ • Affichage résumé vente                                    │
│ • Boutons:                                                   │
│   - Télécharger ticket PDF                                  │
│   - Envoyer par email (optionnel)                           │
│   - Nouvelle vente                                           │
└─────────────────────────────────────────────────────────────┘
```

### 2. Flux de vente à crédit (paiement partiel)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. CRÉATION COMMANDE                                         │
├─────────────────────────────────────────────────────────────┤
│ • status_commande: "confirme"                               │
│ • statut_paiement: "Non Payer"                              │
│ • montant_total: calculé                                    │
│ • montant_paye: 0                                           │
│ • montant_restant: montant_total                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. PAIEMENT PARTIEL #1 (Client revient)                     │
├─────────────────────────────────────────────────────────────┤
│ • Vérification session caisse ouverte                       │
│ • Création transaction:                                      │
│   - amount: 50 000 FCFA (exemple)                           │
│   - order_id: commande existante                            │
│ • TRIGGER: update_order_payment_status                      │
│   - montant_paye = SUM(transactions) = 50 000               │
│   - montant_restant = total - 50 000                        │
│   - statut_paiement = "Partiellement"                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. PAIEMENT PARTIEL #2 (Client revient)                     │
├─────────────────────────────────────────────────────────────┤
│ • Nouvelle transaction: 50 000 FCFA                         │
│ • TRIGGER: update_order_payment_status                      │
│   - montant_paye = 100 000                                  │
│   - SI montant_paye >= montant_total:                       │
│     • statut_paiement = "Payer"                             │
│     • montant_restant = 0                                   │
│ • TRIGGER: award_loyalty_points (car maintenant payé)       │
│   - Attribution points fidélité                             │
└─────────────────────────────────────────────────────────────┘
```

### 3. Flux de réservation avec caution

```
┌─────────────────────────────────────────────────────────────┐
│ 1. VÉRIFICATION DISPONIBILITÉ                                │
├─────────────────────────────────────────────────────────────┤
│ • Sélection service + date + créneau horaire                │
│ • Query: compter réservations existantes pour ce créneau    │
│ • IF count < capacité_max → Disponible                      │
│   ELSE → Afficher "Créneau complet"                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. CRÉATION RÉSERVATION                                      │
├─────────────────────────────────────────────────────────────┤
│ • Insertion table reservations:                              │
│   - total_amount: tarif service                             │
│   - deposit_amount: caution (ex: 50 000 FCFA)              │
│   - montant_paye: 0                                         │
│   - montant_restant: total_amount                           │
│   - status: "confirmed"                                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. PAIEMENT CAUTION (Acompte)                               │
├─────────────────────────────────────────────────────────────┤
│ • Création transaction:                                      │
│   - transaction_type: "caution"                             │
│   - amount: deposit_amount                                  │
│   - reservation_id: réservation créée                       │
│   - status: "pending" (en attente restitution)              │
│ • Mise à jour réservation:                                  │
│   - montant_paye: deposit_amount                            │
│   - montant_restant: total - deposit                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. FIN DE SERVICE (Restitution)                             │
├─────────────────────────────────────────────────────────────┤
│ • Vérification état (véhicule, chambre, etc.)               │
│ • SCÉNARIO A: Pas de dommages                               │
│   - Création transaction remboursement:                     │
│     • transaction_type: "refund"                            │
│     • amount: deposit_amount                                │
│     • status: "completed"                                   │
│   - Mise à jour transaction caution: status → "refunded"    │
│ • SCÉNARIO B: Dommages constatés                            │
│   - Saisie montant déduction (ex: 20 000 FCFA)             │
│   - Création transaction déduction:                         │
│     • transaction_type: "deduction"                         │
│     • amount: montant_dommages                              │
│   - Création transaction remboursement partiel:             │
│     • amount: deposit - montant_dommages                    │
│   - Mise à jour caution: status → "deducted"                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. PAIEMENT FINAL (Solde)                                   │
├─────────────────────────────────────────────────────────────┤
│ • Création transaction:                                      │
│   - transaction_type: "final_payment"                       │
│   - amount: total_amount - deposit_amount                   │
│ • Mise à jour réservation:                                  │
│   - montant_paye: total_amount                              │
│   - montant_restant: 0                                      │
│   - status: "completed"                                     │
└─────────────────────────────────────────────────────────────┘
```

---

### 4. Flux de remboursement (retour produit)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. INITIALISATION REMBOURSEMENT                              │
├─────────────────────────────────────────────────────────────┤
│ • Recherche commande par numéro                              │
│ • Vérification: statut_paiement = "Payer"                   │
│ • Affichage détails commande (articles, montants)           │
│ • Choix: Remboursement total ou partiel                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2A. REMBOURSEMENT TOTAL                                      │
├─────────────────────────────────────────────────────────────┤
│ • Vérification session caisse ouverte                        │
│ • Saisie raison du retour (optionnel)                       │
│ • Sélection méthode de remboursement                        │
│ • Création transaction:                                      │
│   - transaction_type: "refund"                              │
│   - amount: -montant_total_commande (négatif)               │
│   - order_id: commande remboursée                           │
│   - payment_method_id: méthode remboursement                │
│   - status: "completed"                                     │
│ • TRIGGER: update_order_payment_status                      │
│   - Calcul montant net: total_paid - total_refunded        │
│   - statut_paiement → "Rembourser"                          │
│   - montant_paye: 0                                         │
│   - montant_restant: 0                                      │
│ • TRIGGER: restock_after_refund                             │
│   - Réintégration stock tous les articles                   │
│   - Création stock_movements (type: in)                     │
│   - Déduction points fidélité gagnés                        │
│ • Mise à jour session caisse:                               │
│   - total_sales -= montant_remboursé                        │
│   - theoretical_balance recalculé                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2B. REMBOURSEMENT PARTIEL (sélection articles)              │
├─────────────────────────────────────────────────────────────┤
│ • Liste articles de la commande                              │
│ • Sélection articles à retourner + quantités                │
│ • Calcul montant remboursement partiel:                     │
│   montant_partiel = Σ(quantité_retournée × prix_unitaire)  │
│ • Création transaction:                                      │
│   - amount: -montant_partiel (négatif)                      │
│   - notes: détail articles retournés                        │
│ • TRIGGER: update_order_payment_status                      │
│   - montant_paye = total_paid - montant_partiel             │
│   - SI montant_paye = 0:                                    │
│     • statut_paiement → "Rembourser"                        │
│   - SINON:                                                   │
│     • statut_paiement → "Partiellement Rembourser"          │
│ • Réintégration stock des articles retournés uniquement     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. GÉNÉRATION DOCUMENT REMBOURSEMENT                         │
├─────────────────────────────────────────────────────────────┤
│ • Génération PDF avoir/note de crédit:                      │
│   - Référence commande originale                            │
│   - Articles retournés                                      │
│   - Montant remboursé                                       │
│   - Méthode de remboursement                                │
│   - Date et signature                                       │
│ • Upload Supabase Storage                                   │
│ • Envoi email client (optionnel)                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. CONFIRMATION ET TRAÇABILITÉ                               │
├─────────────────────────────────────────────────────────────┤
│ • Message confirmation remboursement                         │
│ • Historique transactions mis à jour                        │
│ • Stock réintégré visible immédiatement                     │
│ • Points fidélité déduits si applicable                     │
│ • Dashboard mis à jour (CA ajusté)                          │
└─────────────────────────────────────────────────────────────┘
```

**Règles métier importantes:**
- ✅ Remboursement possible uniquement si commande payée
- ✅ Session caisse ouverte obligatoire
- ✅ Stock réintégré automatiquement (trigger)
- ✅ Points fidélité déduits automatiquement
- ✅ Montants session caisse ajustés
- ✅ Traçabilité complète via transactions

**Validations:**
- Vérifier que la commande n'a pas déjà été remboursée
- Pour remboursement partiel: vérifier quantités retournées ≤ quantités achetées
- Vérifier que le montant remboursé ne dépasse pas le montant payé

---

## ⚠️ MANQUEMENTS ET AMBIGUÏTÉS IDENTIFIÉS

### 1. ~~Promotions & Remises~~ ✅ CLARIFIÉ

**Solution validée:** Système de codes promo

**Implémentation MVP:**
- Table `promo_codes` avec:
  - Code unique
  - Type de remise (pourcentage ou montant fixe)
  - Valeur de la remise
  - Montant minimum de commande (optionnel)
  - Date de début et fin de validité
  - Nombre d'utilisations max (global et par client)
  - Statut actif/inactif
- Validation lors du paiement:
  - Vérifier validité du code
  - Vérifier conditions (montant min, dates)
  - Vérifier nombre d'utilisations restantes
- Historique des utilisations de codes promo

**Phase 2 (Post-MVP):**
- Promotions automatiques (% sur catégorie, BOGO)
- Happy hours / Tarifs horaires variables
- Promotions cumulables avec règles complexes

---

### 2. ~~Gestion des retours/remboursements~~ ✅ CLARIFIÉ

**Workflow validé:**

**Cas 1: Remboursement total**
```
1. Sélection de la commande à rembourser
2. Vérification: commande doit être payée (statut_paiement = "Payer")
3. Création transaction de remboursement:
   - transaction_type: "refund"
   - amount: montant_total_commande (montant négatif)
   - order_id: commande remboursée
   - payment_method_id: méthode de remboursement
4. Mise à jour commande:
   - statut_paiement: "Rembourser" (NOUVEAU STATUT)
   - montant_paye: 0
   - montant_restant: 0
5. Réintégration stock automatique (trigger inverse)
6. Déduction points fidélité si gagnés sur cette commande
```

**Cas 2: Remboursement partiel (retour de quelques articles)**
```
1. Sélection des articles à retourner
2. Calcul montant de remboursement partiel
3. Création transaction de remboursement partiel:
   - amount: montant_partiel (négatif)
4. Mise à jour commande:
   - montant_paye: montant_paye - montant_partiel
   - Si montant_paye = 0 → statut_paiement: "Rembourser"
   - Sinon → statut_paiement: "Partiellement Rembourser"
5. Réintégration stock des articles retournés
```

**Nouveaux statuts à ajouter:**
- `statut_paiement`: "Rembourser" (remboursement total)
- `statut_paiement`: "Partiellement Rembourser" (remboursement partiel)

**Phase 2 (Post-MVP):**
- Politique de retour automatique (délai configurable)
- Note de crédit pour le client (au lieu de remboursement cash)
- Raisons de retour (défectueux, taille incorrecte, etc.)

---

### 3. ~~Gestion multi-devises~~ ✅ VALIDÉ

**Décision:** Mono-devise FCFA uniquement

**Justification:** Marché cible principal (Afrique de l'Ouest francophone)

**Implémentation:**
- Champ `currency` dans table stores (fixé à "XOF" par défaut)
- Formatage montants avec séparateur milliers (ex: 50 000 FCFA)

**Phase 2 (Post-MVP) - si expansion internationale:**
- Support multi-devises avec taux de change
- Conversion automatique pour rapports

---

### 4. ~~Notifications & Alertes~~ ✅ VALIDÉ

**Décision:** POST-MVP

**MVP:** Alertes visuelles dans dashboard uniquement
- Badge rouge sur stock bas
- Notification in-app pour session caisse non fermée
- Alertes dans page dédiée (centre de notifications)

**Phase 2 (Post-MVP):**
- Intégration Twilio (SMS) ou SendGrid (Email)
- Alertes stock bas (email/SMS gérant)
- Notification commande prête (SMS client)
- Rappel rendez-vous réservation (24h avant)
- Relances paiements crédits

---

### 5. ~~Gestion des dépenses~~ ✅ VALIDÉ

**Décision:** À développer plus tard (lié aux fournisseurs)

**Justification:** Module dépenses nécessite intégration avec système fournisseurs (développé par autre personne)

**MVP:** Pas de module dépenses
- Les sorties de caisse (remise de caisse) sont gérées via le wallet

**Phase 2:**
- Module dépenses complet après réception endpoints fournisseurs
- Catégories de dépenses (achats, loyer, salaires, etc.)
- Pièces justificatives (upload factures)
- Lien avec bons de commande fournisseurs

---

### 6. ~~Rapports personnalisés~~ ✅ VALIDÉ

**Décision:** Rapports prédéfinis uniquement pour MVP

**MVP:**
- Rapports listés dans [dashboard.md](dashboard.md)
- Export Excel uniquement
- Filtres temporels standards

**Phase 2 (Post-MVP):**
- Query builder pour rapports personnalisés
- Export multi-format (PDF, Excel, CSV)
- Planification envoi automatique rapports (email quotidien/hebdo)

---

### 7. ~~Intégration e-commerce~~ ✅ CLARIFIÉ

**Solution validée:** Utilisation du module e-commerce de Mafalia

**Intégration:**
- Réutiliser le storefront e-commerce existant de Mafalia
- Adaptation pour Commercia:
  - Catalogue produits partagé avec POS
  - Synchronisation stock temps réel
  - Commandes web intégrées dans flux commandes général
  - Même système de paiement (avec méthodes e-commerce: carte bancaire en ligne)

**Spécificités e-commerce:**
- Type de commande: ajouter "online" (en plus de pickup/delivery)
- Commandes web apparaissent dans liste commandes POS
- Statut particulier: "en attente de paiement" pour commandes web non payées
- Gestion des retours e-commerce (délai légal)

**Architecture:**
```
Frontend E-commerce (Mafalia) ──┐
                                 ├──→ API Commercia (FastAPI)
Frontend POS (Commercia) ────────┘         ↕
                                    Base de données partagée
```

**Adaptation nécessaire:**
- Endpoints API Commercia compatibles avec frontend Mafalia
- Authentification clients (séparée de l'authentification magasin)
- Catalogue public (produits actifs uniquement)

---

### 8. ~~Gestion des employés (RH)~~ ✅ CLARIFIÉ

**Solution validée:** Module RH simple et efficace

**Implémentation MVP:**

**Table `employees` (extension de users):**
- Informations personnelles (nom, prénom, date naissance, CIN)
- Contact (téléphone, email, adresse)
- Poste et rôle
- Date d'embauche
- Salaire de base (si applicable)
- Statut (actif, congé, inactif)

**Fonctionnalités simples:**
1. **Gestion des employés:**
   - Liste des employés avec filtres (poste, statut)
   - Fiche employé (infos + historique)
   - Ajout/modification/désactivation

2. **Suivi basique des performances:**
   - Nombre de ventes par vendeur (depuis transactions)
   - CA généré par vendeur
   - Sessions caisse gérées par caissier

3. **Pas de:**
   - ❌ Système de pointage (pour le moment)
   - ❌ Calcul automatique salaires (manuel pour MVP)
   - ❌ Gestion congés/absences (manuel)
   - ❌ Commissions automatiques

**Rapports employés:**
- Performance par vendeur (ventes, CA, panier moyen)
- Historique sessions caisse par caissier (total encaissé, écarts)
- Export Excel pour paie

**Phase 2 (Post-MVP):**
- Système de pointage (entrée/sortie)
- Calcul automatique salaires + commissions
- Gestion congés avec validation
- Planning/horaires de travail

---

### 9. Sécurité & Permissions granulaires

**Manquement:** Permissions par rôle trop simples

**Amélioration possible:**
- Permissions granulaires (ex: "peut modifier prix" séparément de "peut créer produit")
- Audit trail (qui a fait quoi, quand)

**Recommandation:**
- MVP: Permissions par rôle (simple)
- Phase 2: Table `permissions` + `role_permissions` (granulaire)

---

### 10. Backup & Recovery

**Manquement:** Pas de stratégie backup mentionnée

**Recommandation:**
- Supabase a backup automatique quotidien (vérifier plan)
- Export manuel données critiques (produits, clients) mensuel

---

## 🚀 RECOMMANDATIONS TECHNIQUES

### 1. Architecture Backend (FastAPI)

**Structure recommandée:**
```
backend/
├── app/
│   ├── main.py                 # Point d'entrée FastAPI
│   ├── config.py               # Configuration (env vars)
│   ├── database.py             # Connexion Supabase
│   ├── dependencies.py         # Dépendances (auth, etc.)
│   │
│   ├── models/                 # Modèles Pydantic
│   │   ├── product.py
│   │   ├── order.py
│   │   ├── client.py
│   │   └── ...
│   │
│   ├── schemas/                # Schémas validation requêtes/réponses
│   │   ├── product.py
│   │   ├── order.py
│   │   └── ...
│   │
│   ├── routers/                # Routes API
│   │   ├── products.py         # CRUD produits
│   │   ├── orders.py           # Gestion commandes
│   │   ├── cash.py             # Sessions caisse
│   │   ├── clients.py          # Gestion clients
│   │   ├── dashboard.py        # KPIs et stats
│   │   └── ...
│   │
│   ├── services/               # Logique métier
│   │   ├── product_service.py
│   │   ├── order_service.py
│   │   ├── payment_service.py
│   │   ├── stock_service.py
│   │   └── ...
│   │
│   └── utils/                  # Utilitaires
│       ├── pdf_generator.py    # Génération tickets PDF
│       ├── sku_generator.py    # Auto-génération SKU
│       └── validators.py       # Validations custom
│
├── tests/                      # Tests unitaires
├── requirements.txt
└── .env.example
```

**Bonnes pratiques:**
- **Séparation concerns:** Routers → Services → Database
- **Validation Pydantic:** Tous les inputs validés avec modèles
- **Gestion erreurs:** Exception handlers centralisés
- **Logging:** Structured logging (JSON) pour debug
- **CORS:** Configuration stricte pour frontend Next.js
- **Rate limiting:** Protection endpoints sensibles

---

### 2. Architecture Frontend (Next.js)

**Structure recommandée:**
```
frontend/
├── src/
│   ├── app/                    # App Router Next.js 14+
│   │   ├── (auth)/             # Routes authentification
│   │   │   ├── login/
│   │   │   └── register/
│   │   │
│   │   ├── (dashboard)/        # Routes protégées
│   │   │   ├── layout.tsx      # Layout avec sidebar
│   │   │   ├── page.tsx        # Dashboard principal
│   │   │   ├── products/
│   │   │   ├── pos/
│   │   │   ├── orders/
│   │   │   ├── clients/
│   │   │   ├── cash/
│   │   │   ├── reports/
│   │   │   └── settings/
│   │   │
│   │   └── api/                # API routes (si nécessaire)
│   │
│   ├── components/             # Composants réutilisables
│   │   ├── ui/                 # Composants UI (buttons, inputs...)
│   │   ├── dashboard/
│   │   ├── products/
│   │   ├── pos/
│   │   └── ...
│   │
│   ├── lib/                    # Utilitaires
│   │   ├── api.ts              # Client API FastAPI
│   │   ├── supabase.ts         # Client Supabase
│   │   ├── utils.ts
│   │   └── validations.ts
│   │
│   ├── hooks/                  # Custom React hooks
│   │   ├── useAuth.ts
│   │   ├── useProducts.ts
│   │   ├── useOrders.ts
│   │   └── ...
│   │
│   ├── types/                  # Types TypeScript
│   │   ├── product.ts
│   │   ├── order.ts
│   │   └── ...
│   │
│   └── styles/                 # Styles globaux
│
├── public/                     # Assets statiques
├── next.config.js
├── tailwind.config.js
└── tsconfig.json
```

**Bonnes pratiques:**
- **Server Components par défaut:** Optimisation performances
- **Client Components:** Uniquement si interactivité nécessaire
- **React Query:** Cache et synchronisation données (useQuery, useMutation)
- **Zod:** Validation formulaires côté client
- **Tailwind CSS:** Design system cohérent
- **Dark mode:** Support via next-themes
- **Responsive:** Mobile-first design

---

### 3. Génération automatique des SKU

**Implémentation recommandée:**

```python
# backend/app/utils/sku_generator.py

def generate_sku(product_type: str, product_data: dict, variant_data: dict = None) -> str:
    """
    Génère automatiquement un SKU selon le type de produit
    """

    if product_type == "retail":
        # Exemple: CRAY12 (Catégorie + Code)
        category_code = product_data["category"][:4].upper()
        product_code = product_data.get("code", str(uuid.uuid4())[:4].upper())
        return f"{category_code}{product_code}"

    elif product_type == "clothing":
        # Exemple: TS-M-RED (Produit-Taille-Couleur)
        if variant_data:
            product_code = product_data["name"][:2].upper()
            size_code = variant_data["size"][0].upper()
            color_code = variant_data["color"][:3].upper()
            return f"{product_code}-{size_code}-{color_code}"
        else:
            return product_data["name"][:6].upper()

    elif product_type == "electronics":
        # Exemple: SM-X100 (Marque-Modèle)
        brand_code = product_data["brand"][:2].upper()
        model_code = product_data["model"].upper()
        return f"{brand_code}-{model_code}"

    elif product_type == "hardware":
        # Exemple: VIS100 (Type+Quantité)
        product_code = product_data["name"][:3].upper()
        quantity = product_data.get("primary_unit_quantity", "")
        return f"{product_code}{quantity}"

    else:
        # Fallback: UUID court
        return str(uuid.uuid4())[:8].upper()
```

---

### 4. Génération tickets PDF

**Librairie recommandée:** `reportlab` ou `weasyprint`

```python
# backend/app/utils/pdf_generator.py

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import io

def generate_receipt_pdf(order_data: dict, store_data: dict) -> bytes:
    """
    Génère un ticket de caisse en PDF
    """
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    # En-tête magasin
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 800, store_data["name"])
    c.setFont("Helvetica", 10)
    c.drawString(50, 785, store_data["address"])
    c.drawString(50, 770, f"Tél: {store_data['phone']}")
    c.drawString(50, 755, f"NIF: {store_data['tax_id']}")

    # Ligne séparation
    c.line(50, 745, 550, 745)

    # Numéro ticket et date
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 730, f"Ticket N°: {order_data['order_number']}")
    c.setFont("Helvetica", 10)
    c.drawString(50, 715, f"Date: {order_data['created_at']}")
    c.drawString(50, 700, f"Client: {order_data['client_name']}")

    # Ligne séparation
    c.line(50, 690, 550, 690)

    # En-têtes colonnes
    y = 675
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Produit")
    c.drawString(300, y, "Qté")
    c.drawString(370, y, "P.U.")
    c.drawString(470, y, "Total")

    c.line(50, y-5, 550, y-5)

    # Articles
    y -= 20
    c.setFont("Helvetica", 10)
    for item in order_data["items"]:
        c.drawString(50, y, item["product_name"][:30])
        c.drawString(300, y, str(item["quantity"]))
        c.drawString(370, y, f"{item['unit_price']:,.0f}")
        c.drawString(470, y, f"{item['subtotal']:,.0f}")
        y -= 15

    # Ligne séparation
    c.line(50, y, 550, y)
    y -= 20

    # Sous-total, remises, TVA, total
    c.drawString(370, y, "Sous-total:")
    c.drawString(470, y, f"{order_data['subtotal']:,.0f} FCFA")

    if order_data["discount_amount"] > 0:
        y -= 15
        c.drawString(370, y, "Remise:")
        c.drawString(470, y, f"-{order_data['discount_amount']:,.0f} FCFA")

    if order_data["loyalty_discount"] > 0:
        y -= 15
        c.drawString(370, y, f"Points fidélité ({order_data['loyalty_points_used']} pts):")
        c.drawString(470, y, f"-{order_data['loyalty_discount']:,.0f} FCFA")

    if store_data["vat_enabled"]:
        y -= 15
        c.drawString(370, y, f"TVA ({store_data['vat_rate']}%):")
        c.drawString(470, y, f"{order_data['tax_amount']:,.0f} FCFA")

    y -= 15
    c.setFont("Helvetica-Bold", 12)
    c.drawString(370, y, "TOTAL TTC:")
    c.drawString(470, y, f"{order_data['total_amount']:,.0f} FCFA")

    # Ligne séparation
    y -= 10
    c.line(50, y, 550, y)
    y -= 20

    # Méthode de paiement
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Paiement: {order_data['payment_method']}")

    # Points gagnés
    if order_data.get("points_earned"):
        y -= 15
        c.drawString(50, y, f"Points gagnés: {order_data['points_earned']} pts")

    # Footer
    y -= 40
    c.setFont("Helvetica-Italic", 9)
    c.drawString(200, y, "Merci de votre visite !")

    c.save()
    buffer.seek(0)
    return buffer.read()
```

**Upload Supabase Storage:**
```python
# Après génération PDF
pdf_bytes = generate_receipt_pdf(order_data, store_data)

# Upload vers Supabase Storage
file_path = f"receipts/{store_id}/{order_number}.pdf"
supabase.storage.from_("receipts").upload(file_path, pdf_bytes)

# Récupérer URL publique
pdf_url = supabase.storage.from_("receipts").get_public_url(file_path)
```

---

### 5. Gestion de la conversion unités multiples

**Approche recommandée:**

**Champs table `products`:**
```sql
has_multiple_units BOOLEAN DEFAULT false
primary_unit VARCHAR(50)          -- "boîte"
secondary_unit VARCHAR(50)        -- "pièce"
conversion_factor INT              -- 12 (1 boîte = 12 pièces)
stock_quantity INT                 -- Stock en unité principale
stock_secondary_unit INT           -- Stock en unité secondaire (calculé)
```

**Trigger synchronisation stock:**
```sql
CREATE OR REPLACE FUNCTION sync_stock_units()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.has_multiple_units THEN
        -- Si modification stock principal → recalculer secondaire
        IF NEW.stock_quantity != OLD.stock_quantity THEN
            NEW.stock_secondary_unit := NEW.stock_quantity * NEW.conversion_factor;
        END IF;

        -- Si modification stock secondaire → recalculer principal
        IF NEW.stock_secondary_unit != OLD.stock_secondary_unit THEN
            NEW.stock_quantity := NEW.stock_secondary_unit / NEW.conversion_factor;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sync_stock_units
BEFORE UPDATE ON products
FOR EACH ROW
EXECUTE FUNCTION sync_stock_units();
```

**Logique vente:**
```python
def sell_product(product_id, quantity, unit):
    product = get_product(product_id)

    if product.has_multiple_units:
        if unit == product.primary_unit:
            # Vente en unité principale
            new_primary = product.stock_quantity - quantity
            new_secondary = new_primary * product.conversion_factor
        else:
            # Vente en unité secondaire
            new_secondary = product.stock_secondary_unit - quantity
            new_primary = new_secondary / product.conversion_factor

        update_product_stock(product_id, new_primary, new_secondary)
    else:
        # Produit sans conversion
        update_product_stock(product_id, product.stock_quantity - quantity)
```

---

### 6. Authentification & Sécurité

**Supabase Auth + Row Level Security:**

```sql
-- Politique RLS: Isolation par magasin
ALTER TABLE products ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can only access their store products"
ON products
FOR ALL
USING (store_id = auth.uid()::uuid);

-- Politique RLS: Permissions par rôle
CREATE POLICY "Only admins and managers can delete products"
ON products
FOR DELETE
USING (
    EXISTS (
        SELECT 1 FROM users
        WHERE users.id = auth.uid()
        AND users.store_id = products.store_id
        AND users.role IN ('admin', 'manager')
    )
);
```

**Middleware FastAPI:**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    # Vérifier token Supabase
    user = supabase.auth.get_user(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    return user

async def require_role(allowed_roles: list):
    def role_checker(current_user = Depends(get_current_user)):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        return current_user
    return role_checker

# Usage dans routes
@router.delete("/products/{product_id}")
async def delete_product(
    product_id: str,
    current_user = Depends(require_role(["admin", "manager"]))
):
    # Seuls admin et manager peuvent supprimer
    ...
```

---

### 7. Gestion des erreurs et logging

**Structure erreurs personnalisées:**
```python
# backend/app/exceptions.py

class ComerciaException(Exception):
    """Base exception"""
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code

class NoOpenCashSessionError(ComerciaException):
    """Aucune session caisse ouverte"""
    def __init__(self):
        super().__init__(
            message="Aucune session de caisse ouverte. Veuillez ouvrir une session avant de procéder au paiement.",
            code="NO_OPEN_CASH_SESSION"
        )

class InsufficientStockError(ComerciaException):
    """Stock insuffisant"""
    def __init__(self, product_name: str, available: int, requested: int):
        super().__init__(
            message=f"Stock insuffisant pour {product_name}. Disponible: {available}, Demandé: {requested}",
            code="INSUFFICIENT_STOCK"
        )

# Exception handler
@app.exception_handler(ComerciaException)
async def comercia_exception_handler(request: Request, exc: ComerciaException):
    return JSONResponse(
        status_code=400,
        content={"error": exc.code, "message": exc.message}
    )
```

**Logging structuré:**
```python
import structlog

logger = structlog.get_logger()

# Usage
logger.info("order_created",
    order_id=order.id,
    client_id=order.client_id,
    total=order.total_amount,
    user_id=current_user.id
)
```

---

### 8. Performance & Optimisations

**Indexation base de données:**
```sql
-- Index sur colonnes fréquemment requêtées
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_store_category ON products(store_id, category_id);
CREATE INDEX idx_orders_store_date ON orders(store_id, created_at DESC);
CREATE INDEX idx_orders_client ON orders(client_id);
CREATE INDEX idx_transactions_session ON transactions(cash_session_id);
CREATE INDEX idx_transactions_order ON transactions(order_id);

-- Index pour recherche full-text
CREATE INDEX idx_products_name_trgm ON products USING gin(name gin_trgm_ops);
CREATE INDEX idx_clients_name_trgm ON clients USING gin(full_name gin_trgm_ops);
```

**Caching stratégique:**
```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

# Cache dashboard stats (5 minutes)
@router.get("/dashboard/stats")
@cache(expire=300)
async def get_dashboard_stats(store_id: str):
    return calculate_stats(store_id)

# Cache liste catégories (rarement modifié)
@router.get("/categories")
@cache(expire=3600)
async def get_categories(store_id: str):
    return get_all_categories(store_id)
```

**Pagination systématique:**
```python
from fastapi import Query

@router.get("/products")
async def list_products(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    store_id: str = Depends(get_current_store)
):
    offset = (page - 1) * limit
    products = db.query(Product).filter_by(store_id=store_id).offset(offset).limit(limit).all()
    total = db.query(Product).filter_by(store_id=store_id).count()

    return {
        "data": products,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit
        }
    }
```

---

## 📅 FEUILLE DE ROUTE DE DÉVELOPPEMENT

### Phase 0: Setup & Infrastructure (Semaine 1)

**Backend:**
- [ ] Initialisation projet FastAPI
- [ ] Configuration Supabase (base de données + storage)
- [ ] Création schéma base de données complet
- [ ] Configuration environnements (dev/staging/prod)
- [ ] Setup CI/CD (GitHub Actions + Vercel)

**Frontend:**
- [ ] Initialisation projet Next.js 14+ (App Router)
- [ ] Configuration Tailwind CSS + Design system
- [ ] Intégration Supabase Auth
- [ ] Layout de base (sidebar, topbar)
- [ ] Routing et navigation

---

### Phase 1: Gestion Produits & Stocks (Semaines 2-3)

**Priorité:** Module fondamental pour tout le reste

**Backend:**
- [ ] Endpoints CRUD produits
- [ ] Gestion catégories/marques
- [ ] Création variantes
- [ ] Génération automatique SKU
- [ ] Gestion stock (alertes, mouvements)
- [ ] Import/Export Excel

**Frontend:**
- [ ] Page liste produits (recherche, filtres, pagination)
- [ ] Formulaire création produit (flow adaptatif par type)
- [ ] Gestion variantes (interface intuitive)
- [ ] Page détail produit
- [ ] Alertes stock bas
- [ ] Import/Export Excel

**Tests:**
- [ ] Création produit simple (retail)
- [ ] Création produit avec variantes (vêtements)
- [ ] Ajustement stock automatique (unités multiples)
- [ ] Import catalogue 100 produits

---

### Phase 2: POS & Commandes (Semaines 4-5)

**Priorité:** Cœur métier de la plateforme

**Backend:**
- [ ] Endpoints création commande
- [ ] Gestion panier (ajout/suppression articles)
- [ ] Calcul automatique prix (remises, taxes)
- [ ] Génération numéro commande unique
- [ ] Trigger ajustement stock après vente
- [ ] États commande (confirme, pret, terminee)

**Frontend:**
- [ ] Interface POS (recherche produits, panier)
- [ ] Sélection variantes/quantités
- [ ] Application remises
- [ ] Recherche/création client rapide
- [ ] Écran récapitulatif avant paiement
- [ ] Page liste commandes (filtres, recherche)
- [ ] Page détail commande

**Tests:**
- [ ] Vente simple 1 produit
- [ ] Vente multiple avec variantes
- [ ] Vente avec remise + points fidélité
- [ ] Ajustement stock automatique vérifié

---

### Phase 3: Caisse & Paiements (Semaine 6)

**Priorité:** Nécessaire pour finaliser les ventes

**Backend:**
- [ ] Endpoints ouverture/fermeture session caisse
- [ ] Vérification session ouverte avant paiement
- [ ] Création transactions
- [ ] Trigger mise à jour totaux session
- [ ] Calcul écarts caisse
- [ ] Endpoints méthodes de paiement

**Frontend:**
- [ ] Modale ouverture session (fond de caisse)
- [ ] Écran paiement (sélection méthode, montant)
- [ ] Support paiement mixte (multiple méthodes)
- [ ] Modale fermeture session (réconciliation)
- [ ] Page historique sessions
- [ ] Page entrées de caisse (transactions)
- [ ] Génération et téléchargement ticket PDF

**Tests:**
- [ ] Ouverture session → ventes → fermeture (écart zéro)
- [ ] Ouverture session → ventes → fermeture (avec écart)
- [ ] Vérification blocage paiement sans session
- [ ] Ticket PDF généré et conforme

---

### Phase 4: Gestion Clients & Fidélité (Semaine 7)

**Priorité:** Important pour la relation client

**Backend:**
- [ ] Endpoints CRUD clients
- [ ] Calcul automatique stats client
- [ ] Logique attribution points fidélité
- [ ] Utilisation points lors paiement
- [ ] Historique mouvements points
- [ ] Trigger mise à jour après commande payée

**Frontend:**
- [ ] Page liste clients (recherche, filtres)
- [ ] Formulaire création/édition client
- [ ] Page détail client (stats, historique achats)
- [ ] Tableau de bord fidélité client
- [ ] Historique points
- [ ] Intégration POS (recherche client, utilisation points)

**Tests:**
- [ ] Création client
- [ ] Vente avec attribution points automatique
- [ ] Utilisation points lors vente
- [ ] Historique complet client

---

### Phase 5: Vente à Crédit (Semaine 8)

**Priorité:** Fonctionnalité essentielle pour certains commerces

**Backend:**
- [ ] Logique création commande non payée
- [ ] Endpoints paiements partiels
- [ ] Trigger mise à jour montants (payé/restant)
- [ ] Vue dettes clients

**Frontend:**
- [ ] Option "Vente à crédit" dans POS
- [ ] Page gestion crédits clients
- [ ] Modal paiement partiel
- [ ] Historique paiements par commande
- [ ] Dashboard dettes (montants, ancienneté)

**Tests:**
- [ ] Création commande à crédit
- [ ] Paiement partiel 1
- [ ] Paiement partiel 2
- [ ] Paiement final (statut → Payé)
- [ ] Attribution points seulement après paiement complet

---

### Phase 6: Codes Promo & Promotions (Semaine 9)

**Priorité:** Fonctionnalité marketing importante

**Backend:**
- [ ] Table `promo_codes` et `promo_code_usage`
- [ ] Endpoints CRUD codes promo
- [ ] Logique validation code (dates, montant min, utilisations)
- [ ] Application remise lors du paiement
- [ ] Historique utilisations par client
- [ ] Endpoints statistiques promo (nombre d'utilisations, CA généré)

**Frontend:**
- [ ] Page gestion codes promo (liste, création, édition)
- [ ] Formulaire création code (type, valeur, conditions)
- [ ] Intégration POS (champ saisie code promo)
- [ ] Affichage remise appliquée dans panier
- [ ] Validation en temps réel (code valide/invalide)
- [ ] Statistiques codes promo (dashboard)

**Tests:**
- [ ] Création code promo pourcentage
- [ ] Création code promo montant fixe
- [ ] Application code avec montant minimum
- [ ] Vérification limite utilisations globale
- [ ] Vérification limite utilisations par client
- [ ] Code expiré rejeté

---

### Phase 7: Retours & Remboursements (Semaine 10)

**Priorité:** Essentiel pour la satisfaction client

**Backend:**
- [ ] Ajout statuts "Rembourser" et "Partiellement Rembourser"
- [ ] Mise à jour trigger `update_order_payment_status` (gestion refunds)
- [ ] Trigger `restock_after_refund` (réintégration stock)
- [ ] Endpoints remboursement total/partiel
- [ ] Validation (commande payée, quantités retournées)
- [ ] Génération PDF avoir/note de crédit
- [ ] Déduction points fidélité

**Frontend:**
- [ ] Page gestion retours/remboursements
- [ ] Recherche commande à rembourser
- [ ] Interface remboursement total
- [ ] Interface remboursement partiel (sélection articles)
- [ ] Affichage statut remboursement
- [ ] Historique remboursements
- [ ] Téléchargement PDF avoir

**Tests:**
- [ ] Remboursement total commande
- [ ] Remboursement partiel (quelques articles)
- [ ] Vérification réintégration stock automatique
- [ ] Vérification déduction points fidélité
- [ ] Vérification ajustement session caisse
- [ ] Tentative remboursement commande non payée (rejetée)

---

### Phase 8: Module RH Simple (Semaine 11)

**Priorité:** Gestion basique des employés

**Backend:**
- [ ] Table `employees` (extension users)
- [ ] Endpoints CRUD employés
- [ ] Endpoints statistiques performance par employé
  - Nombre de ventes par vendeur
  - CA généré par vendeur
  - Sessions caisse par caissier (total encaissé, écarts)
- [ ] Export Excel pour paie

**Frontend:**
- [ ] Page liste employés (filtres poste, statut)
- [ ] Formulaire ajout/édition employé
- [ ] Fiche employé (infos + performances)
- [ ] Dashboard performance employés
- [ ] Historique sessions caisse par caissier
- [ ] Export Excel données employés

**Tests:**
- [ ] Création employé avec poste
- [ ] Consultation performances vendeur
- [ ] Historique sessions caissier
- [ ] Export Excel pour paie

---

### Phase 9: Intégration E-commerce Mafalia (Semaine 12)

**Priorité:** Extension canal de vente

**Backend:**
- [ ] Adaptation endpoints API pour frontend Mafalia
- [ ] Authentification clients (séparée magasin)
- [ ] Endpoints catalogue public (produits actifs)
- [ ] Type commande "online" ajouté
- [ ] Statut "en attente de paiement" pour commandes web
- [ ] Gestion retours e-commerce (délai légal)
- [ ] Méthodes paiement e-commerce (carte en ligne)

**Frontend (adaptation):**
- [ ] Configuration connexion API Commercia
- [ ] Synchronisation catalogue produits
- [ ] Affichage stock temps réel
- [ ] Gestion commandes web dans POS
- [ ] Distinction visuelle commandes online
- [ ] Gestion statut "en attente de paiement"

**Tests:**
- [ ] Création commande depuis storefront
- [ ] Synchronisation stock POS ↔ e-commerce
- [ ] Commande online apparaît dans POS
- [ ] Paiement commande web
- [ ] Retour e-commerce

---

### Phase 10: Réservations & Locations (Semaines 13-14)

**Priorité:** Module distinct, peut être développé en parallèle

**Backend:**
- [ ] Endpoints CRUD services
- [ ] Gestion disponibilités/créneaux
- [ ] Vérification conflits réservations
- [ ] Endpoints CRUD réservations
- [ ] Logique cautions/acomptes
- [ ] Workflow remboursements/déductions

**Frontend:**
- [ ] Page gestion services
- [ ] Calendrier disponibilités
- [ ] Interface réservation (sélection créneau)
- [ ] Vérification disponibilité temps réel
- [ ] Gestion cautions (encaissement/remboursement)
- [ ] Page liste réservations (filtres, statuts)
- [ ] Page détail réservation

**Tests:**
- [ ] Création service avec créneaux
- [ ] Réservation simple
- [ ] Détection conflit créneau
- [ ] Réservation avec caution (workflow complet)
- [ ] Remboursement caution
- [ ] Déduction caution (dommages)

---

### Phase 11: Dashboard & Rapports (Semaine 15)

**Priorité:** Interface principale pour pilotage

**Backend:**
- [ ] Endpoints KPIs (CA, panier moyen, dépenses, solde)
- [ ] Graphiques (revenus, commandes, dépenses)
- [ ] Top produits vendus
- [ ] Heures de pointe (pick meal)
- [ ] Répartition canaux/paiements
- [ ] Endpoints rapports avancés (inventaire, marge, ABC)

**Frontend:**
- [ ] Dashboard principal (KPIs)
- [ ] Filtres temporels (jour/semaine/mois/custom)
- [ ] Graphiques interactifs (Chart.js ou Recharts)
- [ ] Activités récentes
- [ ] Balance canaux/paiements
- [ ] Pages rapports avancés
- [ ] Export Excel rapports

**Tests:**
- [ ] Vérification exactitude KPIs
- [ ] Filtres temporels fonctionnels
- [ ] Export Excel opérationnel

---

### Phase 12: Utilisateurs & Permissions (Semaine 16)

**Priorité:** Sécurité et gestion multi-utilisateurs

**Backend:**
- [ ] Endpoints gestion utilisateurs
- [ ] Middleware vérification rôles
- [ ] Row Level Security Supabase
- [ ] Audit trail (logs actions utilisateurs)

**Frontend:**
- [ ] Page gestion utilisateurs (liste, création, édition)
- [ ] Attribution rôles
- [ ] Affichage conditionnel selon permissions
- [ ] Page profil utilisateur
- [ ] Changement mot de passe

**Tests:**
- [ ] Création utilisateur par rôle
- [ ] Vérification permissions (admin peut tout, vendeur limité)
- [ ] Isolation données par magasin

---

### Phase 13: Paramètres & Configuration (Semaine 17)

**Priorité:** Personnalisation par magasin

**Backend:**
- [ ] Endpoints paramètres magasin
- [ ] Configuration TVA/taxes
- [ ] Paramètres fidélité (règle attribution points)
- [ ] Paramètres alertes stock

**Frontend:**
- [ ] Page paramètres généraux (infos magasin)
- [ ] Configuration fiscalité
- [ ] Configuration fidélité
- [ ] Configuration méthodes paiement
- [ ] Configuration alertes

**Tests:**
- [ ] Modification paramètres et vérification application
- [ ] Activation/désactivation TVA
- [ ] Modification règle points fidélité

---

### Phase 14: Tests, Optimisation & Déploiement (Semaine 18)

**Tests end-to-end:**
- [ ] Scénario complet: Ouverture caisse → Ventes → Fermeture
- [ ] Scénario multi-utilisateurs simultanés
- [ ] Tests de charge (50 utilisateurs simultanés)

**Optimisation:**
- [ ] Analyse performances (Lighthouse, Page Speed)
- [ ] Optimisation requêtes SQL
- [ ] Mise en place caching
- [ ] Compression images

**Déploiement:**
- [ ] Déploiement production Vercel
- [ ] Configuration domaine custom
- [ ] Configuration backup automatique
- [ ] Documentation utilisateur (mini-guide)

---

### Phase 15: Fonctionnalités futures (Post-MVP)

**À développer selon besoins:**

**Haute priorité:**
- [ ] Notifications SMS/Email (Twilio, SendGrid)
  - Alertes stock bas (gérant)
  - Notification commande prête (client)
  - Rappel rendez-vous (24h avant)
  - Relances paiements crédits
- [ ] Intégration API paiement (Wave, Orange Money)
  - Paiement automatique en ligne
  - Vérification transactions
  - Webhooks de confirmation
- [ ] Gestion dépenses avancée
  - Workflow validation (demande → approbation)
  - Pièces justificatives (upload factures)
  - Lien avec bons de commande fournisseurs
  - Catégories de dépenses multiples

**Priorité moyenne:**
- [ ] Promotions automatiques avancées
  - Remises par catégorie/marque
  - BOGO (Buy One Get One)
  - Happy hours / Tarifs horaires variables
  - Promotions cumulables avec règles
- [ ] Rapports personnalisés (query builder)
  - Création rapports custom
  - Export multi-format (PDF, Excel, CSV)
  - Planification envoi automatique
- [ ] Module RH avancé
  - Système de pointage (entrée/sortie)
  - Calcul automatique salaires + commissions
  - Gestion congés avec validation
  - Planning/horaires de travail
- [ ] QR Code paiement mobile
  - Génération QR code par commande
  - Scan pour paiement client
  - Intégration opérateurs mobiles

**Basse priorité:**
- [ ] Application mobile native (React Native)
  - Version mobile du POS
  - Gestion stock en mobilité
  - Notifications push
- [ ] Mode hors-ligne (PWA avec sync)
  - Fonctionnement sans connexion
  - Synchronisation automatique à la reconnexion
  - Gestion conflits
- [ ] Multi-magasins
  - Gestion plusieurs points de vente
  - Transferts inter-magasins
  - Rapports consolidés
  - Vue siège vs filiales

---

## 📝 CONCLUSION

Ce document de spécifications techniques fournit une base solide et complète pour démarrer le développement de **Commercia**. Les points clés:

### ✅ Points forts du projet
- Architecture moderne et scalable (Next.js + FastAPI + Supabase)
- Flux métier bien définis et complets (inspirés de Mafalia)
- Gestion produits flexible et scalable (flow adaptatif par type)
- Système caisse robuste avec réconciliation
- Programme fidélité intégré
- **Gestion complète des retours/remboursements avec réintégration stock automatique**
- **Système de codes promo flexible**
- **Module RH simple et efficace**
- **Intégration e-commerce Mafalia**

### ✅ Clarifications obtenues
- ✅ E-commerce: Intégration avec storefront Mafalia existant
- ✅ Retours/remboursements: Workflow complet avec nouveaux statuts "Rembourser" et "Partiellement Rembourser"
- ✅ Promotions: Système de codes promo avec conditions
- ✅ RH: Module simple avec suivi performances
- ✅ Multi-magasins: Confirmé NON (mono-magasin)
- ✅ Notifications: Post-MVP
- ✅ API Paiements: Post-MVP
- ✅ Gestion dépenses: Post-MVP (lié aux fournisseurs)

### 🎯 Priorités MVP (18 semaines)
1. **Gestion produits & stocks** (fondation) - Semaines 2-3
2. **POS & commandes** (cœur métier) - Semaines 4-5
3. **Caisse & paiements** (essentiel) - Semaine 6
4. **Clients & fidélité** (relation client) - Semaine 7
5. **Vente à crédit** (créances) - Semaine 8
6. **Codes promo** (marketing) - Semaine 9
7. **Retours & remboursements** (satisfaction client) - Semaine 10
8. **Module RH simple** (employés) - Semaine 11
9. **Intégration e-commerce** (canal web) - Semaine 12
10. **Réservations & locations** (services) - Semaines 13-14
11. **Dashboard & rapports** (pilotage) - Semaine 15
12. **Utilisateurs & permissions** (sécurité) - Semaine 16
13. **Paramètres & configuration** (personnalisation) - Semaine 17
14. **Tests & déploiement** (production) - Semaine 18

### 📊 Récapitulatif des modules
**Modules principaux (MVP):**
- ✅ Gestion Produits (flow scalable, variantes, unités multiples, SKU auto)
- ✅ Gestion Stocks (alertes, mouvements, inventaire)
- ✅ POS Omnicanal (pickup, livraison, online)
- ✅ Caisse & Sessions (ouverture/fermeture, réconciliation)
- ✅ Commandes & Paiements (immédiat, crédit, mixte)
- ✅ Clients & Fidélité (points, historique, stats)
- ✅ Codes Promo (validation, conditions, historique)
- ✅ Retours & Remboursements (total/partiel, réintégration stock)
- ✅ Module RH Simple (employés, performances)
- ✅ Réservations & Locations (créneaux, cautions)
- ✅ Dashboard & Rapports (KPIs, graphiques, exports)
- ✅ E-commerce (intégration Mafalia)

**Modules Post-MVP:**
- ⏳ Notifications SMS/Email
- ⏳ Intégration API Wave/Orange Money
- ⏳ Gestion dépenses avancée
- ⏳ Promotions automatiques complexes
- ⏳ Module RH avancé (pointage, salaires)
- ⏳ QR Code paiement mobile

### 🚀 Prochaines étapes immédiates
1. ✅ Document validé avec toutes les clarifications
2. Initialiser les repositories (backend + frontend)
3. Créer le schéma de base de données Supabase complet
   - 20+ tables incluant promo_codes, employees
   - 8 triggers automatiques (paiements, stock, fidélité, remboursements)
4. Commencer Phase 0 (Setup infrastructure)
5. Développer en sprints de 1 semaine par phase

### 📈 Estimations

**Durée MVP complet:** 18 semaines (4,5 mois)
- Phase 0: Setup - 1 semaine
- Phases 1-5: Core fonctionnel - 7 semaines
- Phases 6-9: Fonctionnalités avancées - 4 semaines
- Phases 10-13: Modules complémentaires - 5 semaines
- Phase 14: Tests & déploiement - 1 semaine

**Durée ajustable selon:**
- Réutilisation composants Figma existants (gain 20-30%)
- Complexité réelle module e-commerce (intégration Mafalia)
- Disponibilité et taille équipe
- Parallélisation de certains modules (réservations, RH)

### ⚠️ Risques identifiés et mitigations
1. **Intégration e-commerce Mafalia:** Nécessite coordination avec l'équipe existante
   - Mitigation: Définir contrat API clair dès le début
2. **Triggers complexes:** Remboursements + réintégration stock
   - Mitigation: Tests unitaires rigoureux sur les triggers
3. **Performances:** 50 utilisateurs simultanés avec temps réel
   - Mitigation: Indexation optimale + caching stratégique

### 🎓 Recommandations

**Architecture:**
- Utiliser Redis pour caching (dashboard stats, catalogues)
- Implémenter Rate Limiting sur endpoints sensibles
- Configurer Row Level Security Supabase dès le début

**Développement:**
- Tests unitaires dès Phase 1 (TDD)
- Documentation API automatique (FastAPI SwaggerUI)
- Code review systématique

**Déploiement:**
- Environnements: dev, staging, prod
- CI/CD automatique (GitHub Actions)
- Monitoring (Sentry pour erreurs, Analytics)

---

**Document rédigé le:** 2026-01-12
**Version:** 2.0 (Mise à jour après clarifications)
**Auteur:** Claude (Assistant IA) avec informations fournies par l'équipe projet

**Changelog:**
- **v2.0 (2026-01-12):** Ajout workflow remboursements, codes promo, module RH, intégration e-commerce, mise à jour feuille de route (18 semaines)
- **v1.0 (2026-01-12):** Version initiale

**Dernière mise à jour:** 2026-01-12
**Statut:** ✅ Validé et prêt pour développement
