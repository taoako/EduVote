"""
SQLAlchemy Base configuration and database session management.
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool
from config import DB_CONFIG
import mysql.connector
from mysql.connector import Error

# Create database URL from config
DATABASE_URL = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL, 
    echo=False, 
    pool_pre_ping=True,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()


def get_session():
    """Get a new database session."""
    return SessionLocal()


def create_database():
    """Create the database if it doesn't exist."""
    try:
        connection = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port']
        )
        cursor = connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        cursor.close()
        connection.close()
    except Error as e:
        print(f"Error creating database: {e}")


def init_db():
    """Initialize database tables."""
    create_database()
    # Import all models to register them with Base
    from Models.model_user import User
    from Models.model_election import Election
    from Models.model_candidate import Candidate
    from Models.model_section import Section
    from Models.model_voting_record import VotingRecord
    
    Base.metadata.create_all(bind=engine)
    
    # Run schema migrations for compatibility
    _run_migrations()


def _run_migrations():
    """Run schema migrations for backward compatibility."""
    session = get_session()
    try:
        # Ensure legacy schemas allow the "finalized" status
        try:
            session.execute(text("""
                ALTER TABLE elections
                MODIFY COLUMN status ENUM('upcoming','active','finalized')
                NOT NULL DEFAULT 'upcoming'
            """))
        except Exception:
            pass
        
        # Add missing columns if they don't exist
        migrations = [
            "ALTER TABLE voting_records ADD COLUMN voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE voting_records ADD COLUMN candidate_id INT NULL AFTER election_id",
            "ALTER TABLE voting_records ADD COLUMN status ENUM('cast','spoiled') DEFAULT 'cast' AFTER candidate_id",
            "ALTER TABLE users ADD COLUMN grade_level INT DEFAULT NULL AFTER student_id",
            "ALTER TABLE users ADD COLUMN section VARCHAR(50) DEFAULT NULL AFTER grade_level",
            "ALTER TABLE candidates ADD COLUMN user_id INT NULL AFTER election_id",
            "ALTER TABLE candidates ADD COLUMN created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE candidates ADD COLUMN position VARCHAR(128) DEFAULT NULL",
        ]
        
        for migration in migrations:
            try:
                session.execute(text(migration))
            except Exception:
                pass
        
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Migration error: {e}")
    finally:
        session.close()


# Legacy support - keep get_connection for backward compatibility with controllers
def get_connection():
    """Legacy: Create and return a MySQL database connection."""
    try:
        connection = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            port=DB_CONFIG['port']
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None
