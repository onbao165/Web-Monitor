import json
import click
import sys
from typing import Dict, Any, Optional
from webmonitor.config import get_config_manager
from .cli_utils import success_message, error_message, warning_message

# Define the config command group
@click.group(help='Configuration management commands')
def config():
    pass

@config.command('show', help='Display current configuration')
def config_show():
    # Display current configuration
    try:
        config_manager = get_config_manager()
        config = config_manager.get_config()

        if not config:
            click.echo(click.style("No configuration found", fg='red'), err=True)
            return

        click.echo(click.style("Current Configuration", fg='blue', bold=True))
        click.echo("=" * 50)

        # Display email config (without password)
        email_config = config.get('email', {})
        click.echo(click.style("\n📧 Email Configuration:", fg='cyan', bold=True))
        click.echo(f"  SMTP Host: {email_config.get('smtp_host', 'Not set')}")
        click.echo(f"  SMTP Port: {email_config.get('smtp_port', 'Not set')}")
        click.echo(f"  Username: {email_config.get('username', 'Not set')}")
        click.echo(f"  From Name: {email_config.get('from_name', 'Not set')}")
        click.echo(f"  Password: {'***' if email_config.get('encrypted_password') else 'Not set'}")

        # Display health alerts config
        health_config = config.get('health_alerts', {})
        click.echo(click.style("\n🚨 Health Alerts Configuration:", fg='cyan', bold=True))
        click.echo(f"  Enabled: {health_config.get('enabled', 'Not set')}")
        click.echo(f"  Check Interval: {health_config.get('check_interval_minutes', 'Not set')} minutes")
        click.echo(f"  Unhealthy Threshold: {health_config.get('unhealthy_threshold_hours', 'Not set')} hours")

        # Display data cleanup config
        cleanup_config = config.get('data_cleanup', {})
        click.echo(click.style("\n🧹 Data Cleanup Configuration:", fg='cyan', bold=True))
        click.echo(f"  Enabled: {cleanup_config.get('enabled', 'Not set')}")
        click.echo(f"  Cleanup Interval: {cleanup_config.get('cleanup_interval_hours', 'Not set')} hours")
        click.echo(f"  Keep Healthy Results: {cleanup_config.get('keep_healthy_results_days', 'Not set')} days")
        click.echo(f"  Keep Unhealthy Results: {cleanup_config.get('keep_unhealthy_results_days', 'Not set')} days")

        # Display security config
        security_config = config.get('security', {})
        click.echo(click.style("\n🔐 Security Configuration:", fg='cyan', bold=True))
        click.echo(f"  Encryption Key: {'***' if security_config.get('encryption_key') else 'Not set'}")

        # Display metadata
        click.echo(click.style("\n📅 Configuration Metadata:", fg='cyan', bold=True))
        click.echo(f"  Configured At: {config.get('configured_at', 'Unknown')}")
        click.echo(f"  Last Updated: {config.get('last_updated', 'Unknown')}")

    except Exception as e:
        click.echo(click.style(f"Error displaying configuration: {str(e)}", fg='red'), err=True)

@config.command('set', help='Set a configuration value')
@click.argument('key')
@click.argument('value')
def config_set(key, value):
    # Set a configuration value using dot notation (e.g., email.smtp_host)
    try:
        config_manager = get_config_manager()
        config = config_manager.get_config() or {}

        # Parse the key path
        keys = key.split('.')
        if len(keys) < 2:
            click.echo(click.style("Key must be in format 'section.key' (e.g., email.smtp_host)", fg='red'), err=True)
            return

        # Navigate to the correct section
        current = config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        # Convert value to appropriate type
        final_key = keys[-1]
        converted_value = _convert_value(value)

        # Set the value
        current[final_key] = converted_value

        # Save the configuration
        success = config_manager.save_config(config)

        if success:
            click.echo(click.style(f"✅ Configuration updated: {key} = {converted_value}", fg='green'))
        else:
            click.echo(click.style("❌ Failed to save configuration", fg='red'), err=True)

    except Exception as e:
        click.echo(click.style(f"Error setting configuration: {str(e)}", fg='red'), err=True)

@config.command('reload', help='Reload configuration from file')
def config_reload():
    try:
        config_manager = get_config_manager()
        config = config_manager.load_config()

        if config:
            click.echo(click.style("✅ Configuration reloaded successfully", fg='green'))
        else:
            click.echo(click.style("❌ Failed to reload configuration", fg='red'), err=True)

    except Exception as e:
        click.echo(click.style(f"Error reloading configuration: {str(e)}", fg='red'), err=True)

@config.command('validate', help='Validate current configuration')
def config_validate():
    try:
        config_manager = get_config_manager()

        click.echo(click.style("Configuration Validation", fg='blue', bold=True))
        click.echo("=" * 30)

        # Check email configuration
        is_email_configured = config_manager.is_email_configured()
        email_status = "✅ Valid" if is_email_configured else "❌ Invalid or incomplete"
        click.echo(f"📧 Email Configuration: {email_status}")

        # Check if config file exists and is readable
        config = config_manager.get_config()
        config_status = "✅ Valid" if config else "❌ Missing or invalid"
        click.echo(f"📄 Config File: {config_status}")

        # Check encryption key
        encryption_key = config_manager.get_encryption_key()
        encryption_status = "✅ Present" if encryption_key else "❌ Missing"
        click.echo(f"🔐 Encryption Key: {encryption_status}")

        # Overall status
        overall_valid = is_email_configured and config and encryption_key
        overall_status = "✅ Valid" if overall_valid else "❌ Issues found"
        click.echo(f"\n🎯 Overall Status: {overall_status}")

        if not overall_valid:
            click.echo(click.style("\n💡 Use 'webmonitor config show' to see current settings", fg='yellow'))

    except Exception as e:
        click.echo(click.style(f"Error validating configuration: {str(e)}", fg='red'), err=True)

@config.command('export', help='Export configuration to file')
@click.option('--output', '-o', help='Output file path')
def config_export(output):
    try:
        config_manager = get_config_manager()
        config = config_manager.get_config()

        if not config:
            click.echo(click.style("No configuration to export", fg='red'), err=True)
            return

        # Create a safe copy without sensitive data
        safe_config = _create_safe_config_copy(config)

        if output:
            with open(output, 'w') as f:
                json.dump(safe_config, f, indent=2)
            click.echo(click.style(f"✅ Configuration exported to {output}", fg='green'))
        else:
            click.echo(json.dumps(safe_config, indent=2))

    except Exception as e:
        click.echo(click.style(f"Error exporting configuration: {str(e)}", fg='red'), err=True)



def _convert_value(value: str) -> Any:
    # Try boolean
    if value.lower() in ('true', 'false'):
        return value.lower() == 'true'
    
    # Try integer
    try:
        return int(value)
    except ValueError:
        pass
    
    # Try float
    try:
        return float(value)
    except ValueError:
        pass
    
    # Return as string
    return value

def _create_safe_config_copy(config: Dict[str, Any]) -> Dict[str, Any]:
    safe_config = {}
    
    for section, values in config.items():
        if isinstance(values, dict):
            safe_section = {}
            for key, value in values.items():
                # Skip sensitive keys
                if key in ['encrypted_password', 'password', 'encryption_key']:
                    safe_section[key] = "***HIDDEN***"
                else:
                    safe_section[key] = value
            safe_config[section] = safe_section
        else:
            safe_config[section] = values
    
    return safe_config
