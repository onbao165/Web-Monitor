from typing import List, Dict, Any
from datetime import datetime
from .base_job import BaseJob
from webmonitor.infrastructure import Database
from webmonitor.models import BaseMonitor, Space
from webmonitor.config import get_config_manager
from webmonitor.services.email_service import send_notification_email

class HealthAlertJob(BaseJob):
    def __init__(self, database: Database):
        super().__init__("health_alert")
        self.database = database
        self.config_manager = get_config_manager()
    
    def execute(self) -> bool:
        try:
            # Get health alert configuration
            health_config = self.config_manager.get_health_alerts_config()
            
            if not health_config.get('enabled', True):
                self.logger.info("Health alerts are disabled")
                return True
            
            # Check if email is configured
            if not self.config_manager.is_email_configured():
                self.logger.warning("Email not configured, skipping health alerts")
                return True
            
            threshold_hours = health_config.get('unhealthy_threshold_hours', 24)
            
            # Get monitors that have been unhealthy for too long
            unhealthy_monitors = self.database.get_unhealthy_monitors(threshold_hours)
            
            if not unhealthy_monitors:
                self.logger.info("No monitors found that have been unhealthy for extended periods")
                return True
            
            # Group monitors by space for organized notifications
            monitors_by_space = self._group_monitors_by_space(unhealthy_monitors)
            
            # Send alerts for each space
            alerts_sent = 0
            for space_id, monitors in monitors_by_space.items():
                space = self.database.get_space(space_id)
                if space and space.notification_emails:
                    success = self._send_health_alert(space, monitors, threshold_hours)
                    if success:
                        alerts_sent += 1
                    else:
                        self.logger.error(f"Failed to send health alert for space: {space.name}")
            
            self.logger.info(f"Health alert job completed. Sent {alerts_sent} alerts for {len(unhealthy_monitors)} unhealthy monitors")
            return True
            
        except Exception as e:
            self.logger.error(f"Health alert job failed: {str(e)}", exc_info=True)
            return False
    
    def _group_monitors_by_space(self, monitors: List[BaseMonitor]) -> Dict[str, List[BaseMonitor]]:
        grouped = {}
        for monitor in monitors:
            if monitor.space_id not in grouped:
                grouped[monitor.space_id] = []
            grouped[monitor.space_id].append(monitor)
        return grouped
    
    def _send_health_alert(self, space: Space, monitors: List[BaseMonitor], threshold_hours: int) -> bool:
        try:
            subject = f"🚨 Health Alert: {len(monitors)} monitor(s) unhealthy in {space.name}"
            
            # Create email body
            body = self._create_alert_email_body(space, monitors, threshold_hours)
            
            # Send email
            success = send_notification_email(
                recipients=space.notification_emails,
                subject=subject,
                body=body,
                is_html=True
            )
            
            if success:
                self.logger.info(f"Health alert sent for space '{space.name}' with {len(monitors)} unhealthy monitors")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to send health alert for space {space.name}: {str(e)}")
            return False
    
    def _create_alert_email_body(self, space: Space, monitors: List[BaseMonitor], threshold_hours: int) -> str:
        now = datetime.now()
        
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .monitor {{ background-color: #f8f9fa; padding: 10px; margin: 10px 0; border-left: 4px solid #dc3545; }}
                .monitor-name {{ font-weight: bold; color: #dc3545; }}
                .monitor-details {{ margin-top: 5px; font-size: 0.9em; color: #6c757d; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; font-size: 0.8em; color: #6c757d; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🚨 Health Alert for Space: {space.name}</h2>
                <p>The following monitors have been unhealthy for more than {threshold_hours} hours:</p>
            </div>
        """
        
        for monitor in monitors:
            # Calculate how long it's been unhealthy
            if monitor.last_healthy_at:
                unhealthy_duration = now - monitor.last_healthy_at
                unhealthy_hours = int(unhealthy_duration.total_seconds() / 3600)
                last_healthy_text = f"{unhealthy_hours} hours ago ({monitor.last_healthy_at.strftime('%Y-%m-%d %H:%M:%S')})"
            else:
                last_healthy_text = "Never been healthy"
            
            last_checked_text = "Never checked"
            if monitor.last_checked_at:
                last_checked_text = monitor.last_checked_at.strftime('%Y-%m-%d %H:%M:%S')
            
            body += f"""
            <div class="monitor">
                <div class="monitor-name">{monitor.name}</div>
                <div class="monitor-details">
                    <strong>Type:</strong> {monitor.monitor_type.value}<br>
                    <strong>Status:</strong> {monitor.status.value}<br>
                    <strong>Last Healthy:</strong> {last_healthy_text}<br>
                    <strong>Last Checked:</strong> {last_checked_text}
                </div>
            </div>
            """
        
        body += f"""
            <div class="footer">
                <p>This alert was generated at {now.strftime('%Y-%m-%d %H:%M:%S')} by Web Monitor.</p>
                <p>Please check your monitoring dashboard for more details and take appropriate action.</p>
            </div>
        </body>
        </html>
        """
        
        return body
