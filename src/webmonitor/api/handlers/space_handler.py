import logging
from typing import Dict, Any
from webmonitor.models import Space
from webmonitor.services import MonitorScheduler
from webmonitor.infrastructure import Database

class SpaceCommandHandler:
    # Handler for space-related commands
    
    def __init__(self, database: Database, scheduler: MonitorScheduler):
        self.logger = logging.getLogger(__name__)
        self.database = database
        self.scheduler = scheduler
    
    def start_space(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        # Start all monitors in a space
        space_id = cmd.get('space_id')
        space_name = cmd.get('space_name')

        if not space_id and not space_name:
            return {'status': 'error', 'message': 'Space ID or name required'}

        # If name is provided but not ID, try to resolve the name to an ID
        if not space_id and space_name:
            space = self.database.get_space_by_name(space_name)
            if not space:
                return {'status': 'error', 'message': f'Space with name "{space_name}" not found'}
            space_id = space.id

        self.scheduler.start_all_monitors_in_space(space_id)
        return {'status': 'success', 'message': f'All monitors in space {space_id} started'}
    
    def stop_space(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        # Stop all monitors in a space
        space_id = cmd.get('space_id')
        space_name = cmd.get('space_name')

        if not space_id and not space_name:
            return {'status': 'error', 'message': 'Space ID or name required'}

        # If name is provided but not ID, try to resolve the name to an ID
        if not space_id and space_name:
            space = self.database.get_space_by_name(space_name)
            if not space:
                return {'status': 'error', 'message': f'Space with name "{space_name}" not found'}
            space_id = space.id

        self.scheduler.stop_all_monitors_in_space(space_id)
        return {'status': 'success', 'message': f'All monitors in space {space_id} stopped'}
    
    def list_spaces(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        # List all spaces
        spaces = self.database.list_spaces()
        return {
            'status': 'success',
            'spaces': [space.to_dict() for space in spaces]
        }
    
    def get_space(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        # Get a space by ID
        space_id = cmd.get('space_id')
        if not space_id:
            return {'status': 'error', 'message': 'Space ID required'}
            
        space = self.database.get_space(space_id)
        if not space:
            return {'status': 'error', 'message': 'Space not found'}
            
        return {
            'status': 'success',
            'space': space.to_dict()
        }
    
    def create_space(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        # Create a new space
        space_data = cmd.get('space')
        if not space_data or 'name' not in space_data:
            return {'status': 'error', 'message': 'Space name required'}

        # Check if space name already exists
        existing_space = self.database.get_space_by_name(space_data['name'])
        if existing_space:
            return {'status': 'error', 'message': 'Space name already exists'}
            
        space = Space(
            name=space_data['name'],
            description=space_data.get('description'),
            notification_emails=space_data.get('notification_emails', [])
        )

        # Use provided ID if provided
        if 'id' in space_data:
            space.id = space_data['id']
        
        saved_space = self.database.save_space(space)
        return {
            'status': 'success',
            'message': f'Space {saved_space.name} created',
            'space': saved_space.to_dict()
        }
    
    def update_space(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        # Update an existing space
        space_data = cmd.get('space')
        if not space_data or 'id' not in space_data:
            return {'status': 'error', 'message': 'Space ID required'}
            
        space = self.database.get_space(space_data['id'])
        if not space:
            return {'status': 'error', 'message': 'Space not found'}
            
        # Update fields
        if 'name' in space_data:
            # Check if new name already exists
            if space_data['name'] != space.name:
                existing_space = self.database.get_space_by_name(space_data['name'])
                if existing_space and existing_space.id != space.id:
                    return {'status': 'error', 'message': 'Space name already exists'}
            space.name = space_data['name']
        if 'description' in space_data:
            space.description = space_data['description']
        if 'notification_emails' in space_data:
            space.notification_emails = space_data['notification_emails']
            
        space.update_timestamp()
        saved_space = self.database.save_space(space)
        
        return {
            'status': 'success',
            'message': f'Space {saved_space.name} updated',
            'space': saved_space.to_dict()
        }
    
    def delete_space(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        # Delete a space
        space_id = cmd.get('space_id')
        if not space_id:
            return {'status': 'error', 'message': 'Space ID required'}
            
        # Stop all monitors in this space first
        self.scheduler.stop_all_monitors_in_space(space_id)

        # Delete all monitors in this space
        monitors = self.database.get_monitors_for_space(space_id)
        for monitor in monitors:
            self.database.delete_monitor(monitor.id)
        
        success = self.database.delete_space(space_id)
        if not success:
            return {'status': 'error', 'message': 'Space not found or could not be deleted'}
            
        return {
            'status': 'success',
            'message': f'Space {space_id} deleted'
        }