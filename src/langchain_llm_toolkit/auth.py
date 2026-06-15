import os
import secrets
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel


class TokenData(BaseModel):
    """Token 数据"""

    user_id: str
    username: str
    scopes: list[str] = []
    expires_at: str | None = None


class APIKeyData(BaseModel):
    """API Key 数据"""

    key_id: str
    user_id: str
    name: str
    scopes: list[str] = []
    created_at: str
    last_used_at: str | None = None
    is_active: bool = True


@dataclass
class User:
    """用户数据"""

    id: str
    username: str
    email: str
    hashed_password: str
    is_active: bool = True
    created_at: str = ""
    scopes: list[str] = None

    def __post_init__(self):
        if self.scopes is None:
            self.scopes = []


class AuthStore:
    """认证数据存储"""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or os.environ.get("AUTH_DB_PATH", "./data/auth.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL,
                    scopes TEXT DEFAULT '[]'
                )
            """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS api_keys (
                    key_id TEXT PRIMARY KEY,
                    key_hash TEXT UNIQUE NOT NULL,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    scopes TEXT DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    last_used_at TEXT,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tokens (
                    token_id TEXT PRIMARY KEY,
                    token_hash TEXT UNIQUE NOT NULL,
                    user_id TEXT NOT NULL,
                    scopes TEXT DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """
            )
            conn.commit()

    def save_user(self, user: User) -> bool:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO users
                (id, username, email, hashed_password, is_active, created_at, scopes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user.id,
                    user.username,
                    user.email,
                    user.hashed_password,
                    1 if user.is_active else 0,
                    user.created_at,
                    str(user.scopes),
                ),
            )
            conn.commit()
        return True

    def get_user(self, user_id: str) -> User | None:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            if row:
                return self._row_to_user(row)
        return None

    def get_user_by_username(self, username: str) -> User | None:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            if row:
                return self._row_to_user(row)
        return None

    def _row_to_user(self, row) -> User:
        import ast

        return User(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            hashed_password=row["hashed_password"],
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            scopes=ast.literal_eval(row["scopes"]) if row["scopes"] else [],
        )

    def save_api_key(
        self,
        key_id: str,
        key_hash: str,
        user_id: str,
        name: str,
        scopes: list[str],
    ) -> bool:
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO api_keys
                (key_id, key_hash, user_id, name, scopes, created_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """,
                (
                    key_id,
                    key_hash,
                    user_id,
                    name,
                    str(scopes),
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()
        return True

    def get_api_key_by_hash(self, key_hash: str) -> dict[str, Any] | None:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM api_keys WHERE key_hash = ? AND is_active = 1",
                (key_hash,),
            ).fetchone()
            if row:
                import ast

                return {
                    "key_id": row["key_id"],
                    "user_id": row["user_id"],
                    "name": row["name"],
                    "scopes": ast.literal_eval(row["scopes"]) if row["scopes"] else [],
                    "created_at": row["created_at"],
                    "last_used_at": row["last_used_at"],
                }
        return None

    def update_api_key_last_used(self, key_id: str):
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE api_keys SET last_used_at = ? WHERE key_id = ?",
                (datetime.now().isoformat(), key_id),
            )
            conn.commit()

    def list_api_keys(self, user_id: str) -> list[dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT key_id, name, scopes, created_at, last_used_at "
                "FROM api_keys WHERE user_id = ? AND is_active = 1",
                (user_id,),
            ).fetchall()
            import ast

            return [
                {
                    "key_id": row["key_id"],
                    "name": row["name"],
                    "scopes": ast.literal_eval(row["scopes"]) if row["scopes"] else [],
                    "created_at": row["created_at"],
                    "last_used_at": row["last_used_at"],
                }
                for row in rows
            ]

    def revoke_api_key(self, key_id: str) -> bool:
        with self._get_connection() as conn:
            conn.execute("UPDATE api_keys SET is_active = 0 WHERE key_id = ?", (key_id,))
            conn.commit()
        return True


class JWTHandler:
    """JWT Token 处理器"""

    def __init__(
        self,
        secret_key: str | None = None,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
    ):
        self.secret_key = secret_key or os.environ.get("JWT_SECRET_KEY", secrets.token_urlsafe(32))
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes

    def create_token(
        self,
        user_id: str,
        username: str,
        scopes: list[str] | None = None,
        expires_delta: timedelta | None = None,
    ) -> str:
        import jwt

        if scopes is None:
            scopes = []

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        payload = {
            "sub": user_id,
            "username": username,
            "scopes": scopes,
            "exp": expire,
            "iat": datetime.utcnow(),
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> TokenData:
        import jwt
        from jwt import ExpiredSignatureError, InvalidTokenError

        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            expires_at = None
            if payload.get("exp"):
                expires_at = datetime.fromtimestamp(payload.get("exp")).isoformat()
            return TokenData(
                user_id=payload.get("sub"),
                username=payload.get("username"),
                scopes=payload.get("scopes", []),
                expires_at=expires_at,
            )
        except ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token 已过期") from None
        except InvalidTokenError:
            raise HTTPException(status_code=401, detail="无效的 Token") from None


class PasswordHandler:
    """密码处理器"""

    @staticmethod
    def hash_password(password: str) -> str:
        import hashlib

        salt = secrets.token_hex(16)
        hash_value = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000).hex()
        return f"{salt}:{hash_value}"

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        import hashlib

        try:
            salt, hash_value = hashed_password.split(":")
            new_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000).hex()
            return new_hash == hash_value
        except ValueError:
            return False


class AuthManager:
    """认证管理器"""

    def __init__(
        self,
        store: AuthStore | None = None,
        jwt_handler: JWTHandler | None = None,
    ):
        self.store = store or AuthStore()
        self.jwt_handler = jwt_handler or JWTHandler()
        self.password_handler = PasswordHandler()

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        scopes: list[str] | None = None,
    ) -> User:
        import uuid

        if self.store.get_user_by_username(username):
            raise ValueError(f"用户名已存在: {username}")

        user = User(
            id=str(uuid.uuid4()),
            username=username,
            email=email,
            hashed_password=self.password_handler.hash_password(password),
            is_active=True,
            created_at=datetime.now().isoformat(),
            scopes=scopes or [],
        )

        self.store.save_user(user)
        return user

    def authenticate_user(self, username: str, password: str) -> User | None:
        user = self.store.get_user_by_username(username)
        if not user:
            return None
        if not user.is_active:
            return None
        if not self.password_handler.verify_password(password, user.hashed_password):
            return None
        return user

    def create_access_token(self, user: User) -> str:
        return self.jwt_handler.create_token(
            user_id=user.id,
            username=user.username,
            scopes=user.scopes,
        )

    def create_api_key(
        self,
        user_id: str,
        name: str,
        scopes: list[str] | None = None,
    ) -> str:
        import hashlib
        import uuid

        api_key = f"lk-{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key_id = str(uuid.uuid4())

        self.store.save_api_key(
            key_id=key_id,
            key_hash=key_hash,
            user_id=user_id,
            name=name,
            scopes=scopes or [],
        )

        return api_key

    def validate_api_key(self, api_key: str) -> dict[str, Any] | None:
        import hashlib

        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key_data = self.store.get_api_key_by_hash(key_hash)

        if key_data:
            self.store.update_api_key_last_used(key_data["key_id"])

        return key_data


security = HTTPBearer()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    api_key: str = Security(api_key_header),
) -> TokenData:
    """获取当前用户（支持 JWT、API Key 和 INTERNAL_API_KEY）"""
    internal_key = os.environ.get("INTERNAL_API_KEY")

    token = None
    if credentials:
        token = credentials.credentials
    elif api_key:
        token = api_key

    if token and internal_key and token == internal_key:
        return TokenData(user_id="internal", username="internal", scopes=["*"])

    if token:
        auth_manager = AuthManager()
        if credentials:
            try:
                return auth_manager.jwt_handler.decode_token(token)
            except HTTPException:
                pass
        if api_key:
            key_data = auth_manager.validate_api_key(token)
            if key_data:
                user = auth_manager.store.get_user(key_data["user_id"])
                if user:
                    return TokenData(
                        user_id=user.id,
                        username=user.username,
                        scopes=key_data.get("scopes", []),
                    )

    raise HTTPException(
        status_code=401,
        detail="未提供有效的认证信息",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_scopes(required_scopes: list[str]):
    """检查用户是否具有所需权限"""

    def decorator(current_user: TokenData = Depends(get_current_user)):
        user_scopes = set(current_user.scopes)
        required = set(required_scopes)

        if not required.issubset(user_scopes):
            missing = required - user_scopes
            raise HTTPException(status_code=403, detail=f"缺少权限: {', '.join(missing)}")
        return current_user

    return decorator
