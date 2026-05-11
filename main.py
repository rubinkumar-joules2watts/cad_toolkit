from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routes import router


@router.get("/")
def read_root() -> dict[str, str]:
    return {"message": "MACROS Toolkit is running"}


app = FastAPI(title="MACROS Toolkit")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://localhost:8081",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8081",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
