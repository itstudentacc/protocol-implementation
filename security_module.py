# security_module.py
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Signature import pkcs1_15

from utility import encode_data, decode_data


# Generate the RSA key using the imported library
def generate_RSA_key():
    key = RSA.generate(2048) # Generate a 2048-bit RSA key
    public_key = key.publickey().export_key().decode('utf-8')
    private_key = key.export_key().decode('utf-8')
    return private_key,public_key


# Encrypt the message using the public key, utilizing encode_data from utility.py
def encrypt_message(public_key, message):
    try:
        key = RSA.import_key(public_key) # Import the key
        cipher = PKCS1_OAEP.new(key) # Create a new cipher
        encryption = cipher.encrypt(message.encode('utf-8'))
        return encode_data(encryption)
    except Exception as e:
        print ("Failed to encrypt message!")
        return None
    
# Decrypt the message using the private key, utilizing decode_data from utility.py
def decrypt_message(private_key, message):
    try:
        key = RSA.import_key(private_key) # Import the key
        cipher = PKCS1_OAEP.new(key) # Create a new cipher
        decryption = cipher.decrypt(decode_data(message)).decode('utf-8')
        return decryption
    except Exception as e:
        print ("Failed to decrypt message!")
        return None

