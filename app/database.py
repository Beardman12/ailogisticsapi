from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.config import settings


connect_args: dict[str, bool] = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    sqlite_path = settings.database_url.removeprefix("sqlite:///")
    if sqlite_path:
        Path(sqlite_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
_db_initialized = False


def ensure_initialized() -> None:
    global _db_initialized
    if _db_initialized:
        return
    Base.metadata.create_all(bind=engine)
    _db_initialized = True


def get_db() -> Generator[Session, None, None]:
    ensure_initialized()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
