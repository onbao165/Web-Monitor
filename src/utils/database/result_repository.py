import json
from typing import List, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from src.models.monitor import MonitorResult, MonitorStatus
from .models import MonitorResultModel

class ResultRepository:
    """Repository for MonitorResult operations"""
    
    @staticmethod
    def save(session: Session, result: MonitorResult) -> MonitorResult:
        """Save a monitor result to the database"""
        # Convert details dict to JSON string
        details_json = json.dumps(result.details) if result.details else None
        
        # Create new result (results are always new entries)
        db_result = MonitorResultModel(
            id=result.id,
            monitor_id=result.monitor_id,
            space_id=result.space_id,
            timestamp=result.timestamp,
            status=result.status.value,
            response_time_ms=result.response_time_ms,
            error_message=result.error_message,
            details=details_json
        )
        
        session.add(db_result)
        return result
    
    @staticmethod
    def get_by_monitor_id(session: Session, monitor_id: str, limit: int = 100) -> List[MonitorResult]:
        """Get recent results for a monitor"""
        db_results = session.query(MonitorResultModel)\
            .filter(MonitorResultModel.monitor_id == monitor_id)\
            .order_by(MonitorResultModel.timestamp.desc())\
            .limit(limit)\
            .all()
        
        results = []
        for db_result in db_results:
            # Convert JSON string back to dict
            details = json.loads(db_result.details) if db_result.details else None
            
            results.append(MonitorResult(
                id=db_result.id,
                monitor_id=db_result.monitor_id,
                space_id=db_result.space_id,
                timestamp=db_result.timestamp,
                status=MonitorStatus(db_result.status),
                response_time_ms=db_result.response_time_ms,
                error_message=db_result.error_message,
                details=details
            ))
        
        return results
    
    @staticmethod
    def get_by_space_id(session: Session, space_id: str, days_back: int = 7, limit: int = 1000) -> List[MonitorResult]:
        """Get recent results for a space"""
        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        db_results = session.query(MonitorResultModel)\
            .filter(MonitorResultModel.space_id == space_id)\
            .filter(MonitorResultModel.timestamp >= cutoff_date)\
            .order_by(MonitorResultModel.timestamp.desc())\
            .limit(limit)\
            .all()
        
        results = []
        for db_result in db_results:
            # Convert JSON string back to dict
            details = json.loads(db_result.details) if db_result.details else None
            
            results.append(MonitorResult(
                id=db_result.id,
                monitor_id=db_result.monitor_id,
                space_id=db_result.space_id,
                timestamp=db_result.timestamp,
                status=MonitorStatus(db_result.status),
                response_time_ms=db_result.response_time_ms,
                error_message=db_result.error_message,
                details=details
            ))
        
        return results