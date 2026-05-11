from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routes import router


@router.get("/")
def read_root() -> dict[str, str]:
    return {"message": "MACROS Toolkit is running"}


app = FastAPI(title="MACROS Toolkit")

ALLOWED_ORIGINS = [
    "http://localhost:8080",
    "http://localhost:8081",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:8081",
    "https://macromaster-suite.vercel.app",
    "http://140.238.227.29:5173",
]

ALLOWED_METHODS = ["GET", "POST", "OPTIONS"]

ALLOWED_HEADERS = [
    "Accept",
    "Accept-Language",
    "Content-Language",
    "Content-Type",
    "Authorization",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=ALLOWED_METHODS,
    allow_headers=ALLOWED_HEADERS,
)

app.include_router(router)
