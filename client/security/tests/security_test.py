# This file is for testing only
# The code below is generated using Chat GPT 
# Check whether all the functions implemented in security_module.py and utility.py are working correctly or not
# Testing result can be seen in the terminal

import unittest
from security_module import (
    generate_RSA_key,
    encrypt_message,
    decrypt_message,
    sign_message,
    verify_signature,
    aes_encrypt,
    aes_decrypt,
    generate_fingerprint
)
from utility import encode_data, decode_data
from Crypto.Random import get_random_bytes

class TestSecurityModule(unittest.TestCase):

    def setUp(self):
        # Generate RSA keys for testing
        self.private_key, self.public_key = generate_RSA_key()
        self.message = "This is a test message."
        self.symmetric_key = get_random_bytes(32)  # AES-GCM requires a 32-byte key
        self.fingerprint = generate_fingerprint(self.public_key)
    
    def test_rsa_key_generation(self):
        private_key, public_key = generate_RSA_key()
        self.assertIsInstance(private_key, str)
        self.assertIsInstance(public_key, str)
    
    def test_rsa_encryption_decryption(self):
        encrypted_message = encrypt_message(self.public_key, self.message)
        self.assertIsNotNone(encrypted_message)
        
        decrypted_message = decrypt_message(self.private_key, encrypted_message)
        self.assertEqual(self.message, decrypted_message)
    
    def test_rsa_signing_verification(self):
        signature = sign_message(self.private_key, self.message)
        self.assertIsNotNone(signature)
        
        is_verified = verify_signature(self.public_key, self.message, signature)
        self.assertTrue(is_verified)
    
    def test_aes_encryption_decryption(self):
        iv, encrypted_message, tag = aes_encrypt(self.symmetric_key, self.message)
        self.assertIsNotNone(iv)
        self.assertIsNotNone(encrypted_message)
        self.assertIsNotNone(tag)
        
        decrypted_message = aes_decrypt(self.symmetric_key, iv, encrypted_message, tag)
        self.assertEqual(self.message, decrypted_message)
    
    def test_fingerprint_generation(self):
        fingerprint = generate_fingerprint(self.public_key)
        self.assertIsNotNone(fingerprint)
        self.assertEqual(fingerprint, self.fingerprint)

if __name__ == '__main__':
    unittest.main()
