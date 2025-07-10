import click
import json
import socket
import sys
from typing import Dict, Any, List

# Import shared utilities
from .cli_utils import send_command, success_message, error_message, warning_message

# Define the jobs command group
@click.group(help='System job management commands')
def jobs():
    pass

@jobs.command('status', help='Show status of all system jobs')
def jobs_status():
    try:
        response = send_command({'action': 'get_job_status'})

        if response.get('status') != 'success':
            click.echo(click.style(f"Error: {response.get('message', 'Unknown error')}", fg='red'), err=True)
            return

        jobs = response.get('jobs', [])

        if not jobs:
            click.echo(click.style("No system jobs found", fg='yellow'))
            return

        click.echo(click.style("System Jobs Status", fg='blue', bold=True))
        click.echo("=" * 60)

        for job in jobs:
            name = job.get('name', 'Unknown')
            enabled = job.get('enabled', False)
            run_count = job.get('run_count', 0)
            error_count = job.get('error_count', 0)
            success_rate = job.get('success_rate', 0) * 100
            last_run = job.get('last_run', 'Never')

            # Format status
            status_icon = "🟢" if enabled else "🔴"
            status_text = "Enabled" if enabled else "Disabled"

            click.echo(f"\n{status_icon} {click.style(name.upper(), fg='cyan', bold=True)} ({status_text})")
            click.echo(f"   Runs: {run_count} | Errors: {error_count} | Success Rate: {success_rate:.1f}%")
            click.echo(f"   Last Run: {last_run}")

        click.echo()

    except Exception as e:
        click.echo(click.style(f"Error getting job status: {str(e)}", fg='red'), err=True)

@jobs.command('run', help='Run a system job manually')
@click.argument('job_name')
def jobs_run(job_name):
    # Run a system job manually (e.g., health-alerts, data-cleanup)
    try:
        click.echo(f"🔧 Running job: {job_name}")

        response = send_command({
            'action': 'run_job_manually',
            'job_name': job_name
        })

        if response.get('status') == 'success':
            click.echo(click.style(f"✅ Job '{job_name}' completed successfully", fg='green'))

            # Show any additional details
            if 'details' in response:
                click.echo(f"Details: {response['details']}")
        else:
            error_msg = response.get('message', 'Unknown error')
            click.echo(click.style(f"❌ Job '{job_name}' failed: {error_msg}", fg='red'), err=True)

    except Exception as e:
        click.echo(click.style(f"Error running job: {str(e)}", fg='red'), err=True)

@jobs.command('enable', help='Enable a system job')
@click.argument('job_name')
def jobs_enable(job_name):
    try:
        response = send_command({
            'action': 'enable_job',
            'job_name': job_name
        })

        if response.get('status') == 'success':
            click.echo(click.style(f"✅ Job '{job_name}' enabled", fg='green'))
        else:
            error_msg = response.get('message', 'Unknown error')
            click.echo(click.style(f"❌ Failed to enable job '{job_name}': {error_msg}", fg='red'), err=True)

    except Exception as e:
        click.echo(click.style(f"Error enabling job: {str(e)}", fg='red'), err=True)

@jobs.command('disable', help='Disable a system job')
@click.argument('job_name')
def jobs_disable(job_name):
    try:
        response = send_command({
            'action': 'disable_job',
            'job_name': job_name
        })

        if response.get('status') == 'success':
            click.echo(click.style(f"✅ Job '{job_name}' disabled", fg='green'))
        else:
            error_msg = response.get('message', 'Unknown error')
            click.echo(click.style(f"❌ Failed to disable job '{job_name}': {error_msg}", fg='red'), err=True)

    except Exception as e:
        click.echo(click.style(f"Error disabling job: {str(e)}", fg='red'), err=True)

@jobs.command('preview', help='Preview data cleanup without executing')
def jobs_preview():
    try:
        click.echo("🔍 Getting data cleanup preview...")

        response = send_command({'action': 'get_cleanup_preview'})

        if response.get('status') != 'success':
            click.echo(click.style(f"Error: {response.get('message', 'Unknown error')}", fg='red'), err=True)
            return

        preview = response.get('preview', {})

        click.echo(click.style("\nData Cleanup Preview", fg='blue', bold=True))
        click.echo("=" * 40)

        total_results = preview.get('total_results', 0)
        healthy_to_delete = preview.get('healthy_to_delete', 0)
        unhealthy_to_delete = preview.get('unhealthy_to_delete', 0)
        total_to_delete = preview.get('total_to_delete', 0)
        retention_after = preview.get('retention_after_cleanup', 0)

        click.echo(f"📊 Current Database:")
        click.echo(f"   Total Results: {total_results:,}")
        click.echo(f"")
        click.echo(f"🗑️  Would Delete:")
        click.echo(f"   Healthy Results: {healthy_to_delete:,}")
        click.echo(f"   Unhealthy Results: {unhealthy_to_delete:,}")
        click.echo(f"   Total to Delete: {total_to_delete:,}")
        click.echo(f"")
        click.echo(f"💾 After Cleanup:")
        click.echo(f"   Results Remaining: {retention_after:,}")

        if total_results > 0:
            deletion_percentage = (total_to_delete / total_results) * 100
            click.echo(f"   Deletion Percentage: {deletion_percentage:.1f}%")

        # Show cutoff dates
        healthy_cutoff = preview.get('healthy_cutoff_date')
        unhealthy_cutoff = preview.get('unhealthy_cutoff_date')

        if healthy_cutoff or unhealthy_cutoff:
            click.echo(f"")
            click.echo(f"📅 Cutoff Dates:")
            if healthy_cutoff:
                click.echo(f"   Healthy Results Before: {healthy_cutoff}")
            if unhealthy_cutoff:
                click.echo(f"   Unhealthy Results Before: {unhealthy_cutoff}")

        # Warning if large deletion
        if total_results > 0 and deletion_percentage > 50:
            click.echo(click.style(f"\n⚠️  Warning: This would delete {deletion_percentage:.1f}% of all data!", fg='yellow'))

    except Exception as e:
        click.echo(click.style(f"Error getting cleanup preview: {str(e)}", fg='red'), err=True)

@jobs.command('schedule', help='Show job schedules')
def jobs_schedule():
    try:
        response = send_command({'action': 'get_job_schedule'})

        if response.get('status') != 'success':
            click.echo(click.style(f"Error: {response.get('message', 'Unknown error')}", fg='red'), err=True)
            return

        schedules = response.get('schedules', {})

        if not schedules:
            click.echo(click.style("No job schedules found", fg='yellow'))
            return

        click.echo(click.style("Job Schedules", fg='blue', bold=True))
        click.echo("=" * 30)

        for job_name, schedule_info in schedules.items():
            enabled = schedule_info.get('enabled', False)
            interval = schedule_info.get('interval', 'Unknown')
            next_run = schedule_info.get('next_run', 'Unknown')

            status_icon = "🟢" if enabled else "🔴"
            click.echo(f"\n{status_icon} {click.style(job_name.upper(), fg='cyan', bold=True)}")
            click.echo(f"   Interval: {interval}")
            click.echo(f"   Next Run: {next_run}")

    except Exception as e:
        click.echo(click.style(f"Error getting job schedule: {str(e)}", fg='red'), err=True)
