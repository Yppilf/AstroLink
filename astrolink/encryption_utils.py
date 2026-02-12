from cryptography.fernet import Fernet

def generate_key():
    """Generate and return a new Fernet encryption key."""
    return Fernet.generate_key()

def encrypt_data(data: bytes, key: bytes) -> bytes:
    """Encrypt raw data with the provided key."""
    return Fernet(key).encrypt(data)

def decrypt_data(data: bytes, key: bytes) -> bytes:
    """Decrypt raw data with the provided key."""
    return Fernet(key).decrypt(data)
