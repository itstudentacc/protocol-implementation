import unittest
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import os
from cryptography.hazmat.backends import default_backend

# Assuming the Encryption class is in a module named `encryption_module`
from security_module import Encryption

class TestEncryption(unittest.TestCase):

    def setUp(self):
        self.encryption = Encryption()
        self.public_key, self.private_key = self.encryption.generate_rsa_key_pair()
        self.aes_key = self.encryption.generate_aes_key()
        self.iv = self.encryption.generate_iv()

    def test_rsa_key_generation(self):
        # Test RSA key pair generation
        self.assertIsInstance(self.public_key, bytes)
        self.assertIsInstance(self.private_key, bytes)
        self.assertGreater(len(self.public_key), 0)
        self.assertGreater(len(self.private_key), 0)

    def test_aes_key_generation(self):
        # Test AES key generation
        self.assertEqual(len(self.aes_key), 32)

    def test_iv_generation(self):
        # Test IV generation
        self.assertEqual(len(self.iv), 16)

    def test_rsa_encryption_decryption(self):
        # Test RSA encryption and decryption
        plaintext = b"Secret Message"
        ciphertext = self.encryption.encrypt_rsa(plaintext, self.public_key)
        
        # Load private key for decryption
        private_key = serialization.load_pem_private_key(self.private_key, password=None, backend=default_backend())
        
        decrypted_message = private_key.decrypt(
            ciphertext,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        )
        self.assertEqual(plaintext, decrypted_message)

    def test_rsa_signing_verification(self):
        # Test RSA signing and verification
        message = b"Secret Message"
        signature = self.encryption.sign_rsa(message, self.private_key)
        
        # Load public key for verification
        public_key = serialization.load_pem_public_key(self.public_key, backend=default_backend())
        
        try:
            public_key.verify(
                signature,
                message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=32
                ),
                hashes.SHA256()
            )
        except Exception as e:
            self.fail(f"Verification failed: {str(e)}")

    def test_aes_gcm_encryption(self):
        # Test AES-GCM encryption
        plaintext = b"Secret Message"
        ciphertext, tag = self.encryption.encrypt_aes_gcm(plaintext, self.aes_key, self.iv)
        self.assertIsInstance(ciphertext, bytes)
        self.assertIsInstance(tag, bytes)
        self.assertGreater(len(ciphertext), 0)
        self.assertEqual(len(tag), 16)

if __name__ == '__main__':
    unittest.main()
