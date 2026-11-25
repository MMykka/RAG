from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# pool_recycle: replace a pooled connection once it is 5 minutes old, instead of pool_pre_ping
# (which tested every connection with an extra database trip before each request).
engine = create_engine(settings.database_url, pool_recycle=300)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
