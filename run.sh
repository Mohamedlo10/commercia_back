#!/bin/bash

# Script de démarrage rapide pour Commercia Backend
# Usage: ./run.sh [dev|prod|docker]

set -e

MODE=${1:-dev}

case $MODE in
  dev)
    echo "🚀 Démarrage en mode développement..."
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ;;

  prod)
    echo "🚀 Démarrage en mode production..."
    gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    ;;

  docker)
    echo "🐳 Build et démarrage avec Docker..."
    docker build -t commercia-api .
    docker run -p 8000:8000 --env-file .env commercia-api
    ;;

  test)
    echo "🧪 Lancement des tests..."
    pytest -v
    ;;

  *)
    echo "Usage: ./run.sh [dev|prod|docker|test]"
    echo "  dev    - Mode développement avec rechargement automatique"
    echo "  prod   - Mode production avec Gunicorn"
    echo "  docker - Build et run avec Docker"
    echo "  test   - Lancer les tests"
    exit 1
    ;;
esac
