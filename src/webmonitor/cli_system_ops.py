import os
import sys
import yaml
import click
from .cli_utils import send_command, format_response, _format_system_status

def load_yaml_file(file_path: str) -> dict:
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        click.echo(click.style(f"Error loading YAML file: {str(e)}", fg='red'), err=True)
        sys.exit(1)

def save_yaml_file(data: dict, file_path: str) -> None:
    try:
        with open(file_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)
    except Exception as e:
        click.echo(click.style(f"Error saving YAML file: {str(e)}", fg='red'), err=True)
        sys.exit(1)

def create_config(send_command, yaml_file: str, dry_run: bool = False) -> None:
    # Create resources from YAML config. Allows optional IDs.
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
    # Update resources from YAML config. Requires IDs for all resources.
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

# Individual system commands (not in a group)
@click.command('status')
def status():
    response = send_command({'action': 'status'})
    if response.get('status') == 'success':
        _format_system_status(response)
    else:
        format_response(response)

@click.command('create', help='Create spaces and monitors from a YAML file')
@click.argument('yaml_file', type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True))
@click.option('--dry-run', is_flag=True, help='Show what would be created without making changes')
def create_config_command(yaml_file, dry_run):
    create_config(send_command, yaml_file, dry_run)

@click.command('update', help='Update spaces and monitors from a YAML file')
@click.argument('yaml_file', type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True))
@click.option('--dry-run', is_flag=True, help='Show what would be updated without making changes')
def update_config_command(yaml_file, dry_run):
    update_config(send_command, yaml_file, dry_run)

@click.command('export-all', help='Export all spaces and monitors to a YAML file')
@click.option('--output', '-o', type=click.Path(), required=True, help='Output file')
def export_all_command(output):
    response = export_all(send_command, output)
    if response.get('status') != 'success':
        format_response(response)

def print_sample_config_create() -> None:
    sample = {
        'spaces': [
            {
                'name': 'Production Environment',
                'description': 'Monitoring for production services',
                'notification_emails': [
                    'ops-team@example.com',
                    'alerts@example.com'
                ],
                'id': 'production-space-id'
            },
            {
                'name': 'Development Environment',
                'description': 'Monitoring for development services',
                'notification_emails': [
                    'dev-team@example.com'
                ],
                'id': 'development-space-id'
            }
        ],
        'monitors': [
            {
                'name': 'Main Website',
                'space_id': 'production-space-id',
                'monitor_type': 'url',
                'url': 'https://www.example.com',
                'expected_status_code': 200,
                'timeout_seconds': 30,
                'check_ssl': True,
                'follow_redirects': True,
                'check_interval_seconds': 300
            },
            {
                'name': 'Production Database',
                'space_id': 'production-space-id',
                'monitor_type': 'database',
                'db_type': 'postgresql',
                'host': 'prod-db.example.com',
                'port': 5432,
                'database': 'app_production',
                'username': 'monitor_user',
                'password': 'secure_password',
                'connection_timeout_seconds': 10,
                'query_timeout_seconds': 30,
                'test_query': 'SELECT 1',
                'check_interval_seconds': 600
            }
        ]
    }

    click.echo("# Sample YAML for create config command")
    click.echo("# Save this to a file and use: webmonitor create <file>")
    click.echo("# IDs are optional - will be auto-generated if not provided")
    click.echo("# You can reference space IDs in monitors, or use the generated ones")
    click.echo()
    click.echo(yaml.dump(sample, default_flow_style=False))

def print_sample_config_update() -> None:
    sample = {
        'spaces': [
            {
                'id': 'existing-production-space-id',
                'name': 'Updated Production Environment',
                'description': 'Updated monitoring for production services',
                'notification_emails': [
                    'ops-team@example.com',
                    'alerts@example.com',
                    'manager@example.com'
                ]
            },
            {
                'id': 'existing-dev-space-id',
                'name': 'Updated Development Environment',
                'description': 'Updated monitoring for development services',
                'notification_emails': [
                    'dev-team@example.com',
                    'qa-team@example.com'
                ]
            }
        ],
        'monitors': [
            {
                'id': 'existing-website-monitor-id',
                'name': 'Updated Main Website',
                'space_id': 'existing-production-space-id',
                'monitor_type': 'url',
                'url': 'https://www.updated-example.com',
                'expected_status_code': 200,
                'timeout_seconds': 45,
                'check_ssl': True,
                'follow_redirects': True,
                'check_content': 'Welcome to our updated site',
                'check_interval_seconds': 300
            },
            {
                'id': 'existing-database-monitor-id',
                'name': 'Updated Production Database',
                'space_id': 'existing-production-space-id',
                'monitor_type': 'database',
                'db_type': 'postgresql',
                'host': 'new-prod-db.example.com',
                'port': 5432,
                'database': 'app_production_v2',
                'username': 'updated_monitor_user',
                'password': 'new_secure_password',
                'connection_timeout_seconds': 15,
                'query_timeout_seconds': 45,
                'test_query': 'SELECT COUNT(*) FROM health_status',
                'check_interval_seconds': 600
            }
        ]
    }

    click.echo("# Sample YAML for update config command")
    click.echo("# Save this to a file and use: webmonitor update <file>")
    click.echo("# IDs are required for all resources when updating")
    click.echo("# All spaces and monitors must have existing IDs")
    click.echo()
    click.echo(yaml.dump(sample, default_flow_style=False))

@click.command('sample-create')
def sample_create():
    print_sample_config_create()

@click.command('sample-update')
def sample_update():
    print_sample_config_update()

# List of individual commands to be added to the main CLI
SYSTEM_COMMANDS = [
    status,
    create_config_command,
    update_config_command,
    export_all_command,
    sample_create,
    sample_update
]
