import os
import sys
import json
import socket
from typing import Dict, Any, Optional
import click

from .cli_yaml_ops import (
    create_config,
    update_config,
    create_space_from_file,
    update_space_from_file,
    create_monitor_from_file,
    update_monitor_from_file,
    export_space,
    export_monitor,
    export_all
)

from .cli_yaml_sample_ops import (
    print_sample_space_create,
    print_sample_space_update,
    print_sample_monitor_create,
    print_sample_monitor_update,
    print_sample_config_create,
    print_sample_config_update
)

from .cli_email_ops import (
    configure_email_interactive,
    show_email_status,
    test_email,
    update_email_setting,
    reload_email_config
)

# Config socket path
SOCKET_PATH = os.getenv('SOCKET_PATH', '/tmp/webmonitor.sock')

def send_command(command: Dict[str, Any]) -> Dict[str, Any]:
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(30)  # Add 30-second timeout
        sock.connect(SOCKET_PATH)
        
        # Send command
        sock.sendall(json.dumps(command).encode('utf-8'))
        
        # Receive response with timeout
        data = b''
        sock.settimeout(30)  # Set receive timeout
        while True:
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                data += chunk
            except socket.timeout:
                click.echo("Timeout waiting for daemon response", err=True)
                break
            
        sock.close()
        if not data:
            return {'status': 'error', 'message': 'No response from daemon (timeout)'}
        return json.loads(data.decode('utf-8'))
    except socket.timeout:
        click.echo("Timeout connecting to daemon", err=True)
        return {'status': 'error', 'message': 'Connection to daemon timed out'}
    except socket.error as e:
        click.echo(f"Error connecting to daemon: {e}", err=True)
        return {'status': 'error', 'message': f'Socket error: {str(e)}'}
    except json.JSONDecodeError:
        click.echo("Error decoding response from daemon", err=True)
        return {'status': 'error', 'message': 'Invalid response format'}

def _format_space_summary(space: Dict[str, Any]) -> None:
    click.echo(f"  ID: {space['id']}")
    click.echo(f"  Name: {space['name']}")
    click.echo(f"  Description: {space.get('description', 'N/A')}")
    click.echo("")

def _format_space_details(space: Dict[str, Any]) -> None:
    click.echo("\nSpace Details:")
    click.echo(f"  ID: {space['id']}")
    click.echo(f"  Name: {space['name']}")
    click.echo(f"  Description: {space.get('description', 'N/A')}")
    click.echo(f"  Created: {space.get('created_at', 'N/A')}")
    click.echo(f"  Updated: {space.get('updated_at', 'N/A')}")
    if 'notification_emails' in space and space['notification_emails']:
        click.echo(f"  Notification Emails: {', '.join(space['notification_emails'])}")

def _format_monitor_summary(monitor: Dict[str, Any]) -> None:
    click.echo(f"  ID: {monitor['id']}")
    click.echo(f"  Name: {monitor['name']}")
    click.echo(f"  Type: {monitor['monitor_type']}")
    click.echo(f"  Status: {monitor['status']}")
    click.echo(f"  Space ID: {monitor['space_id']}")
    click.echo(f"  Check Interval: {monitor.get('check_interval_seconds', 'N/A')} seconds")
    click.echo(f"  Last Checked: {monitor.get('last_checked_at', 'Never')}")
    click.echo(f"  Last Healthy: {monitor.get('last_healthy_at', 'Never')}")
    if 'running' in monitor:
        click.echo(f"  Running: {monitor['running']}")
    click.echo("")

def _format_monitor_details(monitor: Dict[str, Any]) -> None:
    click.echo("\nMonitor Details:")
    click.echo(f"  ID: {monitor['id']}")
    click.echo(f"  Name: {monitor['name']}")
    click.echo(f"  Type: {monitor['monitor_type']}")
    click.echo(f"  Status: {monitor['status']}")
    click.echo(f"  Space ID: {monitor['space_id']}")
    click.echo(f"  Check Interval: {monitor.get('check_interval_seconds', 'N/A')} seconds")
    click.echo(f"  Created: {monitor.get('created_at', 'N/A')}")
    click.echo(f"  Updated: {monitor.get('updated_at', 'N/A')}")
    click.echo(f"  Last Checked: {monitor.get('last_checked_at', 'Never')}")
    click.echo(f"  Last Healthy: {monitor.get('last_healthy_at', 'Never')}")

    # Type-specific details
    if monitor['monitor_type'] == 'url':
        click.echo(f"  URL: {monitor.get('url', 'N/A')}")
        click.echo(f"  Expected Status: {monitor.get('expected_status_code', 'N/A')}")
        click.echo(f"  Timeout: {monitor.get('timeout_seconds', 'N/A')} seconds")
        click.echo(f"  Check SSL: {monitor.get('check_ssl', 'N/A')}")
        click.echo(f"  Follow Redirects: {monitor.get('follow_redirects', 'N/A')}")
        if monitor.get('check_content'):
            click.echo(f"  Check Content: {monitor['check_content']}")
    elif monitor['monitor_type'] == 'database':
        click.echo(f"  Database Type: {monitor.get('db_type', 'N/A')}")
        click.echo(f"  Host: {monitor.get('host', 'N/A')}")
        click.echo(f"  Port: {monitor.get('port', 'N/A')}")
        click.echo(f"  Database: {monitor.get('database', 'N/A')}")
        click.echo(f"  Connection Timeout: {monitor.get('connection_timeout_seconds', 'N/A')} seconds")
        click.echo(f"  Query Timeout: {monitor.get('query_timeout_seconds', 'N/A')} seconds")
        click.echo(f"  Test Query: {monitor.get('test_query', 'N/A')}")

def _format_result(result: Dict[str, Any]) -> None:
    # Determine status based on available fields
    is_success = result.get('success', result.get('status') in ['healthy', 'HEALTHY'])
    status_color = 'green' if is_success else 'red'
    status_text = click.style("SUCCESS" if is_success else "FAILURE", fg=status_color)

    click.echo(f"  Time: {result['timestamp']}")
    click.echo(f"  Status: {status_text}")
    click.echo(f"  Response Time: {result.get('response_time_ms', 'N/A')} ms")

    # Show additional result details
    if 'failed_checks' in result:
        click.echo(f"  Failed Checks: {result['failed_checks']}")
    if 'check_list' in result and result['check_list']:
        click.echo(f"  Checks: {', '.join(result['check_list'])}")
    if 'details' in result and result['details']:
        click.echo(f"  Details: {result['details']}")
    click.echo("")

def _format_system_status(response: Dict[str, Any]) -> None:
    click.echo("\nSystem Status:")
    click.echo(f"  Running: {response['running']}")
    click.echo(f"  Total Monitors: {response.get('total_monitors', 0)}")
    if 'monitors' in response and response['monitors']:
        click.echo("\nRunning Monitors:")
        for monitor in response['monitors']:
            _format_monitor_summary(monitor)

def format_response(response: Dict[str, Any]) -> None:
    if response.get('status') == 'success':
        click.echo(click.style(f"SUCCESS: {response.get('message', '')}", fg='green'))

        # Handle specific data types
        if 'spaces' in response:
            if not response['spaces']:
                click.echo("No spaces found.")
            else:
                click.echo("\nSpaces:")
                for space in response['spaces']:
                    _format_space_summary(space)

        elif 'space' in response:
            _format_space_details(response['space'])

        elif 'monitors' in response:
            if not response['monitors']:
                click.echo("No monitors found.")
            else:
                click.echo("\nMonitors:")
                for monitor in response['monitors']:
                    _format_monitor_summary(monitor)

        elif 'monitor' in response:
            _format_monitor_details(response['monitor'])

        elif 'results' in response:
            if not response['results']:
                click.echo("No results found.")
            else:
                click.echo("\nResults:")
                for result in response['results']:
                    _format_result(result)

        elif 'running' in response:
            _format_system_status(response)
    else:
        click.echo(click.style(f"ERROR: {response.get('message', 'Unknown error')}", fg='red'), err=True)

@click.group()
@click.version_option(version='0.1.0')
def cli():
    pass

# Space commands
@cli.group(help='Space management commands')
def space():
    pass

@space.command('list')
def list_spaces():
    response = send_command({'action': 'list_spaces'})
    format_response(response)

@space.command('get')
@click.argument('space_id')
def get_space(space_id):
    response = send_command({'action': 'get_space', 'space_id': space_id})
    format_response(response)

@space.command('start', help='Start all monitors in a space')
@click.argument('space_id')
def start_space(space_id):
    response = send_command({'action': 'start_space', 'space_id': space_id})
    format_response(response)

@space.command('stop', help='Stop all monitors in a space')
@click.argument('space_id')
def stop_space(space_id):
    response = send_command({'action': 'stop_space', 'space_id': space_id})
    format_response(response)

@space.command('delete', help='Delete a space and all its monitors')
@click.argument('space_id')
@click.confirmation_option(prompt='Are you sure you want to delete this space and all its monitors?')
def delete_space(space_id):
    response = send_command({'action': 'delete_space', 'space_id': space_id})
    format_response(response)

# Monitor commands
@cli.group(help='Monitor management commands')
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


# Result commands
@cli.group(help='Result management commands')
def result():
    pass

@result.command('monitor', help='Get results for a monitor')
@click.argument('monitor_id')
@click.option('--limit', type=int, default=10, help='Maximum number of results to return')
def get_monitor_results(monitor_id, limit):
    response = send_command({
        'action': 'get_monitor_results', 
        'monitor_id': monitor_id,
        'limit': limit
    })
    format_response(response)

@result.command('space', help='Get results for all monitors in a space')
@click.argument('space_id')
@click.option('--limit', type=int, default=10, help='Maximum number of results to return')
def get_space_results(space_id, limit):
    response = send_command({
        'action': 'get_space_results', 
        'space_id': space_id,
        'limit': limit
    })
    format_response(response)


# Email commands
@cli.group(help='Email configuration and management commands')
def email():
    pass

@email.command('configure')
def email_configure():
    configure_email_interactive()

@email.command('status')
def email_status():
    show_email_status()

@email.command('test', help='Send a test email to verify configuration')
@click.argument('recipient')
def email_test(recipient):
    test_email(recipient)

@email.command('update')
@click.option('--smtp-host', help='Update SMTP host')
@click.option('--smtp-port', type=int, help='Update SMTP port')
@click.option('--username', help='Update email username')
@click.option('--from-name', help='Update from name')
@click.option('--password', is_flag=True, help='Update password (will prompt)')
def email_update(smtp_host, smtp_port, username, from_name, password):
    """Update specific email settings."""
    if not any([smtp_host, smtp_port, username, from_name, password]):
        click.echo("Please specify at least one setting to update")
        return

    if smtp_host:
        update_email_setting('smtp_host', smtp_host)
    if smtp_port:
        update_email_setting('smtp_port', str(smtp_port))
    if username:
        update_email_setting('username', username)
    if from_name:
        update_email_setting('from_name', from_name)
    if password:
        update_email_setting('password', '')

@email.command('reload', help='Reload email configuration in the running daemon')
def email_reload():
    reload_email_config(send_command)



# System commands
@cli.command('status')
def status():
    """Show system status and running monitors."""
    response = send_command({'action': 'status'})
    format_response(response)

# Configuration commands
@cli.command('create', help='Create spaces and monitors from a YAML file')
@click.argument('yaml_file', type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True))
@click.option('--dry-run', is_flag=True, help='Show what would be created without making changes')
def create_config_command(yaml_file, dry_run):
    create_config(send_command, yaml_file, dry_run)

@cli.command('update', help='Update spaces and monitors from a YAML file')
@click.argument('yaml_file', type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True))
@click.option('--dry-run', is_flag=True, help='Show what would be updated without making changes')
def update_config_command(yaml_file, dry_run):
    update_config(send_command, yaml_file, dry_run)



# Space file operations
@space.command('create-from-file', help='Create a space from a YAML file')
@click.option('--file', '-f', type=click.Path(exists=True), required=True, help='YAML file containing space definition')
def create_space_from_file_command(file):
    response = create_space_from_file(send_command, file)
    format_response(response)

@space.command('update-from-file', help='Update a space from a YAML file')
@click.option('--file', '-f', type=click.Path(exists=True), required=True, help='YAML file containing space definition')
def update_space_from_file_command(space_id, file):
    response = update_space_from_file(send_command, file)
    format_response(response)

# Monitor file operations
@monitor.command('create-from-file', help='Create a monitor from a YAML file')
@click.option('--file', '-f', type=click.Path(exists=True), required=True, help='YAML file containing monitor definition')
def create_monitor_from_file_command(file):
    response = create_monitor_from_file(send_command, file)
    format_response(response)

@monitor.command('update-from-file', help='Update a monitor from a YAML file')
@click.option('--file', '-f', type=click.Path(exists=True), required=True, help='YAML file containing monitor definition')
def update_monitor_from_file_command(monitor_id, file):
    response = update_monitor_from_file(send_command, file)
    format_response(response)

# Export operations
@space.command('export')
@click.argument('space_id')
@click.option('--output', '-o', type=click.Path(), help='Output file (defaults to stdout)')
def export_space_command(space_id, output):
    response = export_space(send_command, space_id, output)
    if response.get('status') != 'success':
        format_response(response)

@cli.command('export-all', help='Export all spaces and monitors to a YAML file')
@click.option('--output', '-o', type=click.Path(), required=True, help='Output file')
def export_all_command(output):
    response = export_all(send_command, output)
    if response.get('status') != 'success':
        format_response(response)

# Space samples
@space.command('sample-create')
def space_sample_create():
    print_sample_space_create()

@space.command('sample-update')
def space_sample_update():
    print_sample_space_update()

# Monitor samples
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

# Configuration samples
@cli.command('sample-create')
def sample_create():
    print_sample_config_create()

@cli.command('sample-update')
def sample_update():
    print_sample_config_update()

def main():
    cli()

if __name__ == '__main__':
    main()
