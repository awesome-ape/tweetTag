from datetime import datetime, timedelta
from uuid import uuid4
from jose import JWTError, jwt

from backend.app.core.security import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

RESET_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "type": "access",
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.utcnow(),
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_password_reset_token(user_id: str) -> tuple[str, str]:
    jti = str(uuid4())

    payload = {
        "sub": user_id,
        "type": "password_reset",
        "jti": jti,
        "exp": datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.utcnow(),
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token, jti


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("type") != "access":
            raise ValueError("Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Invalid token payload")

        return user_id

    except JWTError:
        raise ValueError("Invalid or expired token")


def decode_password_reset_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("type") != "password_reset":
            raise ValueError("Invalid token type")

        if not payload.get("sub") or not payload.get("jti"):
            raise ValueError("Invalid token payload")

        return payload

    except JWTError:
        raise ValueError("Invalid or expired token")