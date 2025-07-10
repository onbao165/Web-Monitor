import threading
import time
import logging
import schedule
from typing import Dict, List, Optional, Set, Any
from datetime import datetime
from .db_checker import check_db
from .url_checker import check_url
from .email_service import should_send_notification, send_monitor_result_email
from webmonitor.infrastructure import Database
from webmonitor.models import BaseMonitor, UrlMonitor, DatabaseMonitor, MonitorType, MonitorResult, MonitorStatus

"""
Scheduler for managing monitor jobs.
Handles scheduling, stopping, and listing monitors.
"""

class MonitorScheduler:
    database: Database
    running_monitors: Dict[BaseMonitor, schedule.Job]
    system_jobs: Dict[str, Any]
    system_job_schedules: Dict[str, schedule.Job]
    monitor_lock: threading.Lock
    logger: logging.Logger
    stop_event: threading.Event
    scheduler_thread: threading.Thread

    def __init__(self, database: Database):
        self.database = database
        self.running_monitors: Dict[BaseMonitor, schedule.Job] = {}
        self.system_jobs: Dict[str, Any] = {}
        self.system_job_schedules: Dict[str, schedule.Job] = {}
        self.monitor_lock = threading.Lock()  # For thread-safe operations
        self.logger = logging.getLogger(__name__)

        # Initialize system jobs
        self._initialize_system_jobs()

        # Start the scheduler in a separate thread
        self.stop_event = threading.Event()
        self.scheduler_thread = threading.Thread(target=self._run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
    
    def _run_scheduler(self):
        # Run the scheduler in a loop until stop_event is set
        while not self.stop_event.is_set():
            schedule.run_pending()
            time.sleep(1)
    
    def _run_monitor(self, monitor: BaseMonitor):
        try:
            self.logger.info(f"Running monitor check: {monitor.name} ({monitor.id})")
            
            # Run the appropriate check based on monitor type
            if isinstance(monitor, UrlMonitor):
                result = check_url(monitor)
            elif isinstance(monitor, DatabaseMonitor):
                result = check_db(monitor)
            else:
                self.logger.error(f"Unknown monitor type: {type(monitor)}")
                return
            
            # Update monitor status and timestamps
            monitor.status = result.status
            monitor.update_last_checked_at()
            if result.status == MonitorStatus.HEALTHY:
                monitor.update_last_healthy_at()

            # Get the most recent previous result for comparison
            previous_results = self.database.get_results_for_monitor(monitor.id, limit=1)
            previous_result = previous_results[0] if previous_results else None
            
            # Save result and updated monitor
            self.database.save_result(result)
            self.database.save_monitor(monitor)
            
            self.logger.info(f"Monitor check completed: {monitor.name} ({monitor.id}) - Status: {result.status.value}")

            # Send notifications if there's a status change
            if should_send_notification(result, previous_result):
                # Get space to access notification settings
                space = self.database.get_space(monitor.space_id)
                
                if space and space.notification_emails:
                    recipients = space.notification_emails
                    send_monitor_result_email(space, result, recipients)
                    self.logger.info(f"Status change notification sent for monitor: {monitor.name}")
        
        except Exception as e:
            self.logger.error(f"Error running monitor {monitor.name} ({monitor.id}): {str(e)}")

    def _initialize_system_jobs(self):
        from webmonitor.config import get_config_manager
        from webmonitor.jobs.health_alert_job import HealthAlertJob
        from webmonitor.jobs.data_cleanup_job import DataCleanupJob

        config_manager = get_config_manager()

        # Initialize health alert job
        health_config = config_manager.get_health_alerts_config()
        if health_config.get('enabled', True):
            health_job = HealthAlertJob(self.database)
            self.system_jobs['health_alert'] = health_job

            # Schedule health alert job
            interval_minutes = health_config.get('check_interval_minutes', 60)
            job = schedule.every(interval_minutes).minutes.do(health_job.run)
            self.system_job_schedules['health_alert'] = job

            self.logger.info(f"Health alert job scheduled to run every {interval_minutes} minutes")

        # Initialize data cleanup job
        cleanup_config = config_manager.get_data_cleanup_config()
        if cleanup_config.get('enabled', True):
            cleanup_job = DataCleanupJob(self.database)
            self.system_jobs['data_cleanup'] = cleanup_job

            # Schedule data cleanup job
            interval_hours = cleanup_config.get('cleanup_interval_hours', 24)
            job = schedule.every(interval_hours).hours.do(cleanup_job.run)
            self.system_job_schedules['data_cleanup'] = job

            self.logger.info(f"Data cleanup job scheduled to run every {interval_hours} hours")

    def schedule_monitor(self, monitor: BaseMonitor) -> bool:
        with self.monitor_lock:
            # Check if monitor is already scheduled
            if any(m.id == monitor.id for m in self.running_monitors.keys()):
                self.logger.warning(f"Monitor {monitor.name} ({monitor.id}) is already scheduled")
                return False
            
            # Create a job that runs at the specified interval
            interval_seconds = monitor.check_interval_seconds
            
            # Schedule the job
            job = schedule.every(interval_seconds).seconds.do(self._run_monitor, monitor)
            
            # Store the job with the full monitor object as key
            self.running_monitors[monitor] = job

            # Update monitor status
            monitor.status = MonitorStatus.UNKNOWN
            monitor.update_timestamp()
            
            # Save updated monitor
            self.database.save_monitor(monitor)
            
            self.logger.info(f"Scheduled monitor: {monitor.name} ({monitor.id}) - Interval: {interval_seconds}s")
            
            # Run the monitor immediately for the first time
            self._run_monitor(monitor)
            
            return True
        
    def stop_monitor(self, monitor_id: str) -> bool:
        with self.monitor_lock:
            # Find the monitor with the given ID
            monitor_to_stop = None
            for monitor in self.running_monitors.keys():
                if monitor.id == monitor_id:
                    monitor_to_stop = monitor
                    break
                
            if not monitor_to_stop:
                self.logger.warning(f"Monitor {monitor_id} is not scheduled")
                return False
            
            # Get the job
            job = self.running_monitors.pop(monitor_to_stop)
            
            # Cancel the job using schedule's cancel_job method
            schedule.cancel_job(job)
            
            # Update monitor status
            monitor = self.database.get_monitor(monitor_id)
            if monitor:
                monitor.status = MonitorStatus.OFFLINE
                monitor.update_timestamp()
                self.database.save_monitor(monitor)
            
            self.logger.info(f"Stopped monitor: {monitor_id}")
            
            return True
    
    def reschedule_monitor(self, monitor: BaseMonitor) -> bool:
        with self.monitor_lock:
            # Find the monitor with the given ID
            monitor_to_reschedule = None
            for m in self.running_monitors.keys():
                if m.id == monitor.id:
                    monitor_to_reschedule = m
                    break
                
            if monitor_to_reschedule:
                # Cancel the job
                job = self.running_monitors.pop(monitor_to_reschedule)
                job.cancel()
                
                # Update monitor status
                monitor.status = MonitorStatus.UNKNOWN
                monitor.update_timestamp()
                self.database.save_monitor(monitor)
                
                
                # Schedule the job
                interval_seconds = monitor.check_interval_seconds
                job = schedule.every(interval_seconds).seconds.do(self._run_monitor, monitor)
                self.running_monitors[monitor] = job

                self.logger.info(f"Rescheduled monitor: {monitor.name} ({monitor.id}) - Interval: {interval_seconds}s")

                return True
            else:
                self.logger.warning(f"Monitor {monitor.name} ({monitor.id}) is not scheduled")
                return False

    
    def list_running_monitors(self, space_id: Optional[str] = None, monitor_type: Optional[MonitorType] = None) -> List[BaseMonitor]:
        with self.monitor_lock:
            if space_id is None:
                # Return all monitors if no space_id is provided
                return list(self.running_monitors.keys())
            
            # Filter by space_id and optionally by monitor_type
            monitors = []
            for monitor in self.running_monitors.keys():
                if monitor.space_id == space_id:
                    if monitor_type is None or monitor.monitor_type == monitor_type:
                        monitors.append(monitor)
            return monitors

    def is_monitor_running(self, monitor_id: str) -> bool:
        # Check if a monitor is running
        with self.monitor_lock:
            return any(m.id == monitor_id for m in self.running_monitors.keys())

    def start_all_monitors_in_space(self, space_id: str):
        monitors_to_start = self.database.get_monitors_for_space(space_id)
        self.logger.info(f"Found {len(monitors_to_start)} monitors in space: {space_id}")
        
        # Then check which ones need to be started
        with self.monitor_lock:
            # Filter out already running monitors
            monitors_to_schedule = []
            for monitor in monitors_to_start:
                if not any(m.id == monitor.id for m in self.running_monitors.keys()):
                    monitors_to_schedule.append(monitor)
        
        # Schedule each monitor individually outside the lock
        for monitor in monitors_to_schedule:
            self.schedule_monitor(monitor)
        
        self.logger.info(f"Started {len(monitors_to_schedule)} monitors in space: {space_id}")

    def stop_all_monitors_in_space(self, space_id: str):
        with self.monitor_lock:
            for monitor, job in list(self.running_monitors.items()):
                if monitor.space_id == space_id:
                    schedule.cancel_job(job)
                    self.running_monitors.pop(monitor)
                    monitor.status = MonitorStatus.OFFLINE
                    monitor.update_timestamp()
                    self.database.save_monitor(monitor)
            self.logger.info(f"Stopped all monitors in space: {space_id}")

    def stop_all_monitors(self):
        with self.monitor_lock:
            for monitor, job in self.running_monitors.items():
                schedule.cancel_job(job)
                monitor.status = MonitorStatus.OFFLINE
                monitor.update_timestamp()
                self.database.save_monitor(monitor)
            self.running_monitors.clear()
            self.logger.info("Stopped all monitors")

    def get_system_job_status(self) -> List[Dict[str, Any]]:
        status_list = []
        for job_name, job in self.system_jobs.items():
            status = job.get_status()
            status['enabled'] = job_name in self.system_job_schedules
            status_list.append(status)
        return status_list

    def run_system_job_manually(self, job_name: str) -> bool:
        if job_name in self.system_jobs:
            job = self.system_jobs[job_name]
            self.logger.info(f"Manually running system job: {job_name}")
            return job.run()
        else:
            self.logger.warning(f"System job not found: {job_name}")
            return False

    def stop(self):
        self.stop_event.set()
        self.scheduler_thread.join()
