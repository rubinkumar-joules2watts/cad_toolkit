from fastapi import APIRouter

from src.macros.route import router as macros_router


router = APIRouter()


router.include_router(macros_router)
