import base64
from typing import Optional
from cryptography.fernet import Fernet

class EncryptionService:
    # Service for encrypting and decrypting sensitive data like passwords

    def __init__(self):
        self._fernet = None
        self._load_key_from_config()

    def _load_key_from_config(self):
        try:
            from webmonitor.config import get_config_manager
            config_manager = get_config_manager()

            key_b64 = config_manager.get_encryption_key()
            if not key_b64:
                # Generate new key and save to config
                key = Fernet.generate_key()
                key_b64 = base64.b64encode(key).decode('utf-8')
                config_manager.set_encryption_key(key_b64)

            # Decode and use the key
            key = base64.b64decode(key_b64.encode('utf-8'))
            self._fernet = Fernet(key)
        except Exception as e:
            raise Exception(f"Failed to load encryption key from config manager: {e}")
    
    def encrypt_data(self, data: str) -> str:
        if not data:
            return ""
        
        try:
            # Convert data to bytes
            data_bytes = data.encode('utf-8')
            
            # Encrypt the data
            encrypted_bytes = self._fernet.encrypt(data_bytes)
            
            # Return base64 encoded string for storage
            return base64.b64encode(encrypted_bytes).decode('utf-8')
        
        except Exception as e:
            raise Exception(f"Failed to encrypt data: {e}")
    
    def decrypt_data(self, encrypted_data: str) -> str:
        if not encrypted_data:
            return ""
        
        try:
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            
            # Decrypt the data
            data_bytes = self._fernet.decrypt(encrypted_bytes)
            
            # Return decrypted data as string
            return data_bytes.decode('utf-8')
        
        except Exception as e:
            raise Exception(f"Failed to decrypt data: {e}")
    
    def is_encrypted(self, value: str) -> bool:
        if not value:
            return False
        
        try:
            # Try to base64 decode it
            decoded = base64.b64decode(value.encode('utf-8'))
            # If it's base64 and has the right length, it's likely encrypted
            return len(decoded) > 0
        except:
            return False
    
    def rotate_key(self):
        # This is a placeholder for key rotation functionality
        raise NotImplementedError("Key rotation not implemented yet")

# Global instance
_encryption_service = None

def get_encryption_service() -> EncryptionService:
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service

def encrypt_password(password: str) -> str:
    return get_encryption_service().encrypt_data(password)

def decrypt_password(encrypted_password: str) -> str:
    return get_encryption_service().decrypt_data(encrypted_password)