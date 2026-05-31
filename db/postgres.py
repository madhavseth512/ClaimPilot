import os
import uuid
from datetime import datetime
from sqlalchemy import create_engine, Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
    f"@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}"
    f"/{os.getenv('POSTGRES_DB', 'claimpilot')}"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    cases = relationship("Case", back_populates="user")


class Case(Base):
    __tablename__ = "cases"

    case_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    intent = Column(String, nullable=False)
    case_status = Column(String, default="active")  # active | complete | escalated
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="cases")
    documents = relationship("Document", back_populates="case")


class Document(Base):
    __tablename__ = "documents"

    document_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, ForeignKey("cases.case_id"), nullable=False)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    filename = Column(String, nullable=False)
    document_type = Column(String, nullable=False)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    chroma_collection_ref = Column(String)

    case = relationship("Case", back_populates="documents")


class ConversationState(Base):
    __tablename__ = "conversation_state"

    state_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, ForeignKey("cases.case_id"), nullable=False, unique=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=False)
    state_json = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
