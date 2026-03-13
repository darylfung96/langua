from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import uuid

from config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Story(Base):
    __tablename__ = "stories"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, default="default_user")
    title = Column(String, nullable=False)
    story_content = Column(Text, nullable=False)
    language = Column(String, nullable=False)
    vocabulary = Column(Text, nullable=False)  # Stored as JSON string
    quiz = Column(Text, nullable=True)  # Stored as JSON string
    audio_file_path = Column(String, nullable=True)  # Path to audio file
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Lyric(Base):
    __tablename__ = "lyrics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, default="default_user")
    title = Column(String, nullable=False)
    video_id = Column(String, nullable=False)
    language = Column(String, nullable=False)
    transcript = Column(Text, nullable=False)  # Stored as JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Resource(Base):
    __tablename__ = "resources"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, default="default_user")
    title = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    language = Column(String, nullable=False)
    transcript = Column(Text, nullable=False)  # Stored as JSON string
    media_file_path = Column(String, nullable=True)  # Path to uploaded media file
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Visual(Base):
    __tablename__ = "visuals"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, default="default_user")
    word = Column(String, nullable=False)
    language = Column(String, nullable=False)
    images = Column(Text, nullable=False)  # Stored as JSON string
    prompt = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)  # Text response from Gemini
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


Base.metadata.create_all(bind=engine)

# Run migrations for existing databases (add new columns if they don't exist)
with engine.connect() as conn:
    from sqlalchemy import text, inspect
    inspector = inspect(engine)
    story_columns = [col["name"] for col in inspector.get_columns("stories")]
    if "quiz" not in story_columns:
        conn.execute(text("ALTER TABLE stories ADD COLUMN quiz TEXT"))
        conn.commit()
    if "audio_file_path" not in story_columns:
        conn.execute(text("ALTER TABLE stories ADD COLUMN audio_file_path TEXT"))
        conn.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
