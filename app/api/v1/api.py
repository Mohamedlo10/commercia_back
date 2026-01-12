"""
Router principal API v1
Agrège tous les routers de l'API
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, categories, products, clients, stock

api_router = APIRouter()

# Inclure tous les routers
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(categories.router, tags=["Categories"])
api_router.include_router(products.router, tags=["Products"])
api_router.include_router(clients.router, tags=["Clients"])
api_router.include_router(stock.router, tags=["Stock"])

# À ajouter au fur et à mesure:
# api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
# api_router.include_router(cash_register.router, prefix="/cash-register", tags=["Cash Register"])
# api_router.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
# api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
# etc.
