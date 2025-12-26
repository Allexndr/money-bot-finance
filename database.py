from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import DATABASE_URL

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    is_subscribed = Column(Boolean, default=True)

class CourseApplication(Base):
    __tablename__ = 'course_applications'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    user_telegram_id = Column(Integer, nullable=False)
    username = Column(String(255))
    first_name = Column(String(255))
    status = Column(String(50), default='pending')  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    processed_by = Column(String(255))

class Newsletter(Base):
    __tablename__ = 'newsletters'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime)
    is_sent = Column(Boolean, default=False)

class BotMessage(Base):
    __tablename__ = 'bot_messages'
    
    id = Column(Integer, primary_key=True)
    page_key = Column(String(100), unique=True, nullable=False)
    title = Column(String(255))
    text = Column(Text, nullable=False)
    parse_mode = Column(String(20), default='HTML')
    is_main_menu = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class BotButton(Base):
    __tablename__ = 'bot_buttons'
    
    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, nullable=False)
    text = Column(String(255), nullable=False)
    button_type = Column(String(50), nullable=False)
    action_data = Column(Text, nullable=False)
    row = Column(Integer, default=0)
    order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Database setup
engine = create_engine(DATABASE_URL, echo=True)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()





