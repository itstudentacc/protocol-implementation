from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature
import base64
import hashlib
import os

class Encryption:
    def __init__(self):
        self.backend = default_backend()

    def generate_rsa_key_pair(self):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=self.backend
        )
        public_key = private_key.public_key()

        # Export keys
        pem_private_key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )

        pem_public_key = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        return pem_public_key, pem_private_key

    def generate_aes_key(self, key_length=32):
        return os.urandom(key_length)

    def generate_iv(self):
        return os.urandom(16)

    def encrypt_rsa(self, plaintext: bytes, public_key_pem: bytes) -> bytes:
        """
        Encrypts plaintext using RSA public key.

        Args:
            plaintext (bytes): Data to be encrypted.
            public_key_pem (bytes): Public key in PEM format.

        Returns:
            bytes: Encrypted data.
        """
        # Load public key
        public_key = serialization.load_pem_public_key(public_key_pem, backend=self.backend)

        # Encrypt the data
        ciphertext = public_key.encrypt(
            plaintext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return ciphertext

    def decrypt_rsa(self, ciphertext: bytes, private_key_pem: bytes) -> bytes:
        """
        Decrypts ciphertext using RSA private key.

        Args:
            ciphertext (bytes): Encrypted data.
            private_key_pem (bytes): Private key in PEM format.

        Returns:
            bytes: Decrypted data.
        """
        # Load private key
        private_key = serialization.load_pem_private_key(private_key_pem, password=None, backend=self.backend)

        # Decrypt the data
        plaintext = private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return plaintext

    def sign_rsa(self, message: bytes, private_key_pem: bytes) -> bytes:
        """
        Signs a message using RSA private key.

        Args:
            message (bytes): Message to be signed.
            private_key_pem (bytes): Private key in PEM format.

        Returns:
            bytes: Signature.
        """
        # Load private key
        private_key = serialization.load_pem_private_key(private_key_pem, password=None, backend=self.backend)

        # Sign the message
        signature = private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=32
            ),
            hashes.SHA256()
        )
        return signature

    def encrypt_aes_gcm(self, plaintext: bytes, aes_key: bytes, iv: bytes) -> bytes:
        """
        Encrypts plaintext using AES-GCM.

        Args:
            plaintext (bytes): Data to be encrypted.
            aes_key (bytes): AES key.
            iv (bytes): Initialization vector.

        Returns:
            bytes: Ciphertext.
        """
        cipher = Cipher(algorithms.AES(aes_key), modes.GCM(iv), backend=self.backend)
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        return ciphertext

    
    def generate_fingerprint(self, public_key):
        # Export the public key in PEM format
        
        # Compute the SHA-256 hash of the PEM-encoded public key
        return hashlib.sha256(public_key).digest()
    
    
    def validate_signature(self, message, signature, public_key_pem):
        try:
            # Load public key
            public_key = serialization.load_pem_public_key(public_key_pem, backend=self.backend)

            # Verify the signature
            public_key.verify(
                signature,
                message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception as e:
            print(f"Signature validation failed: {e}")
            return False
        
        