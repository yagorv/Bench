import hashlib

def verify_password(stored_hex, password):
    candidate = hashlib.sha1(password.encode()).hexdigest()
    return candidate == stored_hex
