import logging
from typing import Dict, Any
from webmonitor.models import UrlMonitor, DatabaseMonitor, MonitorType
from webmonitor.services import MonitorScheduler
from webmonitor.infrastructure import Database
from webmonitor.utils import encrypt_password


class MonitorCommandHandler:
    # Handler for monitor-related commands
    
    def __init__(self, database: Database, scheduler: MonitorScheduler):
        self.logger = logging.getLogger(__name__)
        self.database = database
        self.scheduler = scheduler
    
    def start_monitor(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        # Start a monitor
        monitor_id = cmd.get('monitor_id')
        monitor_name = cmd.get('monitor_name')
        space_id = cmd.get('space_id')
        space_name = cmd.get('space_name')

        if not monitor_id and not monitor_name:
            return {'status': 'error', 'message': 'Monitor ID or name required'}

        # If name is provided but not ID, try to resolve the name to an ID
        if not monitor_id and monitor_name:
            monitor = self.database.get_monitor_by_name(monitor_name, space_id, space_name)
            if not monitor:
                space_msg = f' in space "{space_id}"' if space_id else ''
                return {'status': 'error', 'message': f'Monitor with name "{monitor_name}"{space_msg} not found'}
            monitor_id = monitor.id
        else:
            monitor = self.database.get_monitor(monitor_id)
            if not monitor:
                return {'status': 'error', 'message': 'Monitor not found'}

        success = self.scheduler.schedule_monitor(monitor)
        return {
            'status': 'success' if success else 'error',
            'message': f'Monitor {monitor.name} started' if success else 'Failed to start monitor'
        }
    
    def stop_monitor(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        # Stop a monitor
        monitor_id = cmd.get('monitor_id')
        monitor_name = cmd.get('monitor_name')
        space_id = cmd.get('space_id')

        if not monitor_id and not monitor_name:
            return {'status': 'error', 'message': 'Monitor ID or name required'}

        # If name is provided but not ID, try to resolve the name to an ID
        if not monitor_id and monitor_name:
            monitor = self.database.get_monitor_by_name(monitor_name, space_id)
            if not monitor:
                space_msg = f' in space "{space_id}"' if space_id else ''
                return {'status': 'error', 'message': f'Monitor with name "{monitor_name}"{space_msg} not found'}
            monitor_id = monitor.id
            monitor_display_name = monitor.name
        else:
            monitor = self.database.get_monitor(monitor_id)
            monitor_display_name = monitor.name if monitor else monitor_id

        success = self.scheduler.stop_monitor(monitor_id)
        return {
            'status': 'success' if success else 'error',
            'message': f'Monitor {monitor_display_name} stopped' if success else 'Failed to stop monitor'
        }
    
    def list_monitors(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        # List monitors for a space if space_id is provided, otherwise list all monitors
        space_id = cmd.get('space_id')
        monitors = []
        if not space_id:
            monitors = self.database.list_monitors()
        else:
            monitors = self.database.get_monitors_for_space(space_id)
            
        running_ids = [m.id for m in self.scheduler.list_running_monitors()]

        monitor_dicts = []
        for monitor in monitors:
            monitor_dict = monitor.to_dict()
            monitor_dict['running'] = monitor.id in running_ids
            monitor_dicts.append(monitor_dict)
        
        return {
            'status': 'success',
            'monitors': monitor_dicts
        }
    
    def get_monitor(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        # Get a monitor by ID
        monitor_id = cmd.get('monitor_id')
        if not monitor_id:
            return {'status': 'error', 'message': 'Monitor ID required'}
            
        monitor = self.database.get_monitor(monitor_id)
        if not monitor:
            return {'status': 'error', 'message': 'Monitor not found'}
            
        running_ids = [m.id for m in self.scheduler.list_running_monitors()]
        monitor_dict = monitor.to_dict()
        monitor_dict['running'] = monitor.id in running_ids
        
        return {
            'status': 'success',
            'monitor': monitor_dict
        }
    
    def create_monitor(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        # Create a new monitor
        monitor_data = cmd.get('monitor')
        if not monitor_data or 'name' not in monitor_data or 'space_id' not in monitor_data:
            return {'status': 'error', 'message': 'Monitor name and space_id required'}
            
        # Check if space exists
        space = self.database.get_space(monitor_data['space_id'])
        if not space:
            return {'status': 'error', 'message': 'Space not found'}

        # Check if monitor name already exists
        existing_monitor = self.database.get_monitor_by_name(monitor_data['name'], monitor_data['space_id'])
        if existing_monitor:
            return {'status': 'error', 'message': 'Monitor name already exists in this space'}
            
        monitor_type = monitor_data.get('monitor_type')
        if not monitor_type:
            return {'status': 'error', 'message': 'Monitor type required'}
        
        if monitor_type == 'url':
            if 'url' not in monitor_data:
                return {'status': 'error', 'message': 'URL required for URL monitor'}
                
            monitor = UrlMonitor(
                name=monitor_data['name'],
                space_id=monitor_data['space_id'],
                monitor_type=MonitorType.URL,
                url=monitor_data['url'],
                expected_status_code=monitor_data.get('expected_status_code', 200),
                timeout_seconds=monitor_data.get('timeout_seconds', 30),
                check_ssl=monitor_data.get('check_ssl', True),
                follow_redirects=monitor_data.get('follow_redirects', True),
                check_content=monitor_data.get('check_content'),
                check_interval_seconds=monitor_data.get('check_interval_seconds', 300)
            )
        elif monitor_type == 'database':
            required_fields = ['db_type', 'host', 'port', 'database', 'username']
            for field in required_fields:
                if field not in monitor_data:
                    return {'status': 'error', 'message': f'{field} required for database monitor'}
                    
            monitor = DatabaseMonitor(
                name=monitor_data['name'],
                space_id=monitor_data['space_id'],
                monitor_type=MonitorType.DATABASE,
                db_type=monitor_data['db_type'],
                host=monitor_data['host'],
                port=monitor_data['port'],
                database=monitor_data['database'],
                username=monitor_data['username'],
                connection_timeout_seconds=monitor_data.get('connection_timeout_seconds', 30),
                query_timeout_seconds=monitor_data.get('query_timeout_seconds', 30),
                test_query=monitor_data.get('test_query', 'SELECT 1'),
                check_interval_seconds=monitor_data.get('check_interval_seconds', 300)
            )
            
            # Set the password using the setter method which handles encryption
            if 'password' in monitor_data:
                monitor.password = monitor_data['password']
        else:
            return {'status': 'error', 'message': 'Invalid monitor type'}
            
        saved_monitor = self.database.save_monitor(monitor)
            
        return {
            'status': 'success',
            'message': f'Monitor {saved_monitor.name} created',
            'monitor': saved_monitor.to_dict()
        }
    
    def update_monitor(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        # Update an existing monitor
        monitor_data = cmd.get('monitor')
        if not monitor_data or 'id' not in monitor_data:
            return {'status': 'error', 'message': 'Monitor ID required'}
            
        monitor = self.database.get_monitor(monitor_data['id'])
        if not monitor:
            return {'status': 'error', 'message': 'Monitor not found'}
            
        # Check if monitor is running
        was_running = False
        running_ids = [m.id for m in self.scheduler.list_running_monitors()]
        if monitor.id in running_ids:
            was_running = True
            self.scheduler.stop_monitor(monitor.id)
            
        # Update common fields
        if 'name' in monitor_data:
            # Check if new name already exists
            if monitor_data['name'] != monitor.name:
                existing_monitor = self.database.get_monitor_by_name(monitor_data['name'], monitor.space_id)
                if existing_monitor and existing_monitor.id != monitor.id:
                    return {'status': 'error', 'message': 'Monitor name already exists in this space'}
            monitor.name = monitor_data['name']
        if 'check_interval_seconds' in monitor_data:
            monitor.check_interval_seconds = monitor_data['check_interval_seconds']
            
        # Update type-specific fields
        if isinstance(monitor, UrlMonitor):
            if 'url' in monitor_data:
                monitor.url = monitor_data['url']
            if 'expected_status_code' in monitor_data:
                monitor.expected_status_code = monitor_data['expected_status_code']
            if 'timeout_seconds' in monitor_data:
                monitor.timeout_seconds = monitor_data['timeout_seconds']
            if 'check_ssl' in monitor_data:
                monitor.check_ssl = monitor_data['check_ssl']
            if 'follow_redirects' in monitor_data:
                monitor.follow_redirects = monitor_data['follow_redirects']
            if 'check_content' in monitor_data:
                monitor.check_content = monitor_data['check_content']
        elif isinstance(monitor, DatabaseMonitor):
            if 'host' in monitor_data:
                monitor.host = monitor_data['host']
            if 'port' in monitor_data:
                monitor.port = monitor_data['port']
            if 'database' in monitor_data:
                monitor.database = monitor_data['database']
            if 'username' in monitor_data:
                monitor.username = monitor_data['username']
            if 'password' in monitor_data:
                monitor.password = monitor_data['password']
            if 'connection_timeout_seconds' in monitor_data:
                monitor.connection_timeout_seconds = monitor_data['connection_timeout_seconds']
            if 'query_timeout_seconds' in monitor_data:
                monitor.query_timeout_seconds = monitor_data['query_timeout_seconds']
            if 'test_query' in monitor_data:
                monitor.test_query = monitor_data['test_query']
                
        monitor.update_timestamp()
        saved_monitor = self.database.save_monitor(monitor)
        
        # Restart if it was running before
        if was_running:
            self.scheduler.schedule_monitor(saved_monitor)
            
        return {
            'status': 'success',
            'message': f'Monitor {saved_monitor.name} updated',
            'monitor': saved_monitor.to_dict()
        }
    
    def delete_monitor(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        # Delete a monitor
        monitor_id = cmd.get('monitor_id')
        if not monitor_id:
            return {'status': 'error', 'message': 'Monitor ID required'}
            
        # Stop the monitor if it's running
        self.scheduler.stop_monitor(monitor_id)
        
        success = self.database.delete_monitor(monitor_id)
        if not success:
            return {'status': 'error', 'message': 'Monitor not found or could not be deleted'}
            
        return {
            'status': 'success',
            'message': f'Monitor {monitor_id} deleted'
        }

