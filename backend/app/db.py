import os

from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is missing! Copy backend/.env.example to backend/.env and fill in your Supabase connection string."
    )
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(DATABASE_URL)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)
