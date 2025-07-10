import logging
from typing import Dict, Any
from webmonitor.services import MonitorScheduler

class SystemCommandHandler:
    # Handler for system-related commands
    
    def __init__(self, scheduler: MonitorScheduler):
        self.logger = logging.getLogger(__name__)
        self.scheduler = scheduler
    
    def get_status(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        # Get system status
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
