from fastapi import FastAPI

from app.routers.sessions import router as sessions_router

app = FastAPI(title="Candid Surfer", version="0.1.0")

app.include_router(sessions_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
