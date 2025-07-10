from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool

from .models import Base, SpaceModel, MonitorModel, MonitorResultModel
from .space_repository import SpaceRepository
from .monitor_repository import MonitorRepository
from .result_repository import ResultRepository
from webmonitor.models import Space, BaseMonitor, MonitorResult

class Database:
    # Database access layer using SQLAlchemy
    
    def __init__(self, db_url: str = None):
        if db_url is None:
            db_url = "sqlite:////var/lib/webmonitor/webmonitor.db"   

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
        Base.metadata.create_all(self.engine)
    
    # Space operations
    def save_space(self, space: Space) -> Space:
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
        session = self.Session()
        try:
            return SpaceRepository.get_by_id(session, space_id)
        finally:
            session.close()
    
    def get_space_by_name(self, name: str) -> Optional[Space]:
        session = self.Session()
        try:
            return SpaceRepository.get_by_name(session, name)
        finally:
            session.close()
    
    def list_spaces(self) -> List[Space]:
        session = self.Session()
        try:
            return SpaceRepository.list_all(session)
        finally:
            session.close()
    
    def delete_space(self, space_id: str) -> bool:
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
        session = self.Session()
        try:
            return MonitorRepository.get_by_id(session, monitor_id)
        finally:
            session.close()

    def get_monitor_by_name(self, name: str, space_id: str = None, space_name: str = None) -> Optional[BaseMonitor]:
        session = self.Session()
        try:
            return MonitorRepository.get_by_name(session, name, space_id, space_name)
        finally:
            session.close()

    def list_monitors(self) -> List[BaseMonitor]:
        session = self.Session()
        try:
            return MonitorRepository.list_all(session)
        finally:
            session.close()
    
    def get_monitors_for_space(self, space_id: str) -> List[BaseMonitor]:
        session = self.Session()
        try:
            return MonitorRepository.get_by_space_id(session, space_id)
        finally:
            session.close()
    
    def delete_monitor(self, monitor_id: str) -> bool:
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

    def get_unhealthy_monitors(self, unhealthy_threshold_hours: int) -> List[BaseMonitor]:
        session = self.Session()
        try:
            return MonitorRepository.get_unhealthy_monitors(session, unhealthy_threshold_hours)
        finally:
            session.close()
    
    # Monitor result operations
    def save_result(self, result: MonitorResult) -> MonitorResult:
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
    
    def get_results_for_monitor(self, monitor_id: str, limit: int = 10) -> List[MonitorResult]:
        session = self.Session()
        try:
            return ResultRepository.get_by_monitor_id(session, monitor_id, limit)
        finally:
            session.close()
    
    def get_results_for_space(self, space_id: str, limit: int = 10) -> List[MonitorResult]:
        session = self.Session()
        try:
            return ResultRepository.get_by_space_id(session, space_id, limit)
        finally:
            session.close()

    def cleanup_old_results(self, keep_healthy_days: int, keep_unhealthy_days: int, batch_size: int = 1000) -> Dict[str, Any]:
        session = self.Session()
        try:
            return ResultRepository.cleanup_old_results(session, keep_healthy_days, keep_unhealthy_days, batch_size)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_cleanup_preview(self, keep_healthy_days: int, keep_unhealthy_days: int) -> Dict[str, Any]:
        session = self.Session()
        try:
            return ResultRepository.get_cleanup_preview(session, keep_healthy_days, keep_unhealthy_days)
        finally:
            session.close()



