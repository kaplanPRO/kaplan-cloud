import secrets


def generate_random_token():
    return secrets.token_urlsafe(32)
