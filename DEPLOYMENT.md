# Guide de Déploiement - Commercia Backend

Ce guide détaille les étapes pour déployer l'API Commercia en production sur Render avec Supabase.

## Table des matières

1. [Prérequis](#prérequis)
2. [Configuration Supabase](#configuration-supabase)
3. [Déploiement sur Render](#déploiement-sur-render)
4. [Configuration post-déploiement](#configuration-post-déploiement)
5. [Monitoring](#monitoring)
6. [Rollback](#rollback)

## Prérequis

- ✅ Compte GitHub avec le repository du projet
- ✅ Compte Supabase (gratuit ou payant)
- ✅ Compte Render (gratuit ou payant)
- ✅ Frontend déployé sur Vercel (pour CORS)

## Configuration Supabase

### 1. Créer un projet Supabase

1. Connectez-vous à [Supabase](https://supabase.com)
2. Cliquez sur "New Project"
3. Remplissez les informations :
   - **Name**: commercia-production
   - **Database Password**: Générez un mot de passe fort
   - **Region**: Choisissez la région la plus proche (Frankfurt pour l'Europe/Afrique)
   - **Pricing Plan**: Choisissez selon vos besoins

### 2. Exécuter le script SQL

1. Dans votre projet Supabase, allez dans **SQL Editor**
2. Cliquez sur "New Query"
3. Copiez tout le contenu du fichier `database/init.sql`
4. Exécutez le script (cela peut prendre 1-2 minutes)
5. Vérifiez qu'il n'y a pas d'erreurs

### 3. Récupérer les credentials

1. Allez dans **Settings > Database**
2. Copiez la **Connection String** en mode "URI" :
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
   ```
3. Convertissez-la pour asyncpg :
   ```
   postgresql+asyncpg://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
   ```

### 4. Configurer Row Level Security (RLS)

Les politiques RLS sont activées par le script SQL. Pour les personnaliser :

1. Allez dans **Authentication > Policies**
2. Ajustez les politiques selon vos besoins

## Déploiement sur Render

### Option 1 : Déploiement automatique avec render.yaml

1. **Préparer le repository**
   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```

2. **Créer un service sur Render**
   - Allez sur [Render Dashboard](https://dashboard.render.com)
   - Cliquez sur "New +" → "Blueprint"
   - Connectez votre repository GitHub
   - Render détectera automatiquement le fichier `render.yaml`
   - Cliquez sur "Apply"

3. **Configurer les variables d'environnement**

   Les variables suivantes seront créées automatiquement, mais vous devrez les personnaliser :

   | Variable | Valeur | Description |
   |----------|--------|-------------|
   | `ENVIRONMENT` | `production` | Environnement |
   | `DEBUG` | `false` | Mode debug |
   | `SECRET_KEY` | Auto-généré | Clé secrète JWT |
   | `DATABASE_URL` | Votre URL Supabase | Connexion DB |
   | `BACKEND_CORS_ORIGINS` | `["https://votre-frontend.vercel.app"]` | URLs autorisées |

4. **Modifier render.yaml si nécessaire**

   Éditez le fichier `render.yaml` :
   ```yaml
   services:
     - type: web
       name: commercia-api
       repo: https://github.com/votre-org/commercia  # ← Changez ici
       branch: main
       # ... rest of config
   ```

### Option 2 : Déploiement manuel

1. **Créer un Web Service**
   - Allez sur Render Dashboard
   - Cliquez sur "New +" → "Web Service"
   - Connectez votre repository

2. **Configuration du service**
   - **Name**: `commercia-api`
   - **Runtime**: Python 3
   - **Branch**: main
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT`

3. **Ajouter les variables d'environnement**

   Allez dans **Environment** et ajoutez :

   ```bash
   ENVIRONMENT=production
   DEBUG=false
   SECRET_KEY=<générer-une-clé-sécurisée>
   DATABASE_URL=<votre-url-supabase>
   BACKEND_CORS_ORIGINS=["https://votre-frontend.vercel.app"]
   ACCESS_TOKEN_EXPIRE_MINUTES=10080
   ALGORITHM=HS256
   ```

4. **Déployer**
   - Cliquez sur "Create Web Service"
   - Attendez que le déploiement se termine (5-10 minutes)

## Configuration post-déploiement

### 1. Vérifier le déploiement

Une fois déployé, testez les endpoints :

```bash
# Health check
curl https://votre-api.onrender.com/health

# Documentation
https://votre-api.onrender.com/api/docs
```

### 2. Créer le premier utilisateur admin

Utilisez l'endpoint de register pour créer un admin :

```bash
curl -X POST https://votre-api.onrender.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@commercia.com",
    "password": "SecurePassword123!",
    "role": "admin",
    "store_id": "<votre-store-id>"
  }'
```

**Note** : Créez d'abord un Store dans Supabase SQL Editor :
```sql
INSERT INTO stores (name, currency) VALUES ('Ma Boutique', 'XOF') RETURNING id;
```

### 3. Configurer le frontend

Dans votre application frontend Vercel, configurez :

```env
NEXT_PUBLIC_API_URL=https://votre-api.onrender.com/api/v1
```

### 4. Tester l'intégration

1. Ouvrez votre frontend
2. Essayez de vous connecter avec l'utilisateur admin créé
3. Vérifiez que les requêtes API fonctionnent

## Monitoring

### Logs Render

1. Dans Render Dashboard, sélectionnez votre service
2. Allez dans l'onglet **Logs**
3. Vous verrez tous les logs en temps réel

### Métriques Supabase

1. Dans Supabase, allez dans **Reports**
2. Surveillez :
   - Nombre de connexions
   - Requêtes par seconde
   - Utilisation du stockage

### Health Checks

Render vérifie automatiquement `/health` toutes les 30 secondes.

## Mise à jour de l'application

### Déploiement continu

Render redéploie automatiquement à chaque push sur la branche `main` :

```bash
git add .
git commit -m "Ajout de nouvelles fonctionnalités"
git push origin main
```

### Déploiement manuel

Dans Render Dashboard :
1. Sélectionnez votre service
2. Cliquez sur "Manual Deploy" → "Deploy latest commit"

## Rollback

Si un déploiement cause des problèmes :

1. Dans Render Dashboard, allez dans **Events**
2. Trouvez le dernier déploiement stable
3. Cliquez sur "Rollback to this version"

Ou via Git :

```bash
# Revenir au commit précédent
git revert HEAD
git push origin main
```

## Optimisations Production

### 1. Mise en cache

Activez le caching Redis (optionnel) :
- Créer un service Redis sur Render
- Ajouter la variable `REDIS_URL`
- Implémenter le caching dans le code

### 2. CDN pour les assets

Si vous servez des images :
- Utilisez Cloudflare ou Cloudinary
- Configurez les URLs dans les settings

### 3. Scaling

Pour gérer plus de trafic :
1. Augmentez le nombre de workers Gunicorn
2. Passez à un plan Render supérieur
3. Activez l'autoscaling dans `render.yaml`

## Sécurité

### Checklist de sécurité

- ✅ `DEBUG=false` en production
- ✅ `SECRET_KEY` fort et unique
- ✅ HTTPS activé (automatique sur Render)
- ✅ CORS configuré avec les URLs exactes
- ✅ RLS activé sur Supabase
- ✅ Mots de passe hashés avec bcrypt
- ✅ Rate limiting (à implémenter si besoin)

### Renouveler le SECRET_KEY

Si vous devez changer la clé secrète :

1. Générez une nouvelle clé :
   ```python
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. Mettez à jour dans Render Environment Variables

3. Redéployez (tous les tokens JWT seront invalidés)

## Support

### Problèmes courants

**Erreur de connexion DB**
- Vérifiez que l'URL DATABASE_URL est correcte
- Vérifiez que Supabase autorise les connexions depuis Render

**CORS errors**
- Vérifiez `BACKEND_CORS_ORIGINS` contient l'URL exacte du frontend
- Pas de trailing slash dans les URLs

**502 Bad Gateway**
- Vérifiez les logs Render
- Vérifiez que Gunicorn démarre correctement

### Contacts

- Documentation Render : https://render.com/docs
- Documentation Supabase : https://supabase.com/docs
- Issues GitHub : [votre-repo]/issues

---

**Version du guide:** 1.0
**Dernière mise à jour:** 2026-01-12
