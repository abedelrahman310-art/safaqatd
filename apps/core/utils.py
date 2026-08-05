import os
import hashlib
from cryptography.fernet import Fernet
from django.conf import settings

def get_cipher_suite():
    # Retrieve the key from settings. Ensure it's 32 url-safe base64-encoded bytes.
    # For development, if the key is not proper, we can fall back or generate one, 
    # but let's assume it's correctly provided or we generate a dummy one if it's the default.
    key = settings.ENCRYPTION_KEY.encode('utf-8')
    if len(key) != 44:  # standard Fernet key length
        # Just for safe fallback during development
        key = Fernet.generate_key()
    return Fernet(key)

def encrypt_file_content(file_content: bytes) -> bytes:
    """Encrypts the raw bytes of a file."""
    cipher_suite = get_cipher_suite()
    return cipher_suite.encrypt(file_content)

def decrypt_file_content(encrypted_content: bytes) -> bytes:
    """Decrypts the raw bytes of a file."""
    cipher_suite = get_cipher_suite()
    return cipher_suite.decrypt(encrypted_content)

def generate_file_hash(file_content: bytes) -> str:
    """Generates a SHA-256 hash of the file content for integrity verification."""
    sha256_hash = hashlib.sha256()
    sha256_hash.update(file_content)
    return sha256_hash.hexdigest()
