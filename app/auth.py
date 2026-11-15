import hashlib, hmac, json, time
from urllib.parse import parse_qsl
import jwt
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from .config import settings
from .db import get_db
from .models import User

INIT_DATA_MAX_AGE = 86400

def verify_telegram_init_data(init_data: str) -> dict:
    if not init_data:
        raise HTTPException(401, "Telegram initData is required")
    data = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = data.pop("hash", None)
    if not received_hash:
        raise HTTPException(401, "Invalid Telegram initData")
    auth_date = int(data.get("auth_date", "0"))
    if auth_date <= 0 or time.time() - auth_date > INIT_DATA_MAX_AGE or auth_date > time.time() + 60:
        raise HTTPException(401, "Telegram initData expired")
    check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret_key = hmac.new(b"WebAppData", settings.telegram_bot_token.encode(), hashlib.sha256).digest()
    calculated = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated, received_hash):
        raise HTTPException(401, "Telegram signature mismatch")
    try:
        user_data = json.loads(data["user"])
    except (KeyError, json.JSONDecodeError):
        raise HTTPException(401, "Telegram user data missing")
    return user_data

def issue_token(user: User) -> str:
    now = int(time.time())
    return jwt.encode({"sub": str(user.id), "iat": now, "exp": now + settings.jwt_expire_minutes * 60}, settings.jwt_secret, algorithm="HS256")

def current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Bearer token required")
    try:
        payload = jwt.decode(authorization[7:], settings.jwt_secret, algorithms=["HS256"])
        user = db.get(User, int(payload["sub"]))
    except Exception:
        raise HTTPException(401, "Invalid or expired token")
    if not user:
        raise HTTPException(401, "User not found")
    return user
