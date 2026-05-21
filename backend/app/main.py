from fastapi import FastAPI

from app.routers.sessions import router as sessions_router
from app.routers.uploads import router as uploads_router
from app.routers.webhooks import router as webhooks_router
from app.routers.purchases import router as purchases_router

app = FastAPI(title="Candid Surfer", version="0.1.0")

app.include_router(sessions_router)
app.include_router(uploads_router)
app.include_router(webhooks_router)
app.include_router(purchases_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
