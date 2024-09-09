# security_module.py

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA256
from Crypto.Signature import pss
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

from utility import encode_data, decode_data

# Generate the RSA key using the imported library
def generate_RSA_key():
    key = RSA.generate(2048)  # Generate a 2048-bit RSA key
    public_key = key.publickey().export_key().decode('utf-8')
    private_key = key.export_key().decode('utf-8')
    return private_key, public_key

# Encrypt the message using the public key, utilizing encode_data from utility.py
def encrypt_message(public_key, message):
    try:
        # Import the public key
        key = RSA.import_key(public_key)
        cipher = PKCS1_OAEP.new(key)
        encryption = cipher.encrypt(message.encode('utf-8'))
        return encode_data(encryption)
    except Exception as e:
        print("Failed to encrypt message!")
        return None

# Decrypt the message using the private key, utilizing decode_data from utility.py
def decrypt_message(private_key, message):
    try:
        # Import the key
        key = RSA.import_key(private_key)
        cipher = PKCS1_OAEP.new(key)
        decryption = cipher.decrypt(decode_data(message)).decode('utf-8')
        return decryption
    except Exception as e:
        print("Failed to decrypt message!")
        return None

# Sign message utilizing private key
def sign_message(private_key, message):
    try:
        # Import the private key
        key = RSA.import_key(private_key)
        # Create a hash and sign the message
        hash_message = SHA256.new(message.encode('utf-8'))
        signature = pss.new(key).sign(hash_message)
        return encode_data(signature)
    except Exception as e:
        print("Failed to sign message!")
        return None

# Verify message
def verify_signature(public_key, message, signature):
    try:
        # Import the public key
        key = RSA.import_key(public_key)
        # Create a hash and verify the signature
        hash_message = SHA256.new(message.encode('utf-8'))
        pss.new(key).verify(hash_message, decode_data(signature))
        return True
    except Exception as e:
        return False

def aes_encrypt(symmetric_key, message):
    if not isinstance(symmetric_key, bytes):
        raise TypeError("Expected symmetric_key to be bytes")
    cipher = AES.new(symmetric_key, AES.MODE_GCM)
    ciphertext, _ = cipher.encrypt_and_digest(message.encode('utf-8'))
    return ciphertext  # Return only the ciphertext as bytes



# Decrypt with AES-GCM
def aes_decrypt(symmetric_key, nonce, ciphertext, tag):
    try:
        if not isinstance(symmetric_key, bytes):
            raise TypeError("Expected symmetric_key to be bytes")
        cipher = AES.new(symmetric_key, AES.MODE_GCM, nonce=decode_data(nonce))
        decrypted_message = cipher.decrypt_and_verify(decode_data(ciphertext), decode_data(tag))
        return decrypted_message.decode('utf-8')
    except Exception as e:
        print("Failed to decrypt or verify AES-GCM message!")
        return None

# Generate fingerprint
def generate_fingerprint(public_key):
    """
    Generate a fingerprint for the given public key.
    """
    hash_object = SHA256.new(public_key.encode('utf-8'))
    return encode_data(hash_object.digest())
