import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from webmonitor.utils import encrypt_password, decrypt_password

class EmailConfig:
    
    def __init__(self, config_file_path: str = "data/email_config.json"):
        self.config_file_path = Path(config_file_path)
        self.logger = logging.getLogger(__name__)
        self._config: Optional[Dict[str, Any]] = None
        
    def load_config(self) -> Optional[Dict[str, Any]]:
        # Load email configuration from file.
        if not self.config_file_path.exists():
            self.logger.info("Email configuration file not found")
            return None
            
        try:
            with open(self.config_file_path, 'r') as f:
                self._config = json.load(f)
            self.logger.info("Email configuration loaded successfully")
            return self._config
        except Exception as e:
            self.logger.error(f"Failed to load email configuration: {e}")
            return None
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save email configuration to file with encrypted password."""
        try:
            # Ensure data directory exists
            self.config_file_path.parent.mkdir(exist_ok=True)
            
            # Encrypt password if provided
            if 'password' in config and config['password']:
                config['encrypted_password'] = encrypt_password(config['password'])
                # Remove plain text password from config
                del config['password']
            
            # Add timestamps
            config['last_updated'] = datetime.now().isoformat()
            if 'configured_at' not in config:
                config['configured_at'] = config['last_updated']
            
            # Write configuration file
            with open(self.config_file_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Set secure file permissions (owner read/write only)
            os.chmod(self.config_file_path, 0o600)
            
            self._config = config
            self.logger.info("Email configuration saved successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save email configuration: {e}")
            return False
    
    def get_decrypted_config(self) -> Optional[Dict[str, Any]]:
        """Get configuration with decrypted password."""
        if self._config is None:
            self._config = self.load_config()
            
        if self._config is None:
            return None
            
        # Create a copy to avoid modifying the original
        config = self._config.copy()
        
        # Decrypt password if present
        if 'encrypted_password' in config and config['encrypted_password']:
            try:
                config['password'] = decrypt_password(config['encrypted_password'])
                # Remove encrypted version from returned config
                del config['encrypted_password']
            except Exception as e:
                self.logger.error(f"Failed to decrypt email password: {e}")
                return None
        
        return config
    
    def is_configured(self) -> bool:
        """Check if email is properly configured."""
        config = self.get_decrypted_config()
        if not config:
            return False
            
        required_fields = ['smtp_host', 'smtp_port', 'username', 'password']
        return all(field in config and config[field] for field in required_fields)
    
    def get_smtp_settings(self) -> Optional[Dict[str, Any]]:
        """Get SMTP settings for email service initialization."""
        config = self.get_decrypted_config()
        if not config:
            return None
            
        return {
            'smtp_host': config.get('smtp_host', 'smtp.gmail.com'),
            'smtp_port': config.get('smtp_port', 587),
            'username': config.get('username'),
            'password': config.get('password'),
            'from_name': config.get('from_name', 'Web Monitor')
        }
    
    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, str]:
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
    
    def get_config_status(self) -> Dict[str, Any]:
        """Get configuration status for display (without sensitive data)."""
        config = self.load_config()
        if not config:
            return {
                'configured': False,
                'message': 'Email not configured'
            }
        
        return {
            'configured': True,
            'smtp_host': config.get('smtp_host'),
            'smtp_port': config.get('smtp_port'),
            'username': config.get('username'),
            'from_name': config.get('from_name', 'Web Monitor'),
            'configured_at': config.get('configured_at'),
            'last_updated': config.get('last_updated'),
            'has_password': bool(config.get('encrypted_password'))
        }

# Global instance
_email_config = None

def get_email_config() -> EmailConfig:
    """Get the global email configuration instance."""
    global _email_config
    if _email_config is None:
        _email_config = EmailConfig()
    return _email_config
