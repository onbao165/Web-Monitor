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
        limit = cmd.get('limit', 10)
        
        if not monitor_id:
            return {'status': 'error', 'message': 'Monitor ID required'}
            
        results = self.database.get_results_for_monitor(monitor_id, limit)
        
        return {
            'status': 'success',
            'results': [result.to_dict() for result in results]
        }
    
    def get_space_results(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        # Get results for all monitors in a space
        space_id = cmd.get('space_id')
        limit = cmd.get('limit', 10)
        
        if not space_id:
            return {'status': 'error', 'message': 'Space ID required'}
            
        results = self.database.get_results_for_space(space_id, limit)
        
        return {
            'status': 'success',
            'results': [result.to_dict() for result in results]
        }