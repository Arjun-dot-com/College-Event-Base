from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# This creates a local SQLite database file named 'events_app.db' in your project directory
SQLALCHEMY_DATABASE_URL = "sqlite:///./events_app.db"

# connect_args={"check_same_thread": False} is required specifically for SQLite in FastAPI
# to prevent errors when multiple requests try to access the database at the same time.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# This creates a database session factory that we use in main.py to interact with the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)