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
    from Models.model_position import Position
    from Models.model_audit_log import AuditLog
    
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
            "ALTER TABLE voting_records ADD COLUMN position_id INT NULL AFTER candidate_id",
            "ALTER TABLE users ADD COLUMN grade_level INT DEFAULT NULL AFTER student_id",
            "ALTER TABLE users ADD COLUMN section VARCHAR(50) DEFAULT NULL AFTER grade_level",
            "ALTER TABLE candidates ADD COLUMN user_id INT NULL AFTER election_id",
            "ALTER TABLE candidates ADD COLUMN created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE candidates ADD COLUMN position VARCHAR(128) DEFAULT NULL",
            "ALTER TABLE candidates ADD COLUMN position_id INT NULL AFTER election_id",
            "ALTER TABLE elections ADD COLUMN status_locked TINYINT(1) DEFAULT 0",
        ]
        
        for migration in migrations:
            try:
                session.execute(text(migration))
            except Exception:
                pass

        # Audit logs table
        try:
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    log_id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NULL,
                    action VARCHAR(128) NOT NULL,
                    details TEXT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_audit_created_at (created_at),
                    INDEX idx_audit_user_id (user_id)
                )
            """))
        except Exception:
            pass

        # Ensure voting_records uniqueness is per user/election/position
        # (Older schemas often had a unique index on (user_id, election_id), which breaks ballot voting.)
        try:
            schema = DB_CONFIG["database"]
            idx_rows = session.execute(
                text(
                    """
                    SELECT
                        INDEX_NAME AS index_name,
                        NON_UNIQUE AS non_unique,
                        GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) AS cols
                    FROM information_schema.statistics
                    WHERE table_schema = :schema
                      AND table_name = 'voting_records'
                    GROUP BY INDEX_NAME, NON_UNIQUE
                    """
                ),
                {"schema": schema},
            ).fetchall()

            def _cols(row):
                cols = getattr(row, "cols", None)
                if cols is None and isinstance(row, (tuple, list)) and len(row) >= 3:
                    cols = row[2]
                return (cols or "").lower()

            def _index_name(row):
                name = getattr(row, "index_name", None)
                if name is None and isinstance(row, (tuple, list)) and len(row) >= 1:
                    name = row[0]
                return name

            def _non_unique(row):
                nu = getattr(row, "non_unique", None)
                if nu is None and isinstance(row, (tuple, list)) and len(row) >= 2:
                    nu = row[1]
                return int(nu) if nu is not None else 1

            unique_indexes = [r for r in idx_rows if _non_unique(r) == 0]
            has_new_unique = any(_cols(r) == "user_id,election_id,position_id" for r in unique_indexes)

            # Drop legacy unique index on (user_id,election_id) if present.
            for r in unique_indexes:
                idx_name = _index_name(r)
                if not idx_name or str(idx_name).upper() == "PRIMARY":
                    continue
                if _cols(r) == "user_id,election_id":
                    try:
                        session.execute(text(f"DROP INDEX `{idx_name}` ON voting_records"))
                    except Exception:
                        # Ignore if already dropped or lacking privileges.
                        pass

            # Create the correct unique index if missing.
            if not has_new_unique:
                try:
                    session.execute(
                        text(
                            "CREATE UNIQUE INDEX `uniq_user_election_position` "
                            "ON voting_records (user_id, election_id, position_id)"
                        )
                    )
                except Exception:
                    pass
        except Exception:
            # Don't block app startup if index inspection fails.
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
