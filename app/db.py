from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dummy.db") 

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
)

sessionLocal = sessionmaker(bind=engine,autoflush = False, autocommit = False)

def get_db():
    db=sessionLocal()
    try:
        yield db
    finally:
        db.close()