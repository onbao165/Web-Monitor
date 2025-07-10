import os
import base64
from pathlib import Path
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class EncryptionService:
    # Service for encrypting and decrypting sensitive data like passwords
    
    def __init__(self, key_file_path: str = "data/.encryption_key"):
        self.key_file_path = Path(key_file_path)
        self._fernet = None
        self._ensure_key_exists()
    
    def _ensure_key_exists(self):
        if not self.key_file_path.exists():
            self._generate_new_key()
        self._load_key()
    
    def _generate_new_key(self):
        self.key_file_path.parent.mkdir(exist_ok=True)

        key = Fernet.generate_key()
        
        with open(self.key_file_path, 'wb') as key_file:
            key_file.write(key)
        
        # Set file permissions to be readable only by owner (on Unix-like systems)
        try:
            os.chmod(self.key_file_path, 0o600)
        except OSError:
            # Windows doesn't support chmod the same way
            pass
        
        print(f"🔑 New encryption key generated and saved to {self.key_file_path}")
    
    def _load_key(self):
        try:
            with open(self.key_file_path, 'rb') as key_file:
                key = key_file.read()
                self._fernet = Fernet(key)
        except Exception as e:
            raise Exception(f"Failed to load encryption key: {e}")
    
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
    
    def rotate_key(self, old_key_file: Optional[str] = None):
        # Rotate encryption key (for advanced security)
        # This is a placeholder for key rotation functionality
        raise NotImplementedError("Key rotation not implemented yet")

# Global instance
_encryption_service = None

def get_encryption_service() -> EncryptionService:
    # Get the global encryption service instance
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = EncryptionService()
    return _encryption_service

def encrypt_password(password: str) -> str:
    return get_encryption_service().encrypt_data(password)

def decrypt_password(encrypted_password: str) -> str:
    return get_encryption_service().decrypt_data(encrypted_password)