from sqlalchemy import Column, Integer, String, Boolean, DateTime, Index
from datetime import datetime
from database import Base


class Setting(Base):
    __tablename__ = "settings"
    key = Column(String, primary_key=True)
    value = Column(String, nullable=False, default="")


class Tweet(Base):
    __tablename__ = "tweets"
    id = Column(Integer, primary_key=True, index=True)
    author = Column(String, nullable=False, index=True)
    content = Column(String, nullable=False)
    content_zh = Column(String, nullable=True)
    url = Column(String, nullable=True)
    source_id = Column(String, nullable=False, unique=True, index=True)
    tweeted_at = Column(DateTime, nullable=True)
    saved_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_tweets_saved_at", "saved_at"),
    )


class BarkDevice(Base):
    __tablename__ = "bark_devices"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    server_url = Column(String, nullable=False, default="https://api.day.app")
    device_key = Column(String, nullable=False)
    sound = Column(String, nullable=True, default="")
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
