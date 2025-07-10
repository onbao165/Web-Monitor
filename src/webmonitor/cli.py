import click

# Import command groups from ops files
from .cli_config_ops import config
from .cli_job_ops import jobs
from .cli_email_ops import email
from .cli_space_ops import space
from .cli_monitor_ops import monitor
from .cli_result_ops import result

# Import individual system commands
from .cli_system_ops import SYSTEM_COMMANDS

# Main CLI group
@click.group()
@click.version_option(version='0.1.0')
def cli():
    """Web Monitor CLI - Monitor your web services and databases"""
    pass

# Add command groups
cli.add_command(config)
cli.add_command(jobs)
cli.add_command(email)
cli.add_command(space)
cli.add_command(monitor)
cli.add_command(result)

# Add individual system commands
for command in SYSTEM_COMMANDS:
    cli.add_command(command)

def main():
    cli()

if __name__ == '__main__':
    main()
