from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from db.models import Base
import os
from contextlib import contextmanager
from dotenv import load_dotenv
from db.logger_setup import setup_logger

# Load environment variables
load_dotenv()

# Set up the logger
logger = setup_logger()

# Load database URL from configuration
DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URI")

# Create the engine and initialize the database
# engine = create_engine(
#     DATABASE_URL,
#     pool_size=10,        # Maximum number of persistent connections
#     max_overflow=5,      # Allow up to 5 additional temporary connections
#     pool_recycle=1800,   # Close connections after 30 minutes (adjust if needed)
#     pool_pre_ping=True   # Ensure connections are alive before using them
# )

engine = create_engine(
    DATABASE_URL,
    pool_size=25,     
    max_overflow=10,  
    pool_recycle=1800,   
    pool_pre_ping=True   
)
# Base.metadata.create_all(bind=engine)
with engine.connect() as conn:
    # TODO: Should rather switch to using Alembic
    Base.metadata.create_all(bind=conn)

# Create a configured session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()  # Ensure changes are committed
    except Exception as e:
        session.rollback()  # Rollback on error
        logger.error("Error in database transaction")
        logger.exception(e)
        raise  # Re-raise exception for visibility
    finally:
        session.close()