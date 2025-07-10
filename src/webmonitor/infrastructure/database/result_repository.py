import json
from typing import List, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from webmonitor.models import MonitorResult, MonitorStatus, MonitorType
from .models import MonitorResultModel

class ResultRepository:
    """Repository for MonitorResult operations"""

    @staticmethod
    def _map_fields_to_db(result: MonitorResult, db_result: MonitorResultModel) -> None:
        db_result.monitor_id = result.monitor_id
        db_result.space_id = result.space_id
        db_result.timestamp = result.timestamp
        db_result.status = result.status.value
        db_result.monitor_type = result.monitor_type.value
        db_result.response_time_ms = result.response_time_ms
        db_result.details = json.dumps(result.details) if result.details else None
        db_result.failed_checks = result.failed_checks
        db_result.check_list = json.dumps(result.check_list) if result.check_list else None

    @staticmethod
    def _to_domain_model(db_result: MonitorResultModel) -> MonitorResult:
        details = json.loads(db_result.details) if db_result.details else None

        return MonitorResult(
            id=db_result.id,
            monitor_id=db_result.monitor_id,
            space_id=db_result.space_id,
            monitor_type=MonitorType(db_result.monitor_type),
            timestamp=db_result.timestamp,
            status=MonitorStatus(db_result.status),
            response_time_ms=db_result.response_time_ms,
            details=details,
            failed_checks=db_result.failed_checks,
            check_list=json.loads(db_result.check_list) if db_result.check_list else None
        )

    @staticmethod
    def _to_domain_models(db_results: List[MonitorResultModel]) -> List[MonitorResult]:
        results = []
        for db_result in db_results:
            results.append(ResultRepository._to_domain_model(db_result))
        return results

    @staticmethod
    def save(session: Session, result: MonitorResult) -> MonitorResult:
        # Create new result (results are always new entries)
        db_result = MonitorResultModel(id=result.id)
        ResultRepository._map_fields_to_db(result, db_result)

        session.add(db_result)
        return result
    
    @staticmethod
    def get_by_monitor_id(session: Session, monitor_id: str, limit: int = 100) -> List[MonitorResult]:
        db_results = session.query(MonitorResultModel)\
            .filter(MonitorResultModel.monitor_id == monitor_id)\
            .order_by(MonitorResultModel.timestamp.desc())\
            .limit(limit)\
            .all()

        return ResultRepository._to_domain_models(db_results)
    
    @staticmethod
    def get_by_space_id(session: Session, space_id: str, limit: int = 1000) -> List[MonitorResult]:

        db_results = session.query(MonitorResultModel)\
            .filter(MonitorResultModel.space_id == space_id)\
            .order_by(MonitorResultModel.timestamp.desc())\
            .limit(limit)\
            .all()

        return ResultRepository._to_domain_models(db_results)
