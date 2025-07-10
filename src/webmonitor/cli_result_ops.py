import click
from .cli_utils import send_command, format_response

# Define the result command group
@click.group(help='Result management commands')
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
