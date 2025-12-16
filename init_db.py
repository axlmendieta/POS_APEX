from database import engine
from models import Base
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    try:
        # Start fresh: drop all tables (be careful in production!)
        if os.getenv("ALLOW_SCHEMA_DROP") == "true":
            Base.metadata.drop_all(bind=engine)
            logger.info("Existing tables dropped.")
        else:
            logger.info("Skipping drop_all: ALLOW_SCHEMA_DROP not set to true.") 
        
        # Create all tables defined in models.py
        Base.metadata.create_all(bind=engine)
        logger.info("Tables created successfully!")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")

if __name__ == "__main__":
    init_db()
