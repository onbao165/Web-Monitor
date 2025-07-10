from typing import List, Optional
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import and_

from webmonitor.models import BaseMonitor, UrlMonitor, DatabaseMonitor, MonitorType, MonitorStatus
from .models import MonitorModel

class MonitorRepository:
    """Repository for Monitor operations"""

    @staticmethod
    def _map_base_fields_to_db(monitor: BaseMonitor, db_monitor: MonitorModel) -> None:
        db_monitor.name = monitor.name
        db_monitor.space_id = monitor.space_id
        db_monitor.monitor_type = monitor.monitor_type.value
        db_monitor.status = monitor.status.value
        db_monitor.check_interval_seconds = monitor.check_interval_seconds
        db_monitor.updated_at = monitor.updated_at
        db_monitor.last_checked_at = monitor.last_checked_at
        db_monitor.last_healthy_at = monitor.last_healthy_at

    @staticmethod
    def _map_type_specific_fields_to_db(monitor: BaseMonitor, db_monitor: MonitorModel) -> None:
        if isinstance(monitor, UrlMonitor):
            db_monitor.url = monitor.url
            db_monitor.expected_status_code = monitor.expected_status_code
            db_monitor.timeout_seconds = monitor.timeout_seconds
            db_monitor.check_ssl = monitor.check_ssl
            db_monitor.follow_redirects = monitor.follow_redirects
            db_monitor.check_content = monitor.check_content
        elif isinstance(monitor, DatabaseMonitor):
            db_monitor.db_type = monitor.db_type
            db_monitor.host = monitor.host
            db_monitor.port = monitor.port
            db_monitor.database = monitor.database
            db_monitor.username = monitor.username
            db_monitor.encrypted_password = monitor.encrypted_password
            db_monitor.connection_timeout_seconds = monitor.connection_timeout_seconds
            db_monitor.query_timeout_seconds = monitor.query_timeout_seconds
            db_monitor.test_query = monitor.test_query

    @staticmethod
    def _to_domain_model(db_monitor: MonitorModel) -> Optional[BaseMonitor]:
        if db_monitor.monitor_type == MonitorType.URL.value:
            return UrlMonitor(
                id=db_monitor.id,
                name=db_monitor.name,
                space_id=db_monitor.space_id,
                monitor_type=MonitorType(db_monitor.monitor_type),
                status=MonitorStatus(db_monitor.status),
                check_interval_seconds=db_monitor.check_interval_seconds,
                created_at=db_monitor.created_at,
                updated_at=db_monitor.updated_at,
                last_checked_at=db_monitor.last_checked_at,
                last_healthy_at=db_monitor.last_healthy_at,
                url=db_monitor.url,
                expected_status_code=db_monitor.expected_status_code,
                timeout_seconds=db_monitor.timeout_seconds,
                check_ssl=db_monitor.check_ssl,
                follow_redirects=db_monitor.follow_redirects,
                check_content=db_monitor.check_content
            )
        elif db_monitor.monitor_type == MonitorType.DATABASE.value:
            return DatabaseMonitor(
                id=db_monitor.id,
                name=db_monitor.name,
                space_id=db_monitor.space_id,
                monitor_type=MonitorType(db_monitor.monitor_type),
                status=MonitorStatus(db_monitor.status),
                check_interval_seconds=db_monitor.check_interval_seconds,
                created_at=db_monitor.created_at,
                updated_at=db_monitor.updated_at,
                last_checked_at=db_monitor.last_checked_at,
                last_healthy_at=db_monitor.last_healthy_at,
                db_type=db_monitor.db_type,
                host=db_monitor.host,
                port=db_monitor.port,
                database=db_monitor.database,
                username=db_monitor.username,
                encrypted_password=db_monitor.encrypted_password,
                connection_timeout_seconds=db_monitor.connection_timeout_seconds,
                query_timeout_seconds=db_monitor.query_timeout_seconds,
                test_query=db_monitor.test_query
            )
        return None

    @staticmethod
    def _to_domain_models(db_monitors: List[MonitorModel]) -> List[BaseMonitor]:
        monitors = []
        for db_monitor in db_monitors:
            domain_monitor = MonitorRepository._to_domain_model(db_monitor)
            if domain_monitor:
                monitors.append(domain_monitor)
        return monitors

    @staticmethod
    def save(session: Session, monitor: BaseMonitor) -> BaseMonitor:
        # Check if monitor already exists
        db_monitor = session.query(MonitorModel).filter(MonitorModel.id == monitor.id).first()

        if db_monitor:
            # Update existing monitor
            MonitorRepository._map_base_fields_to_db(monitor, db_monitor)
        else:
            # Create new monitor
            db_monitor = MonitorModel(
                id=monitor.id,
                created_at=monitor.created_at
            )
            MonitorRepository._map_base_fields_to_db(monitor, db_monitor)
            session.add(db_monitor)

        # Set type-specific fields
        MonitorRepository._map_type_specific_fields_to_db(monitor, db_monitor)

        return monitor
    
    @staticmethod
    def get_by_id(session: Session, monitor_id: str) -> Optional[BaseMonitor]:
        db_monitor = session.query(MonitorModel).filter(MonitorModel.id == monitor_id).first()
        if not db_monitor:
            return None

        return MonitorRepository._to_domain_model(db_monitor)

    @staticmethod
    def get_by_name(session: Session, name: str, space_id: str = None, space_name: str = None) -> Optional[BaseMonitor]:
        query = session.query(MonitorModel).filter(MonitorModel.name == name)
        if space_id:
            query = query.filter(MonitorModel.space_id == space_id)
        if space_name:
            query = query.join(SpaceModel).filter(SpaceModel.name == space_name)

        db_monitor = query.first()
        if not db_monitor:
            return None

        return MonitorRepository._to_domain_model(db_monitor)

    @staticmethod
    def list_all(session: Session) -> List[BaseMonitor]:
        db_monitors = session.query(MonitorModel).all()
        return MonitorRepository._to_domain_models(db_monitors)
    
    @staticmethod
    def get_by_space_id(session: Session, space_id: str) -> List[BaseMonitor]:
        db_monitors = session.query(MonitorModel).filter(MonitorModel.space_id == space_id).all()
        return MonitorRepository._to_domain_models(db_monitors)
    
    @staticmethod
    def delete(session: Session, monitor_id: str) -> bool:
        db_monitor = session.query(MonitorModel).filter(MonitorModel.id == monitor_id).first()
        if not db_monitor:
            return False

        session.delete(db_monitor)
        return True

    @staticmethod
    def get_unhealthy_monitors(session: Session, unhealthy_threshold_hours: int) -> List[BaseMonitor]:
        threshold_time = datetime.now() - timedelta(hours=unhealthy_threshold_hours)

        # Find monitors that:
        # 1. Have been checked at least once (last_checked_at is not None)
        # 2. Either have never been healthy OR last_healthy_at is older than threshold
        # 3. Are not currently OFFLINE (meaning they're being monitored)
        db_monitors = session.query(MonitorModel).filter(
            and_(
                MonitorModel.last_checked_at.isnot(None),  # Has been checked
                MonitorModel.status != MonitorStatus.OFFLINE.value,  # Is being monitored
                # Either never been healthy OR last healthy time is old
                (MonitorModel.last_healthy_at.is_(None)) |
                (MonitorModel.last_healthy_at < threshold_time)
            )
        ).all()

        return MonitorRepository._to_domain_models(db_monitors)