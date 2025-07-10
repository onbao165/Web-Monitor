import os
import sys
import yaml
import click
from .cli_utils import send_command, format_response

def load_yaml_file(file_path: str) -> dict:
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        click.echo(click.style(f"Error loading YAML file: {str(e)}", fg='red'), err=True)
        sys.exit(1)

def create_monitor_from_file(send_command, file: str) -> dict:
    monitor_data = load_yaml_file(file)

    # Ensure space_id is provided
    if 'space_id' not in monitor_data:
        click.echo(click.style("Monitor definition is missing required 'space_id' field", fg='red'), err=True)
        sys.exit(1)

    return send_command({
        'action': 'create_monitor',
        'monitor': monitor_data
    })

def update_monitor_from_file(send_command, file: str) -> dict:
    monitor_data = load_yaml_file(file)

    return send_command({
        'action': 'update_monitor',
        'monitor': monitor_data
    })

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

def print_sample_monitor_create(monitor_type: str) -> None:
    if monitor_type.lower() == 'url':
        sample = {
            'name': 'Website Health Check',
            'space_id': 'space-uuid-here',
            'monitor_type': 'url',
            'url': 'https://example.com',
            'expected_status_code': 200,
            'timeout_seconds': 30,
            'check_ssl': True,
            'follow_redirects': True,
            'check_content': 'Welcome',
            'check_interval_seconds': 300
        }
    elif monitor_type.lower() == 'database':
        sample = {
            'name': 'Database Health Check',
            'space_id': 'space-uuid-here',
            'monitor_type': 'database',
            'db_type': 'postgresql',
            'host': 'localhost',
            'port': 5432,
            'database': 'myapp',
            'username': 'monitor_user',
            'password': 'secure_password',
            'connection_timeout_seconds': 10,
            'query_timeout_seconds': 30,
            'test_query': 'SELECT 1',
            'check_interval_seconds': 300
        }
    else:
        click.echo(click.style(f"Unknown monitor type: {monitor_type}. Supported types: url, database", fg='red'), err=True)
        return

    click.echo(f"# Sample YAML for creating a {monitor_type} monitor")
    click.echo("# Save this to a file and use: webmonitor monitor create-from-file -f <file>")
    click.echo("# ID is optional - will be auto-generated if not provided")
    click.echo("# space_id is required and must reference an existing space")
    click.echo()
    click.echo(yaml.dump(sample, default_flow_style=False))

def print_sample_monitor_update(monitor_type: str) -> None:
    if monitor_type.lower() == 'url':
        sample = {
            'id': 'monitor-uuid-here',
            'name': 'Updated Website Health Check',
            'space_id': 'space-uuid-here',
            'monitor_type': 'url',
            'url': 'https://updated-example.com',
            'expected_status_code': 200,
            'timeout_seconds': 45,
            'check_ssl': True,
            'follow_redirects': True,
            'check_content': 'Updated Welcome',
            'check_interval_seconds': 600
        }
    elif monitor_type.lower() == 'database':
        sample = {
            'id': 'monitor-uuid-here',
            'name': 'Updated Database Health Check',
            'space_id': 'space-uuid-here',
            'monitor_type': 'database',
            'db_type': 'mysql',
            'host': 'db.example.com',
            'port': 3306,
            'database': 'production_db',
            'username': 'updated_monitor_user',
            'password': 'new_secure_password',
            'connection_timeout_seconds': 15,
            'query_timeout_seconds': 45,
            'test_query': 'SELECT COUNT(*) FROM health_check',
            'check_interval_seconds': 600
        }
    else:
        click.echo(click.style(f"Unknown monitor type: {monitor_type}. Supported types: url, database", fg='red'), err=True)
        return

    click.echo(f"# Sample YAML for updating a {monitor_type} monitor")
    click.echo("# Save this to a file and use: webmonitor monitor update-from-file <monitor_id> -f <file>")
    click.echo("# ID in the command takes precedence over ID in the file")
    click.echo("# space_id is required and must reference an existing space")
    click.echo()
    click.echo(yaml.dump(sample, default_flow_style=False))

# Define the monitor command group
@click.group(help='Monitor management commands')
def monitor():
    pass

@monitor.command('list')
@click.option('--space-id', help='Filter monitors by space ID')
def list_monitors(space_id):
    command = {'action': 'list_monitors'}
    if space_id:
        command['space_id'] = space_id
    response = send_command(command)
    format_response(response)

@monitor.command('get')
@click.argument('monitor_id')
def get_monitor(monitor_id):
    response = send_command({'action': 'get_monitor', 'monitor_id': monitor_id})
    format_response(response)

@monitor.command('start', help='Start a monitor')
@click.argument('monitor_id')
def start_monitor(monitor_id):
    response = send_command({'action': 'start_monitor', 'monitor_id': monitor_id})
    format_response(response)

@monitor.command('stop', help='Stop a monitor')
@click.argument('monitor_id')
def stop_monitor(monitor_id):
    response = send_command({'action': 'stop_monitor', 'monitor_id': monitor_id})
    format_response(response)

@monitor.command('delete', help='Delete a monitor')
@click.argument('monitor_id')
@click.confirmation_option(prompt='Are you sure you want to delete this monitor?')
def delete_monitor(monitor_id):
    response = send_command({'action': 'delete_monitor', 'monitor_id': monitor_id})
    format_response(response)

@monitor.command('create-from-file', help='Create a monitor from a YAML file')
@click.option('--file', '-f', type=click.Path(exists=True), required=True, help='YAML file containing monitor definition')
def create_monitor_from_file_command(file):
    response = create_monitor_from_file(send_command, file)
    format_response(response)

@monitor.command('update-from-file', help='Update a monitor from a YAML file')
@click.option('--file', '-f', type=click.Path(exists=True), required=True, help='YAML file containing monitor definition')
def update_monitor_from_file_command(file):
    response = update_monitor_from_file(send_command, file)
    format_response(response)

@monitor.command('export')
@click.argument('monitor_id')
@click.option('--output', '-o', type=click.Path(), help='Output file (defaults to stdout)')
def export_monitor_command(monitor_id, output):
    response = export_monitor(send_command, monitor_id, output)
    if response.get('status') != 'success':
        format_response(response)

@monitor.command('sample-create')
@click.option('--type', 'monitor_type', type=click.Choice(['url', 'database']), default='url', help='Type of monitor to show sample for')
def monitor_sample_create(monitor_type):
    print_sample_monitor_create(monitor_type)

@monitor.command('sample-update')
@click.option('--type', 'monitor_type', type=click.Choice(['url', 'database']), default='url', help='Type of monitor to show sample for')
def monitor_sample_update(monitor_type):
    print_sample_monitor_update(monitor_type)
