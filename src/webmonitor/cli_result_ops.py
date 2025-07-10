import click
from .cli_utils import send_command, format_response, resolve_monitor_identifier

# Define the result command group
@click.group(help='Result management commands')
def result():
    pass

@result.command('monitor', help='Get results for a monitor')
@click.argument('monitor_identifier')
@click.option('--space-id', help='Space ID to search for monitor by name (optional if monitor name is unique)')
@click.option('--space-name', help='Space name to search for monitor by name (optional if monitor name is unique)')
@click.option('--limit', type=int, default=10, help='Maximum number of results to return')
def get_monitor_results(monitor_identifier, space_id, space_name, limit):
    _, command_params = resolve_monitor_identifier(monitor_identifier, space_id, space_name)
    command_params['action'] = 'get_monitor_results'
    command_params['limit'] = limit
    response = send_command(command_params)
    format_response(response)

@result.command('space', help='Get results for all monitors in a space')
@click.argument('space_identifier')
@click.option('--limit', type=int, default=10, help='Maximum number of results to return')
def get_space_results(space_identifier, limit):
    _, command_params = resolve_space_identifier(space_identifier)
    command_params['action'] = 'get_space_results'
    command_params['limit'] = limit
    response = send_command(command_params)
    format_response(response)
