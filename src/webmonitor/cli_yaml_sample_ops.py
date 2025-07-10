import yaml
import click

def print_sample_space_create() -> None:
    """Print sample YAML for creating a space (ID is optional)."""
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
    """Print sample YAML for updating a space (ID is required)."""
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

def print_sample_monitor_create(monitor_type: str) -> None:
    """Print sample YAML for creating a monitor (ID is optional)."""
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
    """Print sample YAML for updating a monitor (ID is required)."""
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

def print_sample_config_create() -> None:
    """Print sample YAML for create config command (IDs are optional)."""
    sample = {
        'spaces': [
            {
                'name': 'Production Environment',
                'description': 'Monitoring for production services',
                'notification_emails': [
                    'ops-team@example.com',
                    'alerts@example.com'
                ],
                'id': 'production-space-id'
            },
            {
                'name': 'Development Environment',
                'description': 'Monitoring for development services',
                'notification_emails': [
                    'dev-team@example.com'
                ],
                'id': 'development-space-id'
            }
        ],
        'monitors': [
            {
                'name': 'Main Website',
                'space_id': 'production-space-id',
                'monitor_type': 'url',
                'url': 'https://www.example.com',
                'expected_status_code': 200,
                'timeout_seconds': 30,
                'check_ssl': True,
                'follow_redirects': True,
                'check_interval_seconds': 300
            },
            {
                'name': 'Production Database',
                'space_id': 'production-space-id',
                'monitor_type': 'database',
                'db_type': 'postgresql',
                'host': 'prod-db.example.com',
                'port': 5432,
                'database': 'app_production',
                'username': 'monitor_user',
                'password': 'secure_password',
                'connection_timeout_seconds': 10,
                'query_timeout_seconds': 30,
                'test_query': 'SELECT 1',
                'check_interval_seconds': 600
            }
        ]
    }

    click.echo("# Sample YAML for create config command")
    click.echo("# Save this to a file and use: webmonitor create <file>")
    click.echo("# IDs are optional - will be auto-generated if not provided")
    click.echo("# You can reference space IDs in monitors, or use the generated ones")
    click.echo()
    click.echo(yaml.dump(sample, default_flow_style=False))

def print_sample_config_update() -> None:
    """Print sample YAML for update config command (IDs are required)."""
    sample = {
        'spaces': [
            {
                'id': 'existing-production-space-id',
                'name': 'Updated Production Environment',
                'description': 'Updated monitoring for production services',
                'notification_emails': [
                    'ops-team@example.com',
                    'alerts@example.com',
                    'manager@example.com'
                ]
            },
            {
                'id': 'existing-dev-space-id',
                'name': 'Updated Development Environment',
                'description': 'Updated monitoring for development services',
                'notification_emails': [
                    'dev-team@example.com',
                    'qa-team@example.com'
                ]
            }
        ],
        'monitors': [
            {
                'id': 'existing-website-monitor-id',
                'name': 'Updated Main Website',
                'space_id': 'existing-production-space-id',
                'monitor_type': 'url',
                'url': 'https://www.updated-example.com',
                'expected_status_code': 200,
                'timeout_seconds': 45,
                'check_ssl': True,
                'follow_redirects': True,
                'check_content': 'Welcome to our updated site',
                'check_interval_seconds': 300
            },
            {
                'id': 'existing-database-monitor-id',
                'name': 'Updated Production Database',
                'space_id': 'existing-production-space-id',
                'monitor_type': 'database',
                'db_type': 'postgresql',
                'host': 'new-prod-db.example.com',
                'port': 5432,
                'database': 'app_production_v2',
                'username': 'updated_monitor_user',
                'password': 'new_secure_password',
                'connection_timeout_seconds': 15,
                'query_timeout_seconds': 45,
                'test_query': 'SELECT COUNT(*) FROM health_status',
                'check_interval_seconds': 600
            }
        ]
    }

    click.echo("# Sample YAML for update config command")
    click.echo("# Save this to a file and use: webmonitor update <file>")
    click.echo("# IDs are required for all resources when updating")
    click.echo("# All spaces and monitors must have existing IDs")
    click.echo()
    click.echo(yaml.dump(sample, default_flow_style=False))