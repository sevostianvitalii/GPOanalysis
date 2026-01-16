# =============================================================================
# GPO Analysis Tool - Database Configuration
# =============================================================================

from sqlmodel import SQLModel, create_engine, Session
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Database file location
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "gpo_analysis.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create engine
# check_same_thread=False is needed for SQLite with FastAPI
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def init_db():
    """Initialize the database and create tables."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)
    logger.info(f"Database initialized at {DB_PATH}")

def get_session():
    """Dependency to get a database session."""
    with Session(engine) as session:
        yield session
