import logging
from typing import Dict, Any
from webmonitor.services import MonitorScheduler
from webmonitor.config import get_config_manager
from webmonitor.infrastructure import Database

class SystemCommandHandler:
    # Handler for system-related commands

    def __init__(self, scheduler: MonitorScheduler, database: Database = None):
        self.logger = logging.getLogger(__name__)
        self.scheduler = scheduler
        self.database = database
        self.config_manager = get_config_manager()
    
    def get_status(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        running_monitors = self.scheduler.list_running_monitors()
        monitor_dicts = []
        for monitor in running_monitors:
            monitor_dict = monitor.to_dict()
            monitor_dicts.append(monitor_dict)

        return {
            'status': 'success',
            'running': True,
            'total_monitors': len(running_monitors),
            'monitors': monitor_dicts
        }

    def get_job_status(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        try:
            jobs = self.scheduler.get_system_job_status()
            return {
                'status': 'success',
                'jobs': jobs
            }
        except Exception as e:
            self.logger.error(f"Error getting job status: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def run_job_manually(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        job_name = cmd.get('job_name')
        if not job_name:
            return {'status': 'error', 'message': 'Job name required'}

        try:
            # Convert CLI job names to internal names
            internal_name = self._convert_job_name(job_name)
            success = self.scheduler.run_system_job_manually(internal_name)

            if success:
                return {'status': 'success', 'message': f'Job {job_name} completed successfully'}
            else:
                return {'status': 'error', 'message': f'Job {job_name} failed or not found'}
        except Exception as e:
            self.logger.error(f"Error running job manually: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def get_cleanup_preview(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        if not self.database:
            return {'status': 'error', 'message': 'Database not available'}

        try:
            cleanup_config = self.config_manager.get_data_cleanup_config()
            keep_healthy_days = cleanup_config.get('keep_healthy_results_days', 7)
            keep_unhealthy_days = cleanup_config.get('keep_unhealthy_results_days', 30)

            preview = self.database.get_cleanup_preview(keep_healthy_days, keep_unhealthy_days)
            
            # Convert datetime objects to ISO format strings
            if 'healthy_cutoff_date' in preview and preview['healthy_cutoff_date']:
                preview['healthy_cutoff_date'] = preview['healthy_cutoff_date'].isoformat()
            if 'unhealthy_cutoff_date' in preview and preview['unhealthy_cutoff_date']:
                preview['unhealthy_cutoff_date'] = preview['unhealthy_cutoff_date'].isoformat()

            return {
                'status': 'success',
                'preview': preview
            }
        except Exception as e:
            self.logger.error(f"Error getting cleanup preview: {str(e)}")
            return {'status': 'error', 'message': str(e)}

    def _convert_job_name(self, cli_name: str) -> str:
        """Convert CLI job names to internal job names."""
        name_mapping = {
            'health-alerts': 'health_alert',
            'health_alert': 'health_alert',
            'data-cleanup': 'data_cleanup',
            'data_cleanup': 'data_cleanup'
        }
        return name_mapping.get(cli_name, cli_name)

