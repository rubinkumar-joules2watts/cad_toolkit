from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routes import router


@router.get("/")
def read_root() -> dict[str, str]:
    return {"message": "MACROS Toolkit is running"}


app = FastAPI(title="MACROS Toolkit")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
