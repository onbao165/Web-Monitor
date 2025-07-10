"""
Error message constants for monitoring services
"""

# Base error messages
BASE_ERROR = "An unexpected error occurred during monitoring"

# Connection error messages
CONNECTION_ERROR = "Failed to establish connection"
TIMEOUT_ERROR = "Request timed out after {timeout} seconds"

# Response error messages
STATUS_CODE_ERROR = "Expected status code {expected}, got {actual}"
CONTENT_ERROR = "Required content not found in response"

# SSL error messages
SSL_ERROR = "SSL/TLS verification failed"

# Query error messages
QUERY_CONNECTION_ERROR = "Failed to execute query due to connection error"
QUERY_EXECUTION_ERROR = "Failed to execute query"