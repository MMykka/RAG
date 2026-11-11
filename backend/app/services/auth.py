from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash
from app.config import settings

password_hash = PasswordHash.recommended()   # Argon2 with safe default settings

# hash_password hashes a password using the Argon2 algorithm. It takes a plain-text password as input and returns the hashed version of the password, which can be stored in the database.
def hash_password(password: str) -> str:
    return password_hash.hash(password)

# verify_password checks if a given password matches the hashed password stored in the database. It uses the same hashing algorithm (Argon2) to verify the password.
def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)

# create a JWT access token for a user, which includes the user ID and an expiration time. The token is signed using the secret key and algorithm specified in the settings.
def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)

# decode_access_token decodes a JWT access token and extracts the user ID from it. If the token is invalid or expired, it returns None.
def decode_access_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        return int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        return None
