import os
import urllib.parse
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# print(f"Connecting to database: {DB_NAME} at {DB_HOST}:{DB_PORT} as {DB_USER}")

# URL encode the password to handle special characters like '@'
if DB_PASSWORD:
    encoded_password = urllib.parse.quote_plus(DB_PASSWORD)
else:
    encoded_password = ""

# Create Database URL - using psycopg (v3)
DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

if __name__ == "__main__":
    print(f"Connecting to database: {DB_NAME} at {DB_HOST}:{DB_PORT} as {DB_USER}")
    try:
        # Test connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("Connection successful!", result.fetchone())

    except Exception as e:
        print(f"Error connecting to database: {e}")
