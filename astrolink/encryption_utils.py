# from cryptography.fernet import Fernet

# def generate_key():
#     """Generate and return a new Fernet encryption key."""
#     return Fernet.generate_key()

# def encrypt_data(data: bytes, key: bytes) -> bytes:
#     """Encrypt raw data with the provided key."""
#     return Fernet(key).encrypt(data)

# def decrypt_data(data: bytes, key: bytes) -> bytes:
#     """Decrypt raw data with the provided key."""
#     return Fernet(key).decrypt(data)

import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

CHUNK_SIZE = 1024 * 1024  # 1 MB
NONCE_SIZE = 12

def generate_key():
    return os.urandom(32)

def encrypt_file(
    input_path: str,
    output_path: str,
    key: bytes,
):
    aes = AESGCM(key)

    with (
        open(input_path, "rb") as src,
        open(output_path, "wb") as dst,
    ):
        while True:
            chunk = src.read(CHUNK_SIZE)

            if not chunk:
                break

            nonce = os.urandom(NONCE_SIZE)

            encrypted = aes.encrypt(
                nonce,
                chunk,
                None,
            )

            dst.write(len(encrypted).to_bytes(4, "big"))
            dst.write(nonce)
            dst.write(encrypted)

def decrypt_file(
    input_path: str,
    output_path: str,
    key: bytes,
):
    aes = AESGCM(key)

    with (
        open(input_path, "rb") as src,
        open(output_path, "wb") as dst,
    ):
        while True:

            size_bytes = src.read(4)

            if not size_bytes:
                break

            encrypted_size = int.from_bytes(
                size_bytes,
                "big",
            )

            nonce = src.read(NONCE_SIZE)

            encrypted = src.read(encrypted_size)

            chunk = aes.decrypt(
                nonce,
                encrypted,
                None,
            )

            dst.write(chunk)