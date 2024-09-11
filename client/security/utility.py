#utility.py
import base64

# base64 encoding
def encode_data(data):
    if isinstance(data, str):
        data = data.encode('utf-8')
    encoded_bytes = base64.b64encode(data)
    return encoded_bytes.decode('utf-8')

# base 64 decoding
def decode_data(data):
    return base64.b64decode(data)

