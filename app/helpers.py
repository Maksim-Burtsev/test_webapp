from passlib.hash import sha256_crypt


def hash_password(password: str) -> str:
    return sha256_crypt.encrypt(password)
