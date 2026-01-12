# Makefile pour Commercia Backend

.PHONY: help install dev prod test clean docker-build docker-run format lint

help: ## Affiche l'aide
	@echo "Commandes disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Installe les dépendances
	pip install -r requirements.txt

install-dev: ## Installe les dépendances de développement
	pip install -r requirements.txt
	pip install pytest pytest-asyncio httpx black flake8 mypy

dev: ## Démarre le serveur en mode développement
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

prod: ## Démarre le serveur en mode production
	gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

test: ## Lance les tests
	pytest -v

test-cov: ## Lance les tests avec couverture
	pytest --cov=app --cov-report=html --cov-report=term

clean: ## Nettoie les fichiers temporaires
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

docker-build: ## Build l'image Docker
	docker build -t commercia-api .

docker-run: ## Run le container Docker
	docker run -p 8000:8000 --env-file .env commercia-api

docker-clean: ## Nettoie les images Docker
	docker rmi commercia-api || true

format: ## Formate le code avec Black
	black app/ tests/

lint: ## Vérifie le code avec flake8
	flake8 app/ tests/ --max-line-length=120

type-check: ## Vérifie les types avec mypy
	mypy app/

db-init: ## Initialise la base de données (doit avoir psql installé)
	psql $(DATABASE_URL) < database/init.sql

migrate: ## Lance les migrations Alembic
	alembic upgrade head

migrate-create: ## Crée une nouvelle migration
	alembic revision --autogenerate -m "$(message)"

logs: ## Affiche les logs en temps réel (si utilisation de Docker Compose)
	docker-compose logs -f

shell: ## Ouvre un shell Python avec le contexte de l'app
	python -i -c "from app.main import app; from app.core.database import get_db"

requirements: ## Génère requirements.txt depuis l'environnement actuel
	pip freeze > requirements.txt

check: format lint type-check test ## Lance tous les checks (format, lint, type, tests)

.DEFAULT_GOAL := help
