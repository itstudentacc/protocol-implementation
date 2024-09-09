# This file is for testing only
# The code below is generated using Chat GPT 
# Check whether all the functions implemented in security_module.py and utility.py are working correctly or not
# Testing result can be seen in the terminal

import unittest
import logging
from security_module import generate_RSA_key, encrypt_message, decrypt_message, sign_message, verify_signature, generate_fingerprint

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class TestSecurityModule(unittest.TestCase):
    def test_generate_RSA_key(self):
        private_key, public_key = generate_RSA_key()
        self.assertIsNotNone(private_key)
        self.assertIsNotNone(public_key)
        logging.debug(f"Private Key: {private_key}")
        logging.debug(f"Public Key: {public_key}")

    def test_encrypt_message(self):
        private_key, public_key = generate_RSA_key()
        message = "Hello, World!"
        encrypted_message = encrypt_message(public_key, message)
        self.assertIsNotNone(encrypted_message)
        logging.debug(f"Encrypted Message: {encrypted_message}")

    def test_decrypt_message(self):
        private_key, public_key = generate_RSA_key()
        message = "Hello, World!"
        encrypted_message = encrypt_message(public_key, message)
        decrypted_message = decrypt_message(private_key, encrypted_message)
        self.assertEqual(message, decrypted_message)
        logging.debug(f"Decrypted Message: {decrypted_message}")

    def test_sign_message(self):
        private_key, public_key = generate_RSA_key()
        message = "Hello, World!"
        signature = sign_message(private_key, message)
        self.assertIsNotNone(signature)
        logging.debug(f"Signature: {signature}")

    def test_verify_signature(self):
        private_key, public_key = generate_RSA_key()
        message = "Hello, World!"
        signature = sign_message(private_key, message)
        result = verify_signature(public_key, message, signature)
        self.assertTrue(result)
        logging.debug(f"Verification Result: {result}")

    def test_generate_fingerprint(self):
        private_key, public_key = generate_RSA_key()
        fingerprint = generate_fingerprint(public_key)
        self.assertIsNotNone(fingerprint)
        self.assertIsInstance(fingerprint, str)
        logging.debug( f"fingerprint: {fingerprint}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
