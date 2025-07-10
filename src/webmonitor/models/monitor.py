from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import uuid
from enum import Enum
from webmonitor.utils import encrypt_password, decrypt_password
import urllib.parse

class MonitorType(Enum):
    URL = 'url'
    DATABASE = 'database'

class MonitorStatus(Enum):
    HEALTHY = 'healthy'
    UNHEALTHY = 'unhealthy'
    UNKNOWN = 'unknown'
    OFFLINE = 'offline'

@dataclass
class BaseMonitor:
    # Base class for all monitors
    name: str
    space_id: str  # Space this monitor belongs to
    monitor_type: MonitorType
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: MonitorStatus = MonitorStatus.OFFLINE
    check_interval_seconds: int = 300  # 5 minutes
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_checked_at: Optional[datetime] = None
    last_healthy_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    def update_timestamp(self):
        self.updated_at = datetime.now()

    def update_last_checked_at(self):
        self.last_checked_at = datetime.now()
        self.update_timestamp()

    def update_last_healthy_at(self):
        self.last_healthy_at = datetime.now()
        self.update_timestamp()

    def to_dict(self)->dict:
        # Converts the monitor object to a dictionary
        return {
            'id': self.id,
            'name': self.name,
            'space_id': self.space_id,
            'monitor_type': self.monitor_type.value,
            'status': self.status.value,
            'check_interval_seconds': self.check_interval_seconds,
            'created_at': self.created_at.isoformat(), 
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_checked_at': self.last_checked_at.isoformat() if self.last_checked_at else None,
            'last_healthy_at': self.last_healthy_at.isoformat() if self.last_healthy_at else None
        }
    
    @classmethod
    def from_dict(cls, data: dict)->'BaseMonitor':
        # Converts a dictionary to a monitor object
        monitor = cls(
            id=data['id'],
            name=data['name'],
            space_id=data['space_id'],
            monitor_type=MonitorType(data['monitor_type']),
            status=MonitorStatus(data['status']),
            check_interval_seconds=data['check_interval_seconds'],
            created_at= datetime.fromisoformat(data['created_at']),
        )
        if (data.get('updated_at')):
            monitor.updated_at = datetime.fromisoformat(data['updated_at'])
        if (data.get('last_checked_at')):
            monitor.last_checked_at = datetime.fromisoformat(data['last_checked_at'])
        if (data.get('last_healthy_at')):
            monitor.last_healthy_at = datetime.fromisoformat(data['last_healthy_at'])
        return monitor

    # Add these methods to make BaseMonitor hashable
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, BaseMonitor):
            return False
        return self.id == other.id

@dataclass
class UrlMonitor(BaseMonitor):
    # Represents a URL monitor
    url: str = field(default="")
    expected_status_code: int = 200
    timeout_seconds: int = 30
    check_ssl: bool = True
    follow_redirects: bool = True
    check_content: Optional[str] = None # Check if this string is in the response body

    def __post_init__(self):
        super().__post_init__()
        self.monitor_type = MonitorType.URL

    def to_dict(self)->dict:
        # Converts the URL monitor object to a dictionary
        base_dict = super().to_dict()
        base_dict.update({
            'url': self.url,
            'expected_status_code': self.expected_status_code,
            'timeout_seconds': self.timeout_seconds,
            'check_ssl': self.check_ssl,
            'follow_redirects': self.follow_redirects,
            'check_content': self.check_content
        })
        return base_dict

    @classmethod
    def from_dict(cls, data: dict) -> 'UrlMonitor':
        # Create URL monitor from dictionary
        monitor = cls(
            id=data['id'],
            name=data['name'],
            space_id=data['space_id'],
            monitor_type=MonitorType(data['monitor_type']),
            status=MonitorStatus(data['status']),
            check_interval_seconds=data['check_interval_seconds'],
            created_at= datetime.fromisoformat(data['created_at']),
            url=data['url'],
            expected_status_code=data['expected_status_code'],
            timeout_seconds=data['timeout_seconds'],
            check_ssl=data['check_ssl'],
            follow_redirects=data['follow_redirects'],
        )
        if data.get('updated_at'):
            monitor.updated_at = datetime.fromisoformat(data['updated_at'])
        if data.get('last_checked_at'):
            monitor.last_checked_at = datetime.fromisoformat(data['last_checked_at'])
        if data.get('last_healthy_at'):
            monitor.last_healthy_at = datetime.fromisoformat(data['last_healthy_at'])
        if data.get('check_content'):
            monitor.check_content = data['check_content']
        return monitor

    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, UrlMonitor):
            return False
        return self.id == other.id

@dataclass
class DatabaseMonitor(BaseMonitor):
    # Database monitoring configuration
    db_type: str = ""  # mysql, postgresql, sqlserver
    host: str = ""
    port: int = 0
    database: str = ""
    username: str = ""
    encrypted_password: str = ""
    connection_timeout_seconds: int = 10
    query_timeout_seconds: int = 30
    test_query: str = "SELECT 1"  # Simple query to test connection
    
    def __post_init__(self):
        super().__post_init__()
        self.monitor_type = MonitorType.DATABASE

    @property
    def password(self)->str:
        if not self.encrypted_password:
            return ""
        try:
            return decrypt_password(self.encrypted_password)
        except Exception as e:
            print(f"Warning: Failed to decrypt password for monitor {self.name}: {e}")
            return ""
    
    @password.setter
    def password(self, plain_password: str):
        if not plain_password:
            self.encrypted_password = ""
        else:
            try:
                self.encrypted_password = encrypt_password(plain_password)
                self.update_timestamp()
            except Exception as e:
                raise Exception(f"Failed to encrypt password for monitor {self.name}: {e}")

    def test_connection_string(self) -> str:
        # Generate connection string for testing (password is decrypted on-demand)
        password = self.password  # This will decrypt the password
        # URL encode the password to handle special characters like @
        encoded_password = urllib.parse.quote_plus(password)
        
        if self.db_type.lower() == 'postgresql':
            return f"postgresql://{self.username}:{encoded_password}@{self.host}:{self.port}/{self.database}"
        elif self.db_type.lower() == 'mysql':
            return f"mysql+pymysql://{self.username}:{encoded_password}@{self.host}:{self.port}/{self.database}"
        elif self.db_type.lower() == 'sqlserver':
            # Fix the connection string format for SQL Server with encoded password
            return f"mssql+pyodbc://{self.username}:{encoded_password}@{self.host}:{self.port}/{self.database}?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes"
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

    
    def to_dict(self) -> dict:
        # Convert database monitor to dictionary for storage
        data = super().to_dict()
        data.update({
            'db_type': self.db_type,
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'username': self.username,
            'password': self.encrypted_password,
            'connection_timeout_seconds': self.connection_timeout_seconds,
            'query_timeout_seconds': self.query_timeout_seconds,
            'test_query': self.test_query
        })
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DatabaseMonitor':
        # Create database monitor from dictionary
        monitor = cls(
            id=data['id'],
            name=data['name'],
            space_id=data['space_id'],
            monitor_type=MonitorType(data['monitor_type']),
            status=MonitorStatus(data['status']),
            check_interval_seconds=data['check_interval_seconds'],
            created_at= datetime.fromisoformat(data['created_at']),
            db_type=data['db_type'],
            host=data['host'],
            port=data['port'],
            database=data['database'],
            username=data['username'],
            encrypted_password=data['password'],
            connection_timeout_seconds=data['connection_timeout_seconds'],
            query_timeout_seconds=data['query_timeout_seconds'],
            test_query=data['test_query'],
        )
        if data.get('updated_at'):
            monitor.updated_at = datetime.fromisoformat(data['updated_at'])
        if data.get('last_checked_at'):
            monitor.last_checked_at = datetime.fromisoformat(data['last_checked_at'])
        if data.get('last_healthy_at'):
            monitor.last_healthy_at = datetime.fromisoformat(data['last_healthy_at'])
        return monitor

    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, DatabaseMonitor):
            return False
        return self.id == other.id

@dataclass
class MonitorResult:
    # Result of a monitor check
    monitor_id: str
    space_id: str
    timestamp: datetime
    status: MonitorStatus
    monitor_type: MonitorType
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    response_time_ms: Optional[float] = None # Response time in milliseconds
    details: Optional[Dict[str, Any]] = None # Details of checks that failed or passed
    failed_checks: int = 0
    check_list: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> dict:
        # Convert monitor result to dictionary for storage
        return {
            'id': self.id,
            'monitor_id': self.monitor_id,
            'space_id': self.space_id,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status.value,
            'monitor_type': self.monitor_type.value,
            'response_time_ms': self.response_time_ms,
            'details': self.details,
            'failed_checks': self.failed_checks,
            'check_list': self.check_list
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MonitorResult':
        # Create monitor result from dictionary
        result = cls(
            id=data['id'],
            monitor_id=data['monitor_id'],
            space_id=data['space_id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            status=MonitorStatus(data['status']),
            monitor_type=MonitorType(data['monitor_type']),
            response_time_ms=data.get('response_time_ms'),
            details=data.get('details'),
            failed_checks=data['failed_checks'],
            check_list=data.get('check_list')
        )
        return result
