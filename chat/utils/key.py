import secrets
import string

def generate_unique_key(length=40):
    characters = string.ascii_letters + string.digits

    unique_key = ''.join(secrets.choice(characters) for _ in range(length))
    return unique_key

