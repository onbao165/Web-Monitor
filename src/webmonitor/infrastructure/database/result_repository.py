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

    @staticmethod
    def cleanup_old_results(session: Session, keep_healthy_days: int, keep_unhealthy_days: int, batch_size: int = 1000) -> Dict[str, Any]:
        """
        Clean up old monitor results based on retention policies.
        Returns statistics about the cleanup operation.
        """
        from sqlalchemy import and_

        now = datetime.now()
        healthy_cutoff = now - timedelta(days=keep_healthy_days)
        unhealthy_cutoff = now - timedelta(days=keep_unhealthy_days)

        cleanup_stats = {
            'healthy_deleted': 0,
            'unhealthy_deleted': 0,
            'total_deleted': 0,
            'batches_processed': 0,
            'start_time': now,
            'errors': []
        }

        try:
            # Clean up old healthy results
            healthy_deleted = ResultRepository._cleanup_results_by_status(
                session, healthy_cutoff, MonitorStatus.HEALTHY, batch_size
            )
            cleanup_stats['healthy_deleted'] = healthy_deleted

            # Clean up old unhealthy results (UNHEALTHY and UNKNOWN)
            unhealthy_deleted = 0
            for status in [MonitorStatus.UNHEALTHY, MonitorStatus.UNKNOWN]:
                deleted = ResultRepository._cleanup_results_by_status(
                    session, unhealthy_cutoff, status, batch_size
                )
                unhealthy_deleted += deleted

            cleanup_stats['unhealthy_deleted'] = unhealthy_deleted
            cleanup_stats['total_deleted'] = healthy_deleted + unhealthy_deleted

        except Exception as e:
            cleanup_stats['errors'].append(str(e))
            raise

        cleanup_stats['end_time'] = datetime.now()
        cleanup_stats['duration_seconds'] = (cleanup_stats['end_time'] - cleanup_stats['start_time']).total_seconds()

        return cleanup_stats

    @staticmethod
    def _cleanup_results_by_status(session: Session, cutoff_date: datetime, status: MonitorStatus, batch_size: int) -> int:
        """Clean up results for a specific status in batches."""
        total_deleted = 0

        while True:
            # Find a batch of old results to delete
            old_results = session.query(MonitorResultModel)\
                .filter(and_(
                    MonitorResultModel.timestamp < cutoff_date,
                    MonitorResultModel.status == status.value
                ))\
                .limit(batch_size)\
                .all()

            if not old_results:
                break  # No more results to delete

            # Delete the batch
            for result in old_results:
                session.delete(result)

            batch_count = len(old_results)
            total_deleted += batch_count

            # Commit the batch to avoid long-running transactions
            session.commit()

            # If we got less than batch_size, we're done
            if batch_count < batch_size:
                break

        return total_deleted

    @staticmethod
    def get_cleanup_preview(session: Session, keep_healthy_days: int, keep_unhealthy_days: int) -> Dict[str, Any]:
        """
        Preview what would be deleted without actually deleting anything.
        Useful for safety checks and reporting.
        """
        from sqlalchemy import and_, func

        now = datetime.now()
        healthy_cutoff = now - timedelta(days=keep_healthy_days)
        unhealthy_cutoff = now - timedelta(days=keep_unhealthy_days)

        # Count healthy results that would be deleted
        healthy_count = session.query(func.count(MonitorResultModel.id))\
            .filter(and_(
                MonitorResultModel.timestamp < healthy_cutoff,
                MonitorResultModel.status == MonitorStatus.HEALTHY.value
            ))\
            .scalar()

        # Count unhealthy results that would be deleted
        unhealthy_count = session.query(func.count(MonitorResultModel.id))\
            .filter(and_(
                MonitorResultModel.timestamp < unhealthy_cutoff,
                MonitorResultModel.status.in_([MonitorStatus.UNHEALTHY.value, MonitorStatus.UNKNOWN.value])
            ))\
            .scalar()

        # Get total count for reference
        total_count = session.query(func.count(MonitorResultModel.id)).scalar()

        return {
            'healthy_to_delete': healthy_count,
            'unhealthy_to_delete': unhealthy_count,
            'total_to_delete': healthy_count + unhealthy_count,
            'total_results': total_count,
            'retention_after_cleanup': total_count - (healthy_count + unhealthy_count),
            'healthy_cutoff_date': healthy_cutoff,
            'unhealthy_cutoff_date': unhealthy_cutoff
        }
