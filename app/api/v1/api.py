"""
Router principal API v1
Agrège tous les routers de l'API
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth

api_router = APIRouter()

# Inclure tous les routers
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])

# À ajouter au fur et à mesure:
# api_router.include_router(products.router, prefix="/products", tags=["Products"])
# api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
# api_router.include_router(clients.router, prefix="/clients", tags=["Clients"])
# api_router.include_router(cash_register.router, prefix="/cash-register", tags=["Cash Register"])
# etc.
