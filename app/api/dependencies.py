from typing import Generator
from sqlmodel import Session
from app.database.database import engine


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session

    Yields:
        Database session
    """
    with Session(engine) as session:
        yield session
