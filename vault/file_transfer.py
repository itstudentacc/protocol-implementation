# file_transfer.py

import requests

# from server import url?
url = "http://example.com"

# upload the file via HTTP POST request
def upload_file(url, file_path):
    try:
        with open('file_path', mode ='rb') as file:
            files = {'file': (file_path, file)}
            response = requests.post(url, files=files)
            print (response.json())
    except requests.exceptions.RequestException as e:
        return None

# get file HTTP get request
def get_file(url, save_file_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open (save_file_path, mode = 'wb') as file:
            file.write(response.content)
        return True
    else:  
        return False
