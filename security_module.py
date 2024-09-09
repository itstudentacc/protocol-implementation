# security_module.py
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256

from utility import encode_data, decode_data

import base64


# Generate the RSA key using the imported library
def generate_RSA_key():
    key = RSA.generate(2048) # Generate a 2048-bit RSA key
    public_key = key.publickey().export_key().decode('utf-8')
    private_key = key.export_key().decode('utf-8')
    return private_key,public_key


# Encrypt the message using the public key, utilizing encode_data from utility.py
def encrypt_message(public_key, message):
    try:
        # Import the public key
        key = RSA.import_key(public_key) 
        cipher = PKCS1_OAEP.new(key) 
        encryption = cipher.encrypt(message.encode('utf-8'))
        return encode_data(encryption)
    
    # Error handling
    except Exception as e:
        print ("Failed to encrypt message!")
        return None
    
# Decrypt the message using the private key, utilizing decode_data from utility.py
def decrypt_message(private_key, message):
    try:
        # Import the key
        key = RSA.import_key(private_key) 
        cipher = PKCS1_OAEP.new(key) 

        decryption = cipher.decrypt(decode_data(message)).decode('utf-8')
        return decryption
    
    # Error handling
    except Exception as e:
        print ("Failed to decrypt message!")
        return None

# Sign message utilizing private key
def sign_message(private_key, message):
    try:
        # Import the private key
        key = RSA.import_key(private_key)

       # Create a hash and sign the message
        hash_message = SHA256.new(message.encode('utf-8'))
        signature = pkcs1_15.new(key).sign(hash_message)
        return encode_data(signature)
    
    # Error handling
    except Exception as e:
        print ("Failed to sign message!")
        return None

# Generate signature
def generate_signature(private_key, message):
    try:
        # Import the private key
        key = RSA.import_key(private_key)

       # Create a hash and sign the message
        hash_message = SHA256.new(message.encode('utf-8'))
        signature = pkcs1_15.new(key).sign(hash_message)
        return encode_data(signature)
    
    # Error handling
    except Exception as e:
        print ("Failed to generate signature!")
        return None


# Verify message
def verify_signature(public_key, message, signature):
    try:
        # Import the public key
        key = RSA.import_key(public_key)

       # Create a hash and sign the message
        hash_message = SHA256.new(message.encode('utf-8'))
        pkcs1_15.new(key).verify(hash_message, decode_data(signature))

        # return it as true if it validates successfully
        return True
    
    # Error handling
    except Exception as e:
        return False

def generate_fingerprint(public_key):
    try:
        # Import the public key
        key = RSA.import_key(public_key) 

        # Create a hash of the public key
        hash_key = SHA256.new(key.export_key())
        return hash_key.hexdigest()
    
    # error handling
    except Exception as e:
        print ("Failed to generate fingerprint")
        return None


