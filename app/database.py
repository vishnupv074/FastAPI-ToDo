import os
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import OperationalError

# Fetch environment variables for database connection
HOST = os.environ.get("DB_HOST")
USER = os.environ.get("DB_USER")
PASSWORD = os.environ.get("DB_PASS")
NAME = os.environ.get("DB_NAME")

# Construct the database URL for PostgreSQL
SQLALCHEMY_DATABASE_URL = f"postgresql://{USER}:{PASSWORD}@{HOST}/{NAME}"

"""
This configuration is specific to SQLite and needs adjustments
for other databases. Example for SQLite:
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
"""

# Creating the database engine for PostgreSQL
# engine = create_engine(SQLALCHEMY_DATABASE_URL)
# Retry logic
while True:
    try:
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        engine.connect()
        break
    except OperationalError:
        print("Database unavailable, waiting...")
        time.sleep(5)

# SessionLocal will create a new Session for each request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for the declarative model
Base = declarative_base()
