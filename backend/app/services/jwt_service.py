from datetime import datetime, timedelta
from jose import JWTError, jwt
from app.core.security import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES


def create_access_token(user_id: str) -> str:
    payload = {
        "sub": user_id,                     # 🔑 כאן ה־user_id
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.utcnow()
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")

        if user_id is None:
            raise ValueError("Invalid token payload")

        return user_id

    except JWTError:
        raise ValueError("Invalid or expired token")
