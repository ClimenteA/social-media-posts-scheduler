import uuid
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from hashlib import sha256


class AESCBC:
    """
    aes_cbc = AESCBC("secret text")

    encrypted_message_hex = aes_cbc.encrypt("insecure text")
    print("encrypted_message_hex", encrypted_message_hex)

    decrypted_message = aes_cbc.decrypt(encrypted_message_hex)
    print("decrypted_message", decrypted_message)

    """

    def __init__(self, secret_key: str):
        self.key = sha256(uuid.uuid5(uuid.NAMESPACE_DNS, secret_key).bytes).digest()

    def encrypt(self, text: str):
        cipher = AES.new(self.key, AES.MODE_CBC)
        ciphertext = cipher.encrypt(pad(text.encode(), AES.block_size))
        return f"{cipher.iv.hex()}:{ciphertext.hex()}"

    def decrypt(self, encrypted_text: str):
        iv_hex = encrypted_text.split(":")[0]
        encrypted_text_hex = encrypted_text.split(":")[1]
        iv = bytes.fromhex(iv_hex)
        encrypted_text = bytes.fromhex(encrypted_text_hex)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        plaintext = unpad(cipher.decrypt(encrypted_text), AES.block_size)
        return plaintext.decode()
