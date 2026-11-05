from fastapi import APIRouter

from src.api.v1 import auth, user

ROUTERS: list[APIRouter] = [
    auth.router,
    user.router,
]

api_router = APIRouter()

for router in ROUTERS:
    api_router.include_router(router)
