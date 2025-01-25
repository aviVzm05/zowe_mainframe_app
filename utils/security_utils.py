from cryptography.fernet import Fernet
import base64
import os
from pathlib import Path
import logging
from datetime import datetime, timedelta

class CredentialManager:
    def __init__(self):
        self.key_file = Path('.keys/encryption.key')
        self.key = self._load_or_create_key()
        self.fernet = None
        self._initialize_fernet()
        
    def _initialize_fernet(self):
        """Initialize Fernet with error handling"""
        try:
            self.fernet = Fernet(self.key)
        except Exception as e:
            logging.error(f"Failed to initialize encryption: {str(e)}")
            raise ValueError("Encryption initialization failed")
    
    def _load_or_create_key(self):
        """Load existing key or create new one with proper permissions"""
        try:
            if not self.key_file.exists():
                self.key_file.parent.mkdir(parents=True, exist_ok=True)
                key = Fernet.generate_key()
                
                # Save key with restricted permissions
                with open(self.key_file, 'wb') as f:
                    f.write(key)
                
                # Set file permissions (0600)
                os.chmod(self.key_file, 0o600)
                
                return key
            
            # Load existing key
            with open(self.key_file, 'rb') as f:
                return f.read()
        except Exception as e:
            logging.error(f"Key management failed: {str(e)}")
            raise ValueError("Failed to manage encryption key")
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt encrypted string"""
        try:
            return self.fernet.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logging.error(f"Decryption failed: {str(e)}")
            return None

class SecureProfileManager:
    def __init__(self, profile_manager):
        if not profile_manager:
            raise ValueError("Profile manager cannot be None")
        self.profile_manager = profile_manager
        self.credential_manager = CredentialManager()
        self.creation_time = datetime.now()
        self.expiry_duration = timedelta(hours=1)
    
    def is_expired(self):
        """Check if the session has expired"""
        return datetime.now() - self.creation_time > self.expiry_duration
    
    def secure_property(self, json_path: str, value: str):
        """Securely store sensitive property using proper JSON path"""
        sensitive_fields = ['password', 'user', 'certFile']
        
        # Check if this is a sensitive field that needs encryption
        field_name = json_path.split('.')[-1]
        if field_name in sensitive_fields:
            encrypted_value = self.credential_manager.encrypt(value)
            # Store encrypted value with a marker
            self.profile_manager.set_property(f"{json_path}_encrypted", encrypted_value)
        else:
            # Store non-sensitive values directly
            self.profile_manager.set_property(json_path, value)
    
    def get_property(self, json_path: str) -> str:
        """Retrieve property using JSON path, decrypting if necessary"""
        sensitive_fields = ['password', 'user', 'certFile']
        field_name = json_path.split('.')[-1]
        
        if field_name in sensitive_fields:
            # Try to get encrypted value
            encrypted_value = self.profile_manager.get_property(f"{json_path}_encrypted")
            if encrypted_value:
                return self.credential_manager.decrypt(encrypted_value)
        
        # Get regular property
        return self.profile_manager.get_property(json_path)
    
    def cleanup(self):
        """Securely cleanup sensitive data"""
        try:
            if not self.profile_manager:
                return
            
            # Get all profiles
            profiles = self.profile_manager.config_appname
            
            # Clear sensitive properties from all profiles
            sensitive_paths = [
                "profiles.*.properties.password",
                "profiles.*.properties.user",
                "profiles.*.properties.certFile"
            ]
            
            for path in sensitive_paths:
                self.profile_manager.set_property(path, None)
                self.profile_manager.set_property(f"{path}_encrypted", None)
            
            # Save cleared profile
            self.profile_manager.save()
            
            # Clear from memory
            self.profile_manager = None
            logging.info("Profile cleaned up successfully")
            
        except Exception as e:
            logging.error(f"Cleanup failed: {str(e)}")
            raise 