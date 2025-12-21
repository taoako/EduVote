# Models package - SQLAlchemy ORM Architecture
from .base import Base, get_session, init_db, get_connection
from .model_user import User
from .model_election import Election
from .model_candidate import Candidate
from .model_section import Section
from .model_voting_record import VotingRecord

# Backward compatibility - Database class for legacy code
from .model_db import Database

