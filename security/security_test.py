import unittest
from cryptography.hazmat.primitives import serialization, hashes, padding
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

# Assuming the Encryption class is in a module named `security_module`
from security_module import Encryption

class TestEncryption(unittest.TestCase):

    def setUp(self):
        self.encryption = Encryption()
        self.public_key, self.private_key = self.encryption.generate_rsa_key_pair()
        self.aes_key = self.encryption.generate_aes_key()  # Fixed: no argument passed
        self.iv = self.encryption.generate_iv()  # Fixed: no argument passed

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
        
        # Use the decrypt_rsa method from Encryption class
        decrypted_message = self.encryption.decrypt_rsa(ciphertext, self.private_key)
        self.assertEqual(plaintext, decrypted_message)

    def test_rsa_signing_verification(self):
        # Test RSA signing and verification
        message = b"Secret Message"
        signature = self.encryption.sign_message(message, self.private_key)
        
        # Use validate_signature method from Encryption class to verify
        is_valid = self.encryption.validate_signature(message, signature, self.public_key)
        self.assertTrue(is_valid)

    def test_aes_gcm_encryption_decryption(self):
        # Test AES-GCM encryption and decryption
        plaintext = b"Secret Message"
        ciphertext, tag = self.encryption.encrypt_aes_gcm(plaintext, self.aes_key, self.iv)
        self.assertIsInstance(ciphertext, bytes)
        self.assertIsInstance(tag, bytes)
        self.assertGreater(len(ciphertext), 0)
        self.assertEqual(len(tag), 16)

        # Test AES-GCM decryption
        decrypted_message = self.encryption.decrypt_aes_gcm(ciphertext, self.aes_key, self.iv, tag)
        self.assertEqual(plaintext, decrypted_message)

if __name__ == '__main__':
    unittest.main()
