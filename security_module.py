# security_module.py
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Signature import pkcs1_15

from utility import encode_data, decode_data


# Generate the RSA key using the imported library
def generate_RSA_key():
    key = RSA.generate(2048)
    publicKey = key.publickey().export_key().decode('utf-8')
    privateKey = key.export_key().decode('utf-8')
    return privateKey,publicKey





