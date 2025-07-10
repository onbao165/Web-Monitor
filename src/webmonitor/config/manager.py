import os
import json
import logging
import base64
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

class ConfigManager:    
    def __init__(self, config_file_path: str = "data/webmonitor_config.json"):
        self.config_file_path = Path(config_file_path)
        self.logger = logging.getLogger(__name__)
        self._config: Optional[Dict[str, Any]] = None
        
    def load_config(self) -> Optional[Dict[str, Any]]:
        if not self.config_file_path.exists():
            self.logger.info("Configuration file not found, creating default config")
            self._create_default_config()
            
        try:
            with open(self.config_file_path, 'r') as f:
                self._config = json.load(f)
            self.logger.info("Configuration loaded successfully")
            return self._config
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            return None
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        try:
            # Ensure data directory exists
            self.config_file_path.parent.mkdir(exist_ok=True)

            # Encrypt email password if provided
            if 'email' in config and 'password' in config['email'] and config['email']['password']:
                from webmonitor.utils import encrypt_password
                config['email']['encrypted_password'] = encrypt_password(config['email']['password'])
                # Remove plain text password from config
                del config['email']['password']
            
            # Add timestamps
            config['last_updated'] = datetime.now().isoformat()
            if 'configured_at' not in config:
                config['configured_at'] = config['last_updated']
            
            # Write configuration file
            with open(self.config_file_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            self._config = config
            self.logger.info("Configuration saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False
    
    def get_config(self) -> Optional[Dict[str, Any]]:
        if self._config is None:
            self._config = self.load_config()
        return self._config
    
    def get_email_config(self) -> Optional[Dict[str, Any]]:
        config = self.get_config()
        if not config or 'email' not in config:
            return None
            
        email_config = config['email'].copy()
        
        # Decrypt password if present
        if 'encrypted_password' in email_config and email_config['encrypted_password']:
            try:
                from webmonitor.utils import decrypt_password
                email_config['password'] = decrypt_password(email_config['encrypted_password'])
                # Remove encrypted version from returned config
                del email_config['encrypted_password']
            except Exception as e:
                self.logger.error(f"Failed to decrypt email password: {e}")
                return None
        
        return email_config
    
    def get_health_alerts_config(self) -> Dict[str, Any]:
        config = self.get_config()
        if not config or 'health_alerts' not in config:
            return self._get_default_health_alerts_config()
        return config['health_alerts']
    
    def get_data_cleanup_config(self) -> Dict[str, Any]:
        config = self.get_config()
        if not config or 'data_cleanup' not in config:
            return self._get_default_data_cleanup_config()
        return config['data_cleanup']
    
    def get_encryption_key(self) -> Optional[str]:
        config = self.get_config()
        if not config or 'security' not in config:
            return None
        return config['security'].get('encryption_key')
    
    def set_encryption_key(self, key: str) -> bool:
        config = self.get_config() or {}
        if 'security' not in config:
            config['security'] = {}
        config['security']['encryption_key'] = key
        return self.save_config(config)
    
    def is_email_configured(self) -> bool:
        email_config = self.get_email_config()
        if not email_config:
            return False
            
        required_fields = ['smtp_host', 'smtp_port', 'username', 'password']
        return all(field in email_config and email_config[field] for field in required_fields)
    
    def _create_default_config(self) -> None:
        default_config = {
            "email": {
                "smtp_host": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "",
                "from_name": "Web Monitor"
            },
            "health_alerts": self._get_default_health_alerts_config(),
            "data_cleanup": self._get_default_data_cleanup_config(),
            "security": {
                "encryption_key": self._generate_encryption_key()
            }
        }
        
        self.save_config(default_config)
    
    def _get_default_health_alerts_config(self) -> Dict[str, Any]:
        return {
            "enabled": True,
            "check_interval_minutes": 60,
            "unhealthy_threshold_hours": 24
        }
    
    def _get_default_data_cleanup_config(self) -> Dict[str, Any]:
        return {
            "enabled": True,
            "cleanup_interval_hours": 24,
            "keep_healthy_results_days": 7,
            "keep_unhealthy_results_days": 30
        }
    
    def _generate_encryption_key(self) -> str:
        from cryptography.fernet import Fernet
        key = Fernet.generate_key()
        return base64.b64encode(key).decode('utf-8')

# Global instance
_config_manager = None

def get_config_manager() -> ConfigManager:
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
