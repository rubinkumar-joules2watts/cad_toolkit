import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routes import router


@router.get("/")
def read_root() -> dict[str, str]:
    return {"message": "MACROS Toolkit is running"}


def _cors_origins() -> list[str]:
    """
    Browsers reject Access-Control-Allow-Origin: * when Access-Control-Allow-Credentials
    is true — so we never combine * with allow_credentials=True.

    Set CORS_ORIGINS to a comma-separated list on the server (e.g. Render) for extra
    frontends: https://app.example.com,http://1.2.3.4:5173
    """
    raw = os.getenv("CORS_ORIGINS", "").strip()
    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()]
    return [
        "http://localhost:8080",
        "http://localhost:8081",
        "http://localhost:5173",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8081",
        "http://127.0.0.1:5173",
        "http://140.238.227.29:5173",
        "https://macromaster-suite.vercel.app",
    ]


app = FastAPI(title="MACROS Toolkit")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
    ],
)

app.include_router(router)
