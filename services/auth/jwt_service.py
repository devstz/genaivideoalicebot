import jwt
from datetime import datetime, timezone, timedelta
from config.settings import get_settings


class JwtService:
    def __init__(self):
        self.settings = get_settings()
        self.secret_key = self.settings.TOKEN  # Using bot token as secret for simplicity, can be separated later
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 30

    def create_access_token(self, user_id: int) -> str:
        """Генерирует Access Token со сроком жизни 30 минут."""
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        to_encode = {"sub": str(user_id), "type": "access", "exp": expire}
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, user_id: int) -> str:
        """Генерирует Refresh Token со сроком жизни 30 дней."""
        expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)
        to_encode = {"sub": str(user_id), "type": "refresh", "exp": expire}
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str, token_type: str) -> int | None:
        """Проверяет токен и возвращает user_id, если токен валиден."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            if payload.get("type") != token_type:
                return None
            user_id = payload.get("sub")
            if user_id is None:
                return None
            return int(user_id)
        except jwt.PyJWTError:
            return None
