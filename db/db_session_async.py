from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os
from contextlib import asynccontextmanager

# Load database URL (must use an async driver, e.g., asyncpg for PostgreSQL)
DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URI").replace("postgresql://", "postgresql+asyncpg://")

# Create the async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Initialize the database metadata
Base = declarative_base()

# Create an async session factory
SessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

@asynccontextmanager
async def get_async_session():
    """
    Provides a transactional scope for async database operations.
    """
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()