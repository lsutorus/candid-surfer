"""Seed the database with approved surf spots."""

import os
import uuid

from sqlmodel import Session, select

from app.db import engine
from app.models import Spot

SPOTS = [
    {
        "id": uuid.UUID("a1b2c3d4-0001-4000-8000-000000000001"),
        "name": "Pipeline",
        "lat": 21.6654,
        "lng": -158.0525,
        "timezone": "Pacific/Honolulu",
        "is_approved": True,
    },
    {
        "id": uuid.UUID("a1b2c3d4-0002-4000-8000-000000000002"),
        "name": "Lowers",
        "lat": 33.3858,
        "lng": -117.5922,
        "timezone": "America/Los_Angeles",
        "is_approved": True,
    },
    {
        "id": uuid.UUID("a1b2c3d4-0003-4000-8000-000000000003"),
        "name": "Uluwatu",
        "lat": -8.8291,
        "lng": 115.0849,
        "timezone": "Asia/Makassar",
        "is_approved": True,
    },
]


def seed() -> None:
    with Session(engine) as session:
        for spot_data in SPOTS:
            existing = session.get(Spot, spot_data["id"])
            if existing is None:
                session.add(Spot(**spot_data))
        session.commit()
    print(f"Seeded {len(SPOTS)} spots")


if __name__ == "__main__":
    seed()
