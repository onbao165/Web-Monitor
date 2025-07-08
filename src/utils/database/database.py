from typing import List, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool

from src.models.space import Space
from src.models.monitor import BaseMonitor, MonitorResult

from .models import Base
from .space_repository import SpaceRepository
from .monitor_repository import MonitorRepository
from .result_repository import ResultRepository

class Database:
    """Database access layer using SQLAlchemy"""
    
    def __init__(self, db_url: str = "sqlite:///data/monitor.db"):
        self.engine = create_engine(
            db_url, 
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800
        )
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        
    def init_db(self):
        """Initialize the database schema"""
        Base.metadata.create_all(self.engine)
    
    # Space operations
    def save_space(self, space: Space) -> Space:
        """Save a space to the database"""
        session = self.Session()
        try:
            space = SpaceRepository.save(session, space)
            session.commit()
            return space
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_space(self, space_id: str) -> Optional[Space]:
        """Get a space by ID"""
        session = self.Session()
        try:
            return SpaceRepository.get_by_id(session, space_id)
        finally:
            session.close()
    
    def get_space_by_name(self, name: str) -> Optional[Space]:
        """Get a space by name"""
        session = self.Session()
        try:
            return SpaceRepository.get_by_name(session, name)
        finally:
            session.close()
    
    def list_spaces(self) -> List[Space]:
        """List all spaces"""
        session = self.Session()
        try:
            return SpaceRepository.list_all(session)
        finally:
            session.close()
    
    def delete_space(self, space_id: str) -> bool:
        """Delete a space by ID"""
        session = self.Session()
        try:
            result = SpaceRepository.delete(session, space_id)
            session.commit()
            return result
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    # Monitor operations
    def save_monitor(self, monitor: BaseMonitor) -> BaseMonitor:
        """Save a monitor to the database"""
        session = self.Session()
        try:
            monitor = MonitorRepository.save(session, monitor)
            session.commit()
            return monitor
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_monitor(self, monitor_id: str) -> Optional[BaseMonitor]:
        """Get a monitor by ID"""
        session = self.Session()
        try:
            return MonitorRepository.get_by_id(session, monitor_id)
        finally:
            session.close()
    
    def get_monitors_for_space(self, space_id: str) -> List[BaseMonitor]:
        """Get all monitors for a space"""
        session = self.Session()
        try:
            return MonitorRepository.get_by_space_id(session, space_id)
        finally:
            session.close()
    
    def delete_monitor(self, monitor_id: str) -> bool:
        """Delete a monitor by ID"""
        session = self.Session()
        try:
            result = MonitorRepository.delete(session, monitor_id)
            session.commit()
            return result
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    # Monitor result operations
    def save_result(self, result: MonitorResult) -> MonitorResult:
        """Save a monitor result to the database"""
        session = self.Session()
        try:
            result = ResultRepository.save(session, result)
            session.commit()
            return result
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_results_for_monitor(self, monitor_id: str, limit: int = 100) -> List[MonitorResult]:
        """Get recent results for a monitor"""
        session = self.Session()
        try:
            return ResultRepository.get_by_monitor_id(session, monitor_id, limit)
        finally:
            session.close()
    
    def get_results_for_space(self, space_id: str, days_back: int = 7, limit: int = 1000) -> List[MonitorResult]:
        """Get recent results for a space"""
        session = self.Session()
        try:
            return ResultRepository.get_by_space_id(session, space_id, days_back, limit)
        finally:
            session.close()