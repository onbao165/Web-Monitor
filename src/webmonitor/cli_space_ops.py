import os
import sys
import yaml
import click
from .cli_utils import send_command, format_response, resolve_space_identifier

def load_yaml_file(file_path: str) -> dict:
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        click.echo(click.style(f"Error loading YAML file: {str(e)}", fg='red'), err=True)
        sys.exit(1)

def create_space_from_file(send_command, file: str) -> dict:
    space_data = load_yaml_file(file)
    return send_command({
        'action': 'create_space',
        'space': space_data
    })

def update_space_from_file(send_command, file: str) -> dict:
    space_data = load_yaml_file(file)

    return send_command({
        'action': 'update_space',
        'space': space_data
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

def print_sample_space_create() -> None:
    sample = {
        'name': 'My Web Space',
        'description': 'Space for monitoring web services',
        'notification_emails': [
            'admin@example.com',
            'alerts@example.com'
        ]
    }

    click.echo("# Sample YAML for creating a space")
    click.echo("# Save this to a file and use: webmonitor space create-from-file -f <file>")
    click.echo("# ID is optional - will be auto-generated if not provided")
    click.echo()
    click.echo(yaml.dump(sample, default_flow_style=False))

def print_sample_space_update() -> None:
    sample = {
        'id': 'space-uuid-here',
        'name': 'My Updated Web Space',
        'description': 'Updated space for monitoring web services',
        'notification_emails': [
            'admin@example.com',
            'alerts@example.com',
            'newuser@example.com'
        ]
    }

    click.echo("# Sample YAML for updating a space")
    click.echo("# Save this to a file and use: webmonitor space update-from-file <space_id> -f <file>")
    click.echo("# ID in the command takes precedence over ID in the file")
    click.echo()
    click.echo(yaml.dump(sample, default_flow_style=False))

# Define the space command group
@click.group(help='Space management commands')
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

@space.command('start', help='Start all monitors in a space (accepts ID or name)')
@click.argument('space_identifier')
def start_space(space_identifier):
    _, command_params = resolve_space_identifier(space_identifier)
    command_params['action'] = 'start_space'
    response = send_command(command_params)
    format_response(response)

@space.command('stop', help='Stop all monitors in a space (accepts ID or name)')
@click.argument('space_identifier')
def stop_space(space_identifier):
    _, command_params = resolve_space_identifier(space_identifier)
    command_params['action'] = 'stop_space'
    response = send_command(command_params)
    format_response(response)

@space.command('delete', help='Delete a space and all its monitors')
@click.argument('space_id')
@click.confirmation_option(prompt='Are you sure you want to delete this space and all its monitors?')
def delete_space(space_id):
    response = send_command({'action': 'delete_space', 'space_id': space_id})
    format_response(response)

@space.command('create-from-file', help='Create a space from a YAML file')
@click.option('--file', '-f', type=click.Path(exists=True), required=True, help='YAML file containing space definition')
def create_space_from_file_command(file):
    response = create_space_from_file(send_command, file)
    format_response(response)

@space.command('update-from-file', help='Update a space from a YAML file')
@click.option('--file', '-f', type=click.Path(exists=True), required=True, help='YAML file containing space definition')
def update_space_from_file_command(file):
    response = update_space_from_file(send_command, file)
    format_response(response)

@space.command('export')
@click.argument('space_id')
@click.option('--output', '-o', type=click.Path(), help='Output file (defaults to stdout)')
def export_space_command(space_id, output):
    response = export_space(send_command, space_id, output)
    if response.get('status') != 'success':
        format_response(response)

@space.command('sample-create')
def space_sample_create():
    print_sample_space_create()

@space.command('sample-update')
def space_sample_update():
    print_sample_space_update()
