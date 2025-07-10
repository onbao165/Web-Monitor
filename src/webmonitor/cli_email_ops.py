import click
import getpass
import sys
from datetime import datetime
from typing import Dict, Any
from .config import get_config_manager
from .services.email_service import EmailService
from .cli_utils import send_command

# Define the email command group
@click.group(help='Email configuration and management commands')
def email():
    pass

@email.command('configure')
def email_configure():
    # Configure email settings interactively
    click.echo(click.style("Email Configuration Setup", fg='blue', bold=True))
    click.echo("=" * 30)

    config_manager = get_config_manager()

    # Get current config for defaults
    current_email_config = config_manager.get_email_config() or {}

    # Collect configuration
    email_config = {}

    # SMTP Host
    default_host = current_email_config.get('smtp_host', 'smtp.gmail.com')
    email_config['smtp_host'] = click.prompt(
        f"SMTP Host",
        default=default_host,
        show_default=True
    )

    # SMTP Port
    default_port = current_email_config.get('smtp_port', 587)
    email_config['smtp_port'] = click.prompt(
        f"SMTP Port",
        default=default_port,
        type=int,
        show_default=True
    )

    # Username
    default_username = current_email_config.get('username', '')
    email_config['username'] = click.prompt(
        f"Email Username",
        default=default_username if default_username else None
    )

    # Password
    email_config['password'] = getpass.getpass("Email Password: ")
    if not email_config['password']:
        click.echo(click.style("Password cannot be empty", fg='red'), err=True)
        sys.exit(1)

    # From Name
    default_from_name = current_email_config.get('from_name', 'Web Monitor')
    email_config['from_name'] = click.prompt(
        f"From Name",
        default=default_from_name,
        show_default=True
    )

    # Validate configuration
    is_valid, message = _validate_email_config(email_config)
    if not is_valid:
        click.echo(click.style(f"Configuration error: {message}", fg='red'), err=True)
        sys.exit(1)

    # Test connection
    click.echo("\nTesting SMTP connection...")
    email_service = EmailService(
        smtp_host=email_config['smtp_host'],
        smtp_port=email_config['smtp_port'],
        username=email_config['username'],
        password=email_config['password'],
        from_name=email_config['from_name']
    )

    success, test_message = email_service.test_connection()
    if not success:
        click.echo(click.style(f"Connection test failed: {test_message}", fg='red'), err=True)
        if not click.confirm("Save configuration anyway?"):
            sys.exit(1)
    else:
        click.echo(click.style("✓ Connection test successful!", fg='green'))

    # Save configuration
    current_config = config_manager.get_config() or {}
    current_config['email'] = email_config

    if config_manager.save_config(current_config):
        click.echo(click.style("✓ Email configuration saved successfully!", fg='green'))

        # Reload email service
        from .services.email_service import reload_email_service
        if reload_email_service():
            click.echo(click.style("✓ Email service reloaded", fg='green'))
    else:
        click.echo(click.style("Failed to save email configuration", fg='red'), err=True)
        sys.exit(1)

@email.command('status')
def email_status():
    config_manager = get_config_manager()
    email_config = config_manager.get_email_config()

    if not email_config or not config_manager.is_email_configured():
        click.echo(click.style("Email is not configured", fg='yellow'))
        click.echo("Run 'webmonitor email configure' to set up email notifications")
        return

    # Get config without decrypted password for display
    config = config_manager.get_config()
    email_display_config = config.get('email', {}) if config else {}

    click.echo(click.style("Email Configuration Status", fg='blue', bold=True))
    click.echo("=" * 30)
    click.echo(f"SMTP Host: {email_config.get('smtp_host', 'Not set')}")
    click.echo(f"SMTP Port: {email_config.get('smtp_port', 'Not set')}")
    click.echo(f"Username: {email_config.get('username', 'Not set')}")
    click.echo(f"From Name: {email_config.get('from_name', 'Web Monitor')}")
    click.echo(f"Password: {'✓ Configured' if email_display_config.get('encrypted_password') else '✗ Not set'}")
    click.echo(f"Configured: {config.get('configured_at', 'Unknown') if config else 'Unknown'}")
    click.echo(f"Last Updated: {config.get('last_updated', 'Unknown') if config else 'Unknown'}")

@email.command('test', help='Send a test email to verify configuration')
@click.argument('recipient')
def email_test(recipient):
    # Send a test email to verify configuration
    config_manager = get_config_manager()

    if not config_manager.is_email_configured():
        click.echo(click.style("Email is not configured. Run 'webmonitor email configure' first.", fg='red'), err=True)
        sys.exit(1)

    from .services.email_service import get_email_service
    email_service = get_email_service()

    # Reload configuration to ensure we have the latest
    email_service.load_from_config()

    subject = "Web Monitor Test Email"
    body = """
    <h2>Web Monitor Test Email</h2>
    <p>This is a test email from your Web Monitor system.</p>
    <p>If you received this email, your email configuration is working correctly!</p>
    <p><strong>Timestamp:</strong> {timestamp}</p>
    """.format(timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    click.echo(f"Sending test email to {recipient}...")

    success = email_service.send_email([recipient], subject, body, is_html=True)

    if success:
        click.echo(click.style("✓ Test email sent successfully!", fg='green'))
    else:
        click.echo(click.style("✗ Failed to send test email", fg='red'), err=True)
        sys.exit(1)

@email.command('update')
@click.option('--smtp-host', help='Update SMTP host')
@click.option('--smtp-port', type=int, help='Update SMTP port')
@click.option('--username', help='Update email username')
@click.option('--from-name', help='Update from name')
@click.option('--password', is_flag=True, help='Update password (will prompt)')
def email_update(smtp_host, smtp_port, username, from_name, password):
    if not any([smtp_host, smtp_port, username, from_name, password]):
        click.echo("Please specify at least one setting to update")
        return

    config_manager = get_config_manager()
    current_email_config = config_manager.get_email_config()

    if not current_email_config:
        click.echo(click.style("Email is not configured. Run 'webmonitor email configure' first.", fg='red'), err=True)
        sys.exit(1)

    # Update the specific settings
    if smtp_host:
        current_email_config['smtp_host'] = smtp_host
        click.echo(click.style(f"✓ Updated SMTP host to: {smtp_host}", fg='green'))
    if smtp_port:
        current_email_config['smtp_port'] = smtp_port
        click.echo(click.style(f"✓ Updated SMTP port to: {smtp_port}", fg='green'))
    if username:
        current_email_config['username'] = username
        click.echo(click.style(f"✓ Updated username to: {username}", fg='green'))
    if from_name:
        current_email_config['from_name'] = from_name
        click.echo(click.style(f"✓ Updated from name to: {from_name}", fg='green'))
    if password:
        current_email_config['password'] = getpass.getpass("New Password: ")
        click.echo(click.style("✓ Updated password", fg='green'))

    # Validate updated configuration
    is_valid, message = _validate_email_config(current_email_config)
    if not is_valid:
        click.echo(click.style(f"Configuration error: {message}", fg='red'), err=True)
        sys.exit(1)

    # Save updated configuration
    current_config = config_manager.get_config() or {}
    current_config['email'] = current_email_config

    if config_manager.save_config(current_config):
        click.echo(click.style("✓ Email configuration updated successfully!", fg='green'))

        # Reload email service
        from .services.email_service import reload_email_service
        if reload_email_service():
            click.echo(click.style("✓ Email service reloaded", fg='green'))
    else:
        click.echo(click.style("Failed to update email configuration", fg='red'), err=True)
        sys.exit(1)

@email.command('reload', help='Reload email configuration in the running daemon')
def email_reload():
    response = send_command({'action': 'reload_email_config'})

    if response.get('status') == 'success':
        click.echo(click.style("✓ Email configuration reloaded in daemon", fg='green'))
    else:
        click.echo(click.style(f"Failed to reload email config: {response.get('message', 'Unknown error')}", fg='red'), err=True)

def _validate_email_config(config: Dict[str, Any]) -> tuple[bool, str]:
    """Validate email configuration."""
    required_fields = ['smtp_host', 'smtp_port', 'username', 'password']

    for field in required_fields:
        if field not in config or not config[field]:
            return False, f"Missing required field: {field}"

    # Validate port is a number
    try:
        port = int(config['smtp_port'])
        if port < 1 or port > 65535:
            return False, "SMTP port must be between 1 and 65535"
    except (ValueError, TypeError):
        return False, "SMTP port must be a valid number"

    # Validate email format (basic check)
    username = config['username']
    if '@' not in username or '.' not in username:
        return False, "Username should be a valid email address"

    return True, "Configuration is valid"
