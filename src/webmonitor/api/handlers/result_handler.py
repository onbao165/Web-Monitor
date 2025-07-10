import logging
from typing import Dict, Any
from datetime import datetime, timedelta
from  webmonitor.infrastructure import Database

class ResultCommandHandler:
    # Handler for result-related commands
    
    def __init__(self, database: Database):
        self.logger = logging.getLogger(__name__)
        self.database = database
    
    def get_monitor_results(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        # Get results for a monitor
        monitor_id = cmd.get('monitor_id')
        monitor_name = cmd.get('monitor_name')
        space_id = cmd.get('space_id')
        space_name = cmd.get('space_name')
        limit = cmd.get('limit', 10)
        
        if not monitor_id and not monitor_name:
            return {'status': 'error', 'message': 'Monitor ID or name required'}
        
        # If name is provided but not ID, try to resolve the name to an ID
        if not monitor_id and monitor_name:
            monitor = self.database.get_monitor_by_name(monitor_name, space_id, space_name)
            if not monitor:
                space_msg = f' in space "{space_id}"' if space_id else ''
                return {'status': 'error', 'message': f'Monitor with name "{monitor_name}"{space_msg} not found'}
            monitor_id = monitor.id
            
        results = self.database.get_results_for_monitor(monitor_id, limit)
        
        return {
            'status': 'success',
            'results': [result.to_dict() for result in results]
        }
    
    def get_space_results(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        # Get results for all monitors in a space
        space_id = cmd.get('space_id')
        space_name = cmd.get('space_name')
        limit = cmd.get('limit', 10)
        
        if not space_id and not space_name:
            return {'status': 'error', 'message': 'Space ID or name required'}
        
        # If name is provided but not ID, try to resolve the name to an ID
        if not space_id and space_name:
            space = self.database.get_space_by_name(space_name)
            if not space:
                return {'status': 'error', 'message': f'Space with name "{space_name}" not found'}
            space_id = space.id
            
        results = self.database.get_results_for_space(space_id, limit)
        
        return {
            'status': 'success',
            'results': [result.to_dict() for result in results]
        }