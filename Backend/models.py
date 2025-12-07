"""
Database models for the encrypted questionnaire system using SQLAlchemy ORM.
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON, PickleType
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
import json

Base = declarative_base()


class Questionnaire(Base):
    """
    Table to store questionnaires with encrypted responses.
    
    Each questionnaire contains:
    - A unique link/ID
    - Deadline for responses
    - JSON with questions and options
    - Public and secret keys for BFV encryption
    - Accumulated encrypted responses (list of ciphertexts)
    """
    __tablename__ = 'questionnaires'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    link = Column(String(255), unique=True, nullable=False, index=True)
    deadline = Column(DateTime, nullable=False)
    questions_json = Column(Text, nullable=False)  # JSON string with questions
    
    # BFV Parameters
    poly_degree = Column(Integer, nullable=False)
    plain_modulus = Column(Integer, nullable=False)
    ciph_modulus = Column(String(100), nullable=False)  # Store as string for large numbers
    
    # Encryption keys (stored as JSON serialized polynomials)
    public_key_json = Column(Text, nullable=False)
    secret_key_json = Column(Text, nullable=False)
    
    # Accumulated encrypted responses
    # This is a list of lists: one list per question, each containing accumulated ciphertext
    accumulated_responses_json = Column(Text, nullable=True)  # JSON string
    
    # Decrypted results (stored after deadline)
    decrypted_results_json = Column(Text, nullable=True)  # JSON string with decrypted results
    is_decrypted = Column(Integer, default=0)  # Boolean flag: 0=not decrypted, 1=decrypted
    hide_results_until_deadline = Column(Integer, default=1)  # 1=true, 0=false

    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    num_responses = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<Questionnaire(id={self.id}, link='{self.link}', deadline='{self.deadline}')>"
    
    def get_questions(self):
        """Parse and return questions as Python object."""
        return json.loads(self.questions_json)
    
    def set_questions(self, questions):
        """Set questions from Python object."""
        self.questions_json = json.dumps(questions)
    
    def get_public_key(self):
        """Parse and return public key."""
        return json.loads(self.public_key_json)
    
    def set_public_key(self, public_key):
        """Set public key from Python object."""
        self.public_key_json = json.dumps(public_key)
    
    def get_secret_key(self):
        """Parse and return secret key."""
        return json.loads(self.secret_key_json)
    
    def set_secret_key(self, secret_key):
        """Set secret key from Python object."""
        self.secret_key_json = json.dumps(secret_key)
    
    def get_accumulated_responses(self):
        """Parse and return accumulated responses."""
        if self.accumulated_responses_json:
            return json.loads(self.accumulated_responses_json)
        return None
    
    def set_accumulated_responses(self, responses):
        """Set accumulated responses from Python object."""
        self.accumulated_responses_json = json.dumps(responses)
    
    def get_params(self):
        """Return BFV parameters as dict."""
        return {
            'poly_degree': self.poly_degree,
            'plain_modulus': self.plain_modulus,
            'ciph_modulus': int(self.ciph_modulus)
        }
    
    def get_decrypted_results(self):
        """Parse and return decrypted results."""
        if self.decrypted_results_json:
            return json.loads(self.decrypted_results_json)
        return None
    
    def set_decrypted_results(self, results):
        """Set decrypted results from Python object."""
        self.decrypted_results_json = json.dumps(results)
        self.is_decrypted = 1


class SubmissionRecord(Base):
    """
    Table to track which certificate fingerprints have answered which questionnaire.
    """
    __tablename__ = 'submission_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    questionnaire_id = Column(Integer, nullable=False, index=True)
    cert_fingerprint = Column(String(64), nullable=False)
    submitted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        {'sqlite_autoincrement': True}
    )


# Database initialization
def init_db(db_url='sqlite:///questionnaires.db'):
    """
    Initialize the database.
    
    Args:
        db_url: SQLAlchemy database URL (default: SQLite)
    
    Returns:
        engine, Session: Database engine and session maker
    """
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return engine, Session


def get_session(db_url='sqlite:///questionnaires.db'):
    """
    Get a new database session.
    
    Args:
        db_url: SQLAlchemy database URL
    
    Returns:
        session: Database session
    """
    engine = create_engine(db_url, echo=False)
    Session = sessionmaker(bind=engine)
    return Session()


if __name__ == '__main__':
    # Test database creation
    print("Creating database...")
    engine, Session = init_db()
    print("Database created successfully!")
    print(f"Tables: {Base.metadata.tables.keys()}")
