import logging
from typing import Dict, Any, Optional
from webmonitor.infrastructure import Database
from webmonitor.services import MonitorScheduler
from .handlers import (
    MonitorCommandHandler,
    SpaceCommandHandler,
    ResultCommandHandler,
    SystemCommandHandler
)

class CommandHandler:
    # Main command handler that delegates to specific handlers
    
    def __init__(self, database: Database, scheduler: MonitorScheduler):
        self.logger = logging.getLogger(__name__)
        self.database = database
        self.scheduler = scheduler
        
        # Initialize specific handlers
        self.monitor_handler = MonitorCommandHandler(database, scheduler)
        self.space_handler = SpaceCommandHandler(database, scheduler)
        self.result_handler = ResultCommandHandler(database)
        self.system_handler = SystemCommandHandler(scheduler, database)
        
        # Command routing map
        self.command_routes = {
            # Monitor commands
            'start_monitor': self.monitor_handler.start_monitor,
            'stop_monitor': self.monitor_handler.stop_monitor,
            'list_monitors': self.monitor_handler.list_monitors,
            'get_monitor': self.monitor_handler.get_monitor,
            'create_monitor': self.monitor_handler.create_monitor,
            'update_monitor': self.monitor_handler.update_monitor,
            'delete_monitor': self.monitor_handler.delete_monitor,
            
            # Space commands
            'start_space': self.space_handler.start_space,
            'stop_space': self.space_handler.stop_space,
            'list_spaces': self.space_handler.list_spaces,
            'get_space': self.space_handler.get_space,
            'create_space': self.space_handler.create_space,
            'update_space': self.space_handler.update_space,
            'delete_space': self.space_handler.delete_space,
            
            # Result commands
            'get_monitor_results': self.result_handler.get_monitor_results,
            'get_space_results': self.result_handler.get_space_results,
            
            # System commands
            'status': self.system_handler.get_status,

            # Job commands
            'get_job_status': self.system_handler.get_job_status,
            'run_job_manually': self.system_handler.run_job_manually,
            'get_cleanup_preview': self.system_handler.get_cleanup_preview,

            # Email commands
            'reload_email_config': self.reload_email_config,
        }
    
    def handle_command(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        # Route command to appropriate handler
        try:
            action = command_data.get('action')
            
            if action in self.command_routes:
                return self.command_routes[action](command_data)
            else:
                return {'status': 'error', 'message': 'Unknown action'}

        except Exception as e:
            self.logger.error(f"Error handling command: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': str(e)}

    def reload_email_config(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Reload email configuration."""
        try:
            from webmonitor.services.email_service import reload_email_service

            success = reload_email_service()
            if success:
                return {'status': 'success', 'message': 'Email configuration reloaded successfully'}
            else:
                return {'status': 'error', 'message': 'Failed to reload email configuration'}
        except Exception as e:
            return {'status': 'error', 'message': f'Error reloading email config: {str(e)}'}