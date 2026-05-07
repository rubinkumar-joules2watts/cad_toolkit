from fastapi import FastAPI


app = FastAPI(title="CAD Toolkit API")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "CAD Toolkit API is running"}
