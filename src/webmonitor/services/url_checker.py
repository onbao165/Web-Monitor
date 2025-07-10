import requests
import time
import ssl
import socket
from urllib.parse import urlparse
from datetime import datetime
from typing import Dict, Any
from webmonitor.models import UrlMonitor, MonitorResult, MonitorStatus
from webmonitor.utils import errors
from webmonitor.infrastructure import Database

"""
Workflow:
1. Start a timer
2. Send a request to the URL
3. Check the response
    a. Check status code
    b. Check content (if applicable)
    c. Check SSL (if applicable)
4. Stop the timer
5. Calculate the response time
6. Create a MonitorResult
7. Return the MonitorResult
"""

def check_url(monitor: UrlMonitor) -> MonitorResult:
    start_time = time.time()
    details: Dict[str, Any] = {}
    status = MonitorStatus.HEALTHY
    failed_checks = 0
    # Define checks
    check_list = ['connection', 'status_code']
    if monitor.check_content:
        check_list.append('content')
    if monitor.check_ssl:
        check_list.append('ssl')

    try:
        # Send request
        response = requests.get(
            monitor.url,
            timeout=monitor.timeout_seconds,
            verify=monitor.check_ssl,
            allow_redirects=monitor.follow_redirects
        )

        details['connection'] = {
            'connected': True
        }

        # Check status code
        if response.status_code != monitor.expected_status_code:
            status = MonitorStatus.UNHEALTHY
            failed_checks += 1
            details['status_code'] = {
                'expected': monitor.expected_status_code,
                'actual': response.status_code,
                'message': errors.STATUS_CODE_ERROR.format(expected=monitor.expected_status_code, actual=response.status_code)
            }
        else:
            details['status_code'] = {
                'expected': monitor.expected_status_code,
                'actual': response.status_code
            }
        # Check content
        if monitor.check_content and monitor.check_content not in response.text:
            status = MonitorStatus.UNHEALTHY
            failed_checks += 1
            details['content'] = {
                'expected': monitor.check_content,
                'found': False,
                'message': errors.CONTENT_ERROR
            }
        else:
            details['content'] = {
                'expected': monitor.check_content,
                'found': True
            }
        # Check SSL (Check SSL expiry)
        if monitor.check_ssl:
            ssl_details = get_ssl_expiry(monitor.url)
            if not ssl_details['has_ssl']:
                status = MonitorStatus.UNHEALTHY
                failed_checks += 1
                details['ssl'] = {
                    'message': errors.SSL_ERROR,
                    'error': ssl_details['error']
                }
            else:
                details['ssl'] = {
                    'expiry_date': ssl_details['expiry_date'],
                    'days_until_expiry': ssl_details['days_until_expiry'],
                    'issuer': ssl_details['issuer']
                }
    except requests.exceptions.Timeout:
        status = MonitorStatus.UNHEALTHY
        failed_checks += 1
        details['connection'] = {
            'connected': False,
            'message': errors.TIMEOUT_ERROR.format(timeout=monitor.timeout_seconds)
        }
    except requests.exceptions.ConnectionError:
        status = MonitorStatus.UNHEALTHY
        failed_checks += 1
        details['connection'] = {
            'connected': False,
            'message': errors.CONNECTION_ERROR
        }
    except Exception:
        status = MonitorStatus.UNHEALTHY
        failed_checks += 1
        details['connection'] = {
            'connected': False,
            'message': errors.BASE_ERROR
        }
    finally:
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        return MonitorResult(
            monitor_id=monitor.id,
            space_id=monitor.space_id,
            timestamp=datetime.now(),
            status=status,
            monitor_type=monitor.monitor_type,
            response_time_ms=response_time_ms,
            details=details,
            failed_checks=failed_checks,
            check_list=check_list
        )
        
def get_ssl_expiry(url: str) -> dict:
    try:
        # Extract domain from URL
        domain = urlparse(url).netloc
        if ':' in domain:  # Remove port if present
            domain = domain.split(':')[0]
        
        # Create SSL context
        context = ssl.create_default_context()
        
        # Connect to the server
        with socket.create_connection((domain, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                # Get certificate
                cert = ssock.getpeercert()
                
                # Extract expiry date
                expiry_date = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                
                # Calculate days until expiry
                days_until_expiry = (expiry_date - datetime.now()).days
                
                # Process issuer information safely
                issuer_info = {}
                if 'issuer' in cert:
                    # The issuer is a sequence of RDNs (Relative Distinguished Names)
                    # Each RDN is a sequence of name-value pairs
                    for rdn in cert['issuer']:
                        for name, value in rdn:
                            issuer_info[name] = value
                
                return {
                    'has_ssl': True,
                    'expiry_date': expiry_date.isoformat(),
                    'days_until_expiry': days_until_expiry,
                    'issuer': issuer_info
                }
    except Exception as e:
        return {
            'has_ssl': False,
            'error': str(e)
        }

