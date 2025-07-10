import json
import socket
import click
import os
import uuid
from typing import Dict, Any, Tuple

# Config socket path
SOCKET_PATH = os.getenv('SOCKET_PATH', '/var/run/webmonitor/webmonitor.sock')

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
        
        if data:
            return json.loads(data.decode('utf-8'))
        else:
            return {'status': 'error', 'message': 'No response from daemon'}
            
    except FileNotFoundError:
        return {'status': 'error', 'message': 'Daemon not running or socket not found'}
    except ConnectionRefusedError:
        return {'status': 'error', 'message': 'Connection refused. Is the daemon running?'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

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

def format_table_data(data: list, headers: list) -> None:
    if not data:
        click.echo("No data to display")
        return
    
    # Calculate column widths
    widths = [len(header) for header in headers]
    for row in data:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(str(cell)))
    
    # Print header
    header_row = " | ".join(header.ljust(widths[i]) for i, header in enumerate(headers))
    click.echo(click.style(header_row, fg='cyan', bold=True))
    click.echo("-" * len(header_row))
    
    # Print data rows
    for row in data:
        data_row = " | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row))
        click.echo(data_row)

def confirm_action(message: str, default: bool = False) -> bool:
    return click.confirm(message, default=default)

def success_message(message: str) -> None:
    click.echo(click.style(f"✅ {message}", fg='green'))

def error_message(message: str) -> None:
    click.echo(click.style(f"❌ {message}", fg='red'), err=True)

def warning_message(message: str) -> None:
    click.echo(click.style(f"⚠️  {message}", fg='yellow'))

def info_message(message: str) -> None:
    click.echo(click.style(f"ℹ️  {message}", fg='blue'))

def is_uuid(identifier: str) -> bool:
    try:
        uuid.UUID(identifier)
        return True
    except ValueError:
        return False

def resolve_space_identifier(identifier: str) -> Tuple[str, Dict[str, Any]]:
    """
    Resolve space identifier to command parameters.
    Returns action name and command dict.
    """
    if is_uuid(identifier):
        return 'space_id', {'space_id': identifier}
    else:
        return 'space_name', {'space_name': identifier}

def resolve_monitor_identifier(identifier: str, space_id: str = None, space_name: str = None) -> Tuple[str, Dict[str, Any]]:
    """
    Resolve monitor identifier to command parameters.
    Returns action name and command dict.
    """
    if is_uuid(identifier):
        return 'monitor_id', {'monitor_id': identifier}
    else:
        command = {'monitor_name': identifier}
        if space_id:
            command['space_id'] = space_id
        if space_name:
            command['space_name'] = space_name
        return 'monitor_name', command
