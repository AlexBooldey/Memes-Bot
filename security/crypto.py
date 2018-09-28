import hashlib
import os.path
from functools import lru_cache


class Crypto:

    def __init__(self):
        self.path = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        self.key = input("Enter key: ")


    def check_key(self):
        return True if os.path.isfile(self.path + '/key.data') else False

    def fast_encrypt(self, msg):
        full_key = str(msg) + str(self.key)

        hash_obj = hashlib.md5(full_key.encode('utf-8'))
        return hash_obj.hexdigest()

    def encrypt(self, msg):
        full_key = str(msg) + str(self.key)

        hash_obj = hashlib.md5(full_key.encode('utf-8'))
        hash_val = hash_obj.hexdigest()

        with open(self.path + '/key.data', 'w') as file:
            file.write(hash_val)
        file.close()

    @lru_cache(maxsize=12)
    def decipher(self):
        with open(self.path + '/key.data', 'r') as file:
            encrypted_text = file.read()
        file.close()
        return encrypted_text
