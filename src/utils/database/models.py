from sqlalchemy import Column, String, Integer, Boolean, Float, ForeignKey, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Create base class for SQLAlchemy models
Base = declarative_base()

class SpaceModel(Base):
    __tablename__ = 'spaces'
    
    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    notification_emails = Column(Text, nullable=True)  # Store as JSON string
    
    # Relationship to monitors
    monitors = relationship("MonitorModel", back_populates="space", cascade="all, delete-orphan")

class MonitorModel(Base):
    __tablename__ = 'monitors'
    
    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    space_id = Column(String(36), ForeignKey('spaces.id'), nullable=False)
    monitor_type = Column(String(20), nullable=False)
    enabled = Column(Boolean, default=True)
    status = Column(String(20), nullable=False)
    check_interval_seconds = Column(Integer, default=300)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
    last_checked_at = Column(DateTime, nullable=True)
    
    # URL monitor specific fields
    url = Column(String(500), nullable=True)
    expected_status_code = Column(Integer, nullable=True)
    timeout_seconds = Column(Integer, nullable=True)
    check_ssl = Column(Boolean, nullable=True)
    follow_redirects = Column(Boolean, nullable=True)
    check_content = Column(Text, nullable=True)
    
    # Database monitor specific fields
    db_type = Column(String(20), nullable=True)
    host = Column(String(100), nullable=True)
    port = Column(Integer, nullable=True)
    database = Column(String(100), nullable=True)
    username = Column(String(100), nullable=True)
    _encrypted_password = Column(String(500), nullable=True)
    connection_timeout_seconds = Column(Integer, nullable=True)
    query_timeout_seconds = Column(Integer, nullable=True)
    test_query = Column(Text, nullable=True)
    
    # Relationships
    space = relationship("SpaceModel", back_populates="monitors")
    results = relationship("MonitorResultModel", back_populates="monitor", cascade="all, delete-orphan")

class MonitorResultModel(Base):
    __tablename__ = 'monitor_results'
    
    id = Column(String(36), primary_key=True)
    monitor_id = Column(String(36), ForeignKey('monitors.id'), nullable=False)
    space_id = Column(String(36), ForeignKey('spaces.id'), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False)
    response_time_ms = Column(Float, nullable=True)
    error_message = Column(Text, nullable=True)
    details = Column(Text, nullable=True)  # Store as JSON string
    
    # Relationships
    monitor = relationship("MonitorModel", back_populates="results")