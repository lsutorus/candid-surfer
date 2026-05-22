import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.sessions import router as sessions_router
from app.routers.spots import router as spots_router
from app.routers.uploads import router as uploads_router
from app.routers.webhooks import router as webhooks_router
from app.routers.purchases import router as purchases_router

app = FastAPI(title="Candid Surfer", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions_router)
app.include_router(spots_router)
app.include_router(uploads_router)
app.include_router(webhooks_router)
app.include_router(purchases_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
