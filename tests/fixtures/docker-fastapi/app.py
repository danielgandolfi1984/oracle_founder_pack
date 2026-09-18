import os

from fastapi import FastAPI


app = FastAPI()


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/database-configured")
def database_configured() -> dict[str, bool]:
    return {
        "configured": bool(os.environ.get("DATABASE_URL")),
        "payments_configured": bool(os.environ.get("PAYMENTS_API_KEY")),
    }
