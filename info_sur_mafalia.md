📦 MODULE COMMANDES (Orders)
Vue d'ensemble
Le module Commandes gère l'ensemble du cycle de vie d'une commande, de la création jusqu'au paiement et au suivi.

Flux de fonctionnement
1. Création de commande
Étapes :

L'utilisateur sélectionne le type de commande :

- Pickup (à récupérer)
- Livraison : nécessite adresse, téléphone, mode de livraison (rapide/standard)
L'utilisateur ajoute des produits au panier avec :

Quantités
Variantes (tailles, options)
Extras (suppléments)
Notes spéciales
2. Paiement
Le système collecte :

Informations client (nom, téléphone, type de client)
Application de remises et codes promo
Utilisation de points de fidélité
Sélection du mode de paiement (espèces, carte, mobile money, etc.)
Deux scénarios possibles :

A. Commande payée immédiatement :

- Crée la commande avec `status_commande` = "confirme"
- Enregistre les produits commandés
- Crée automatiquement une transaction liée
- Déduit les points de fidélité si utilisés
- Définit `statut_paiement` = "Payer"
- Ajoute la vente à la session de caisse

B. Commande sans paiement immédiat (paiement différé ou partiel) :

- Crée la commande avec `status_commande` = "confirme"
- `statut_paiement` = "Non Payer" ou "Partiellement" selon le cas
- Le paiement sera traité plus tard ou par paiements partiels
- Pas (ou pas encore) de transaction finale marquant la commande comme complètement payée
3. Cycle de vie des statuts
La gestion des statuts est désormais séparée en deux axes distincts : `statut_paiement` et `status_commande`.

- `statut_paiement` (indique l'état du paiement) :
	- `Payer` — paiement complet reçu
	- `Non Payer` — aucun paiement reçu
	- `Partiellement` — paiement partiel reçu

- `status_commande` (état opérationnel de la commande) :
	- `confirme` — commande enregistrée et validée
	- `pret` — commande préparée et prête pour pickup ou livraison
	- point de terminaison : `terminee` (pour les commandes `pickup`) ou `livree` (pour les commandes `livraison`)

Règles importantes :

- Une commande déjà totalement payée (`statut_paiement` = `Payer`) ne peut plus être modifiée sans action d'annulation/remboursement.
- Le statut terminal dépend du type de commande : seul le type `livraison` peut atteindre `livree`.
- Le paiement nécessite obligatoirement une session de caisse ouverte pour créer des transactions liées.
4. Gestion des commandes
Fonctionnalités disponibles :

Liste des commandes avec filtres (statut, type, date)
Recherche de commandes
Affichage cuisine pour les chefs
Modification (seulement si non payée)
Historique client avec toutes ses commandes
Intégrations clés
Avec les clients
Les commandes sont liées au profil client
Mise à jour automatique :
Date de dernière commande
Total dépensé cumulé
Nombre de commandes
Gestion des points de fidélité :
Utilisation lors du paiement
Déduction automatique après validation
Avec les produits
Liaison avec le catalogue produits
Support des variantes (tailles, options)
Support des extras (suppléments)
Calcul automatique des prix unitaires et sous-totaux
Aucune gestion de table n'est requise — l'application gère uniquement les commandes de type `pickup` et `livraison`.
Avec la caisse
Obligatoire : session de caisse ouverte pour créer une commande payée
Chaque paiement crée une transaction
Les ventes sont automatiquement ajoutées au total de la session
💰 MODULE CAISSE (Cash Register)
Vue d'ensemble
Le module Caisse gère l'ouverture/fermeture des sessions de caisse, l'enregistrement des transactions, et la réconciliation des fonds.

Flux de fonctionnement
1. Ouverture de session
Processus :

L'utilisateur initie l'ouverture
Sélection du caissier (si l'utilisateur n'est pas caissier)
Saisie du montant initial (fond de caisse)
Vérification : une seule session ouverte par restaurant
Création de la session avec :
Montant initial
Total des ventes : 0
Total des dépenses : 0
Solde théorique : montant initial
Statut : "ouvert"
Heure d'ouverture
Important : Sans session ouverte, impossible de créer des commandes payées !

2. Enregistrement des transactions
À chaque vente (commande payée) :

Création d'une transaction avec :

Type : "sale" (vente)
Montant
Méthode de paiement utilisée
Référence à la commande
Nom et téléphone du client
Numéro de transaction unique
Statut : "completed"
Mise à jour automatique de la session :

Total des ventes += montant
Montant final += montant
Liaison complète :

Transaction ← Session
Transaction ← Commande
Transaction ← Méthode de paiement
Transaction ← Utilisateur/caissier
3. Suivi en temps réel
Le système calcule automatiquement :

Total des ventes du jour/période
Nombre de transactions
Répartition par méthode de paiement :
Espèces (montant + nombre)
Mobile Money (Wave, Orange Money, MTN)
Carte bancaire
Chèque, TPE, etc.
Vue "Entrées de caisse" affiche :

Total du jour
Liste des transactions récentes
Filtres par période (aujourd'hui, semaine, mois, tout)
Badges de méthode de paiement
4. Fermeture de session et réconciliation
Processus :

L'utilisateur clique sur "Fermer la session"
Saisie du montant réel (comptage physique de la caisse)
Ajout de notes optionnelles
Le système calcule automatiquement :


Solde théorique = Montant initial + Total ventes - Total dépenses
Écart = Montant réel - Solde théorique
Résultat :

Écart positif : surplus de caisse
Écart négatif : manque en caisse
La session est verrouillée (statut "closed")
Aucune modification possible après fermeture
Traçabilité complète pour audit
Règles métier importantes
Contraintes strictes
Une seule session ouverte par restaurant à la fois
Session obligatoire pour tout paiement de commande
Sessions verrouillées après fermeture (immuable)
Transactions liées : impossible de supprimer sans traçabilité
Méthodes de paiement
Méthodes supportées :

Espèces (Cash)
Carte bancaire
Mobile Money :
Wave
Orange Money
Mixx by Yaas (MTN)
Wari
TPE (Terminal de paiement)
Chèque
Chaque méthode peut avoir :

Nom affiché
Code système
Icône
Statut actif/inactif
Champs de formulaire spécifiques
Réconciliation et audit
Données conservées :

Heure d'ouverture/fermeture
Caissier responsable
Montant initial vs montant final
Solde théorique vs réel
Écart constaté
Notes de réconciliation
Toutes les transactions de la session
Utilité :

Suivi des performances caissier
Détection d'anomalies
Audit comptable
Rapports financiers
Intégrations clés
Avec les commandes
Blocage : pas de commande payée sans session ouverte
Chaque paiement génère une transaction
Mise à jour en temps réel du total de la session
Avec les utilisateurs/caissiers
Attribution de la session à un caissier
Traçabilité de qui a ouvert/fermé
Lien avec les employés (informations_employees)
Avec les restaurants
Isolation par restaurant : chaque restaurant a ses propres sessions
Support multi-restaurant
Avec le wallet (portefeuille)
"Alimenter le wallet" : transfert de la caisse vers le portefeuille
"Remise de caisse" : retrait de fonds du registre
🔗 Points de connexion entre les deux modules
Commandes → Caisse
Chaque commande payée crée une transaction
La transaction est liée à la session de caisse ouverte
Le montant est ajouté automatiquement au total des ventes
Caisse → Commandes
Session ouverte obligatoire pour valider un paiement
Blocage des paiements si aucune session active
Traçabilité complète via transaction.order_reference
Flux complet

1. Ouverture session caisse
2. Création commande (panier)
3. Paiement → vérifie session ouverte
4. Création transaction liée
5. Mise à jour session (total ventes)
6. Commande passe à "payée"
7. [répétition pour autres commandes]
8. Fermeture session avec réconciliation
Cette logique assure une traçabilité financière complète, une gestion rigoureuse des fonds, et une intégration fluide entre la prise de commande et l'encaissement.