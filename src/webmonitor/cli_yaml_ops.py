import os
import sys
import yaml
import click
from typing import Dict, Any, List

def load_yaml_file(file_path: str) -> Dict:
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        click.echo(click.style(f"Error loading YAML file: {str(e)}", fg='red'), err=True)
        sys.exit(1)

def save_yaml_file(data: Dict, file_path: str) -> None:
    try:
        with open(file_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)
    except Exception as e:
        click.echo(click.style(f"Error saving YAML file: {str(e)}", fg='red'), err=True)
        sys.exit(1)

def create_space_from_file(send_command, file: str) -> Dict:
    space_data = load_yaml_file(file)
    return send_command({
        'action': 'create_space',
        'space': space_data
    })

def update_space_from_file(send_command, file: str) -> Dict:
    space_data = load_yaml_file(file)
    
    # Ensure the ID in the command takes precedence
    space_data['id'] = space_id
    
    return send_command({
        'action': 'update_space',
        'space': space_data
    })

def create_monitor_from_file(send_command, file: str) -> Dict:
    monitor_data = load_yaml_file(file)

    # Ensure space_id is provided
    if 'space_id' not in monitor_data:
        click.echo(click.style("Monitor definition is missing required 'space_id' field", fg='red'), err=True)
        sys.exit(1)

    return send_command({
        'action': 'create_monitor',
        'monitor': monitor_data
    })

def update_monitor_from_file(send_command, file: str) -> Dict:
    monitor_data = load_yaml_file(file)
    
    # Ensure the ID in the command takes precedence
    monitor_data['id'] = monitor_id
    
    return send_command({
        'action': 'update_monitor',
        'monitor': monitor_data
    })

def export_space(send_command, space_id: str, output: str = None) -> None:
    response = send_command({'action': 'get_space', 'space_id': space_id})
    
    if response.get('status') != 'success':
        return response
    
    space_data = response.get('space', {})
    yaml_str = yaml.dump(space_data, default_flow_style=False)
    
    if output:
        with open(output, 'w') as f:
            f.write(yaml_str)
        click.echo(f"Space exported to {output}")
    else:
        click.echo(yaml_str)
    
    return response

def export_monitor(send_command, monitor_id: str, output: str = None) -> None:
    response = send_command({'action': 'get_monitor', 'monitor_id': monitor_id})
    
    if response.get('status') != 'success':
        return response
    
    monitor_data = response.get('monitor', {})
    yaml_str = yaml.dump(monitor_data, default_flow_style=False)
    
    if output:
        with open(output, 'w') as f:
            f.write(yaml_str)
        click.echo(f"Monitor exported to {output}")
    else:
        click.echo(yaml_str)
    
    return response

def create_config(send_command, yaml_file: str, dry_run: bool = False) -> None:
    """Create resources from YAML config. Allows optional IDs."""
    config = load_yaml_file(yaml_file)

    # Track results
    results = {
        'spaces': {'created': 0, 'failed': 0},
        'monitors': {'created': 0, 'failed': 0}
    }

    # Process spaces first
    if 'spaces' in config:
        click.echo("Creating spaces...")
        for space in config['spaces']:
            space_name = space.get('name')

            if dry_run:
                click.echo(f"  Would create space '{space_name}'")
                continue

            # Create new space (ID is optional)
            response = send_command({
                'action': 'create_space',
                'space': space
            })

            if response.get('status') == 'success':
                click.echo(click.style(f"  Created space '{space_name}'", fg='green'))
                results['spaces']['created'] += 1
                # Store the new ID in case monitors reference it
                if 'space' in response:
                    space['id'] = response['space']['id']
            else:
                click.echo(click.style(f"  Failed to create space '{space_name}': {response.get('message')}", fg='red'))
                results['spaces']['failed'] += 1

    # Process monitors
    if 'monitors' in config:
        click.echo("Creating monitors...")
        for monitor in config['monitors']:
            monitor_name = monitor.get('name')

            if dry_run:
                click.echo(f"  Would create monitor '{monitor_name}'")
                continue

            # Ensure space_id is provided
            if 'space_id' not in monitor:
                click.echo(click.style(f"Monitor '{monitor_name}' is missing required 'space_id' field", fg='red'), err=True)
                results['monitors']['failed'] += 1
                continue

            # Create new monitor (ID is optional)
            response = send_command({
                'action': 'create_monitor',
                'monitor': monitor
            })

            if response.get('status') == 'success':
                click.echo(click.style(f"  Created monitor '{monitor_name}'", fg='green'))
                results['monitors']['created'] += 1
            else:
                click.echo(click.style(f"  Failed to create monitor '{monitor_name}': {response.get('message')}", fg='red'))
                results['monitors']['failed'] += 1

    # Print summary
    if dry_run:
        click.echo("\nDry run completed. No changes were made.")
    else:
        click.echo("\nCreate completed:")
        click.echo(f"  Spaces: {results['spaces']['created']} created, {results['spaces']['failed']} failed")
        click.echo(f"  Monitors: {results['monitors']['created']} created, {results['monitors']['failed']} failed")

def update_config(send_command, yaml_file: str, dry_run: bool = False) -> None:
    """Update resources from YAML config. Requires IDs for all resources."""
    config = load_yaml_file(yaml_file)

    # Validate that all resources have IDs
    validation_errors = []

    if 'spaces' in config:
        for i, space in enumerate(config['spaces']):
            if not space.get('id'):
                space_name = space.get('name', f'space at index {i}')
                validation_errors.append(f"Space '{space_name}' is missing required 'id' field")

    if 'monitors' in config:
        for i, monitor in enumerate(config['monitors']):
            if not monitor.get('id'):
                monitor_name = monitor.get('name', f'monitor at index {i}')
                validation_errors.append(f"Monitor '{monitor_name}' is missing required 'id' field")

    if validation_errors:
        click.echo(click.style("Validation errors found:", fg='red'), err=True)
        for error in validation_errors:
            click.echo(click.style(f"  - {error}", fg='red'), err=True)
        click.echo(click.style("Update operation aborted. All resources must have 'id' fields for updates.", fg='red'), err=True)
        sys.exit(1)

    # Track results
    results = {
        'spaces': {'updated': 0, 'failed': 0},
        'monitors': {'updated': 0, 'failed': 0}
    }

    # Process spaces first
    if 'spaces' in config:
        click.echo("Updating spaces...")
        for space in config['spaces']:
            space_name = space.get('name')
            space_id = space.get('id')

            if dry_run:
                click.echo(f"  Would update space '{space_name}' (ID: {space_id})")
                continue

            # Update existing space
            response = send_command({
                'action': 'update_space',
                'space': space
            })

            if response.get('status') == 'success':
                click.echo(click.style(f"  Updated space '{space_name}' (ID: {space_id})", fg='green'))
                results['spaces']['updated'] += 1
            else:
                click.echo(click.style(f"  Failed to update space '{space_name}': {response.get('message')}", fg='red'))
                results['spaces']['failed'] += 1

    # Process monitors
    if 'monitors' in config:
        click.echo("Updating monitors...")
        for monitor in config['monitors']:
            monitor_name = monitor.get('name')
            monitor_id = monitor.get('id')

            if dry_run:
                click.echo(f"  Would update monitor '{monitor_name}' (ID: {monitor_id})")
                continue

            # Update existing monitor
            response = send_command({
                'action': 'update_monitor',
                'monitor': monitor
            })

            if response.get('status') == 'success':
                click.echo(click.style(f"  Updated monitor '{monitor_name}' (ID: {monitor_id})", fg='green'))
                results['monitors']['updated'] += 1
            else:
                click.echo(click.style(f"  Failed to update monitor '{monitor_name}': {response.get('message')}", fg='red'))
                results['monitors']['failed'] += 1

    # Print summary
    if dry_run:
        click.echo("\nDry run completed. No changes were made.")
    else:
        click.echo("\nUpdate completed:")
        click.echo(f"  Spaces: {results['spaces']['updated']} updated, {results['spaces']['failed']} failed")
        click.echo(f"  Monitors: {results['monitors']['updated']} updated, {results['monitors']['failed']} failed")

def export_all(send_command, output: str) -> None:
    # If the output path does not contains yaml extension, add it
    if not output.endswith('.yaml') and not output.endswith('.yml'):
        output += '.yaml'

    # Get all spaces
    spaces_response = send_command({'action': 'list_spaces'})
    if spaces_response.get('status') != 'success':
        return spaces_response

    # Get all monitors
    monitors_response = send_command({'action': 'list_monitors'})
    if monitors_response.get('status') != 'success':
        return monitors_response

    # Combine into a single config
    config = {
        'spaces': spaces_response.get('spaces', []),
        'monitors': monitors_response.get('monitors', [])
    }

    # Write to file
    save_yaml_file(config, output)
    click.echo(f"Exported {len(config['spaces'])} spaces and {len(config['monitors'])} monitors to {output}")

    return {'status': 'success', 'message': 'Export completed successfully'}