from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import hashlib
import base64
import os

#Constant
KEY_SIZE_RSA = 2048
PUBLIC_EXPONENT = 65537
IV_SIZE = 16
KEY_LENGTH = 16


# Make class Encryption with cryptographic functions
class Encryption:
    # define self
    def __init__(self):
        self.backend = default_backend()

    # generate private and public key
    def generate_rsa_key_pair(self):
        private_key = rsa.generate_private_key(
            public_exponent= PUBLIC_EXPONENT,
            key_size= KEY_SIZE_RSA,
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
    
    def export_public_key(self, public_key):
        pem_public_key = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return pem_public_key
    
    def export_private_key(self, private_key):
        pem_private_key = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )

        return pem_private_key
    
    #load public key from pem
    def load_public_key(self, pem_public_key):
        public_key = serialization.load_pem_public_key(pem_public_key, backend=self.backend)
        return public_key
    
    #load private key from pem
    def load_private_key(self, pem_private_key):
        private_key = serialization.load_pem_private_key(pem_private_key, password=None, backend=self.backend)
        return private_key

    # Generate random AES key
    def generate_aes_key(self):
        return os.urandom(KEY_LENGTH)

    # Generate random IV
    def generate_iv(self):
        return os.urandom(IV_SIZE)

    # Encrypt data using RSA
    def encrypt_rsa(self, data, public_key):

        # Encrypt the data
        ciphertext = public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return ciphertext

    # Decrypt data using RSA
    def decrypt_rsa(self, cipher_data, private_key):
        # Decrypt the data
        plaintext = private_key.decrypt(
            cipher_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return plaintext
    
    # Encrypt symmetric key
    def encrypt_aes_gcm(self, plaintext, aes_key, iv):
        encryptor = Cipher(
            algorithms.AES(aes_key),
            modes.GCM(iv),
            backend=self.backend
        ).encryptor()
        # Encrypt the data
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        return ciphertext, encryptor.tag
    

    # Decrypt symmetric key
    def decrypt_aes_gcm(self, ciphertext, aes_key, iv, tag):
        decryptor = Cipher(
            algorithms.AES(aes_key),
            modes.GCM(iv, tag),
            backend=self.backend
        ).decryptor()
        # Decrypt the data
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        return plaintext

    # Sign messages
    def sign_message(self, message, private_key_pem):
        # load private key
        private_key = serialization.load_pem_private_key(private_key_pem, password=None, backend=self.backend)

        # Sign the message
        signature = private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature
    
    # Calculate fingerprint using public key
    def generate_fingerprint(self, public_key_pem):
        
        fingerprint = hashlib.sha256(public_key_pem).digest()
        return base64.b64encode(fingerprint).decode('utf-8')

        