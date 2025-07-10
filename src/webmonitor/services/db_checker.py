import time
import logging
from datetime import datetime
from typing import Dict, Any, List
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from webmonitor.models import DatabaseMonitor, MonitorResult, MonitorStatus
from webmonitor.utils import errors

"""
Workflow:
1. Start a timer
2. Connect to the database
3. Check the connection
4. Stop the timer
5. Calculate the response time
6. Create a MonitorResult
7. Return the MonitorResult
"""

def check_db(monitor: DatabaseMonitor) -> MonitorResult:
    start_time = time.time()
    details: Dict[str, Any] = {}
    status = MonitorStatus.HEALTHY
    failed_checks = 0
    # Define checks
    check_list = ['connection', 'query']
    
    try:
        logger = logging.getLogger(__name__)
        # Connect to database
        engine = create_engine(
            monitor.test_connection_string(), 
            pool_pre_ping=True,
            connect_args={"connect_timeout": monitor.connection_timeout_seconds}
        )

        # Test connection
        with engine.connect() as connection:
            details['connection'] = {
                'connected': True
            }
            
            # Run test query if provided
            if monitor.test_query and monitor.test_query.strip():
                try:
                    # Set query timeout
                    if monitor.db_type.lower() == 'postgresql':
                        connection.execute(text(f"SET statement_timeout = {monitor.query_timeout_seconds * 1000}"))
                    elif monitor.db_type.lower() == 'mysql':
                        connection.execute(text(f"SET max_execution_time = {monitor.query_timeout_seconds * 1000}"))
                    elif monitor.db_type.lower() == 'sqlserver':
                        # For SQL Server, set lock timeout (in milliseconds)
                        connection.execute(text(f"SET LOCK_TIMEOUT {monitor.query_timeout_seconds * 1000}"))
                    
                    # Execute the test query
                    result = connection.execute(text(monitor.test_query))
                    row_count = result.rowcount
                    details['query'] = {
                        'executed': True,
                        'message': f"Query '{monitor.test_query}' executed successfully. Rows affected: {row_count}"
                    }
                except SQLAlchemyError as e:
                    logger.error(f"Error executing query: {str(e)}", exc_info=True)
                    failed_checks += 1
                    status = MonitorStatus.UNHEALTHY
                    details['query'] = {
                        'executed': False,
                        'message': errors.QUERY_EXECUTION_ERROR
                    }
    except Exception as e:
        logger.error(f"Error checking database: {str(e)}", exc_info=True)
        status = MonitorStatus.UNHEALTHY
        failed_checks += 2
        details['connection'] = {
            'connected': False,
            'message': errors.CONNECTION_ERROR,
        }
        details['query'] = {
            'executed': False,
            'message': errors.QUERY_CONNECTION_ERROR
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
