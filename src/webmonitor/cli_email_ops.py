import click
import getpass
import sys
from typing import Dict, Any
from .services.email_config import get_email_config
from .services.email_service import EmailService

def configure_email_interactive() -> None:
    click.echo(click.style("Email Configuration Setup", fg='blue', bold=True))
    click.echo("=" * 30)
    
    email_config = get_email_config()
    
    # Get current config for defaults
    current_config = email_config.get_config_status()
    
    # Collect configuration
    config = {}
    
    # SMTP Host
    default_host = current_config.get('smtp_host', 'smtp.gmail.com')
    config['smtp_host'] = click.prompt(
        f"SMTP Host", 
        default=default_host,
        show_default=True
    )
    
    # SMTP Port
    default_port = current_config.get('smtp_port', 587)
    config['smtp_port'] = click.prompt(
        f"SMTP Port", 
        default=default_port,
        type=int,
        show_default=True
    )
    
    # Username
    default_username = current_config.get('username', '')
    config['username'] = click.prompt(
        f"Email Username", 
        default=default_username if default_username else None
    )
    
    # Password
    config['password'] = getpass.getpass("Email Password: ")
    if not config['password']:
        click.echo(click.style("Password cannot be empty", fg='red'), err=True)
        sys.exit(1)
    
    # From Name
    default_from_name = current_config.get('from_name', 'Web Monitor')
    config['from_name'] = click.prompt(
        f"From Name", 
        default=default_from_name,
        show_default=True
    )
    
    # Validate configuration
    is_valid, message = email_config.validate_config(config)
    if not is_valid:
        click.echo(click.style(f"Configuration error: {message}", fg='red'), err=True)
        sys.exit(1)
    
    # Test connection
    click.echo("\nTesting SMTP connection...")
    email_service = EmailService(
        smtp_host=config['smtp_host'],
        smtp_port=config['smtp_port'],
        username=config['username'],
        password=config['password'],
        from_name=config['from_name']
    )
    
    success, test_message = email_service.test_connection()
    if not success:
        click.echo(click.style(f"Connection test failed: {test_message}", fg='red'), err=True)
        if not click.confirm("Save configuration anyway?"):
            sys.exit(1)
    else:
        click.echo(click.style("✓ Connection test successful!", fg='green'))
    
    # Save configuration
    if email_config.save_config(config):
        click.echo(click.style("✓ Email configuration saved successfully!", fg='green'))
        
        # Reload email service
        from .services.email_service import reload_email_service
        if reload_email_service():
            click.echo(click.style("✓ Email service reloaded", fg='green'))
    else:
        click.echo(click.style("Failed to save email configuration", fg='red'), err=True)
        sys.exit(1)

def show_email_status() -> None:
    email_config = get_email_config()
    status = email_config.get_config_status()
    
    if not status['configured']:
        click.echo(click.style("Email is not configured", fg='yellow'))
        click.echo("Run 'webmonitor email configure' to set up email notifications")
        return
    
    click.echo(click.style("Email Configuration Status", fg='blue', bold=True))
    click.echo("=" * 30)
    click.echo(f"SMTP Host: {status['smtp_host']}")
    click.echo(f"SMTP Port: {status['smtp_port']}")
    click.echo(f"Username: {status['username']}")
    click.echo(f"From Name: {status['from_name']}")
    click.echo(f"Password: {'✓ Configured' if status['has_password'] else '✗ Not set'}")
    click.echo(f"Configured: {status['configured_at']}")
    click.echo(f"Last Updated: {status['last_updated']}")

def test_email(recipient: str) -> None:
    email_config = get_email_config()
    
    if not email_config.is_configured():
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
    """.format(timestamp=click.get_current_context().meta.get('timestamp', 'Unknown'))
    
    click.echo(f"Sending test email to {recipient}...")
    
    success = email_service.send_email([recipient], subject, body, is_html=True)
    
    if success:
        click.echo(click.style("✓ Test email sent successfully!", fg='green'))
    else:
        click.echo(click.style("✗ Failed to send test email", fg='red'), err=True)
        sys.exit(1)

def update_email_setting(setting: str, value: str) -> None:
    email_config = get_email_config()
    current_config = email_config.get_decrypted_config()
    
    if not current_config:
        click.echo(click.style("Email is not configured. Run 'webmonitor email configure' first.", fg='red'), err=True)
        sys.exit(1)
    
    # Update the specific setting
    if setting == 'password':
        current_config['password'] = getpass.getpass("New Password: ")
    else:
        current_config[setting] = value
    
    # Validate updated configuration
    is_valid, message = email_config.validate_config(current_config)
    if not is_valid:
        click.echo(click.style(f"Configuration error: {message}", fg='red'), err=True)
        sys.exit(1)
    
    # Save updated configuration
    if email_config.save_config(current_config):
        click.echo(click.style(f"✓ Updated {setting} successfully!", fg='green'))
        
        # Reload email service
        from .services.email_service import reload_email_service
        if reload_email_service():
            click.echo(click.style("✓ Email service reloaded", fg='green'))
    else:
        click.echo(click.style(f"Failed to update {setting}", fg='red'), err=True)
        sys.exit(1)

def reload_email_config(send_command) -> None:
    response = send_command({'action': 'reload_email_config'})
    
    if response.get('status') == 'success':
        click.echo(click.style("✓ Email configuration reloaded in daemon", fg='green'))
    else:
        click.echo(click.style(f"Failed to reload email config: {response.get('message', 'Unknown error')}", fg='red'), err=True)
