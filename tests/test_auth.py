import os
import tempfile
from datetime import timedelta

import pytest

from langchain_llm_toolkit.auth import (
    AuthManager,
    AuthStore,
    JWTHandler,
    PasswordHandler,
    TokenData,
)


class TestPasswordHandler:
    """测试密码处理器"""

    def test_hash_password(self):
        """测试密码哈希"""
        password = "test_password_123"
        hashed = PasswordHandler.hash_password(password)

        assert hashed != password
        assert ":" in hashed
        assert len(hashed) > len(password)

    def test_verify_password_correct(self):
        """测试验证正确密码"""
        password = "correct_password"
        hashed = PasswordHandler.hash_password(password)

        assert PasswordHandler.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """测试验证错误密码"""
        password = "correct_password"
        hashed = PasswordHandler.hash_password(password)

        assert PasswordHandler.verify_password("wrong_password", hashed) is False

    def test_different_passwords_different_hashes(self):
        """测试不同密码产生不同哈希"""
        password = "same_password"
        hash1 = PasswordHandler.hash_password(password)
        hash2 = PasswordHandler.hash_password(password)

        assert hash1 != hash2

    def test_verify_invalid_hash_format(self):
        """测试无效哈希格式"""
        assert PasswordHandler.verify_password("password", "invalid_hash") is False


@pytest.mark.filterwarnings("ignore::jwt.warnings.InsecureKeyLengthWarning")
class TestJWTHandler:
    """测试 JWT 处理器"""

    @pytest.fixture
    def jwt_handler(self):
        return JWTHandler(secret_key="test_secret_key_for_testing")

    def test_create_token(self, jwt_handler):
        """测试创建 Token"""
        token = jwt_handler.create_token(
            user_id="user-123",
            username="testuser",
        )

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_token(self, jwt_handler):
        """测试解码 Token"""
        token = jwt_handler.create_token(
            user_id="user-123",
            username="testuser",
            scopes=["read", "write"],
        )

        token_data = jwt_handler.decode_token(token)

        assert token_data.user_id == "user-123"
        assert token_data.username == "testuser"
        assert "read" in token_data.scopes
        assert "write" in token_data.scopes

    def test_token_with_custom_expiry(self, jwt_handler):
        """测试自定义过期时间"""
        token = jwt_handler.create_token(
            user_id="user-123",
            username="testuser",
            expires_delta=timedelta(hours=1),
        )

        token_data = jwt_handler.decode_token(token)
        assert token_data.expires_at is not None

    def test_different_secrets(self):
        """测试不同密钥"""
        handler1 = JWTHandler(secret_key="secret1")
        handler2 = JWTHandler(secret_key="secret2")

        token = handler1.create_token("user-1", "user1")

        with pytest.raises(Exception):
            handler2.decode_token(token)


class TestAuthStore:
    """测试认证存储"""

    @pytest.fixture
    def temp_db(self):
        """创建临时数据库"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        yield db_path
        os.unlink(db_path)

    @pytest.fixture
    def auth_store(self, temp_db):
        return AuthStore(db_path=temp_db)

    def test_save_user(self, auth_store):
        """测试保存用户"""
        from langchain_llm_toolkit.auth import User

        user = User(
            id="user-1",
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            is_active=True,
            created_at="2024-01-01T00:00:00",
            scopes=["read"],
        )

        result = auth_store.save_user(user)
        assert result is True

    def test_get_user(self, auth_store):
        """测试获取用户"""
        from langchain_llm_toolkit.auth import User

        user = User(
            id="user-1",
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            created_at="2024-01-01T00:00:00",
        )
        auth_store.save_user(user)

        retrieved = auth_store.get_user("user-1")

        assert retrieved is not None
        assert retrieved.username == "testuser"

    def test_get_user_by_username(self, auth_store):
        """测试通过用户名获取用户"""
        from langchain_llm_toolkit.auth import User

        user = User(
            id="user-1",
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            created_at="2024-01-01T00:00:00",
        )
        auth_store.save_user(user)

        retrieved = auth_store.get_user_by_username("testuser")

        assert retrieved is not None
        assert retrieved.id == "user-1"

    def test_get_nonexistent_user(self, auth_store):
        """测试获取不存在的用户"""
        user = auth_store.get_user("nonexistent")
        assert user is None

    def test_save_api_key(self, auth_store):
        """测试保存 API Key"""
        result = auth_store.save_api_key(
            key_id="key-1",
            key_hash="hash123",
            user_id="user-1",
            name="Test Key",
            scopes=["read"],
        )
        assert result is True

    def test_get_api_key_by_hash(self, auth_store):
        """测试获取 API Key"""
        auth_store.save_api_key(
            key_id="key-1",
            key_hash="hash123",
            user_id="user-1",
            name="Test Key",
            scopes=["read"],
        )

        key_data = auth_store.get_api_key_by_hash("hash123")

        assert key_data is not None
        assert key_data["key_id"] == "key-1"
        assert key_data["name"] == "Test Key"

    def test_list_api_keys(self, auth_store):
        """测试列出 API Keys"""
        auth_store.save_api_key(
            key_id="key-1",
            key_hash="hash1",
            user_id="user-1",
            name="Key 1",
            scopes=[],
        )
        auth_store.save_api_key(
            key_id="key-2",
            key_hash="hash2",
            user_id="user-1",
            name="Key 2",
            scopes=[],
        )

        keys = auth_store.list_api_keys("user-1")

        assert len(keys) == 2

    def test_revoke_api_key(self, auth_store):
        """测试撤销 API Key"""
        auth_store.save_api_key(
            key_id="key-1",
            key_hash="hash1",
            user_id="user-1",
            name="Key 1",
            scopes=[],
        )

        auth_store.revoke_api_key("key-1")

        key_data = auth_store.get_api_key_by_hash("hash1")
        assert key_data is None


@pytest.mark.filterwarnings("ignore::jwt.warnings.InsecureKeyLengthWarning")
class TestAuthManager:
    """测试认证管理器"""

    @pytest.fixture
    def temp_db(self):
        """创建临时数据库"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        yield db_path
        os.unlink(db_path)

    @pytest.fixture
    def auth_manager(self, temp_db):
        store = AuthStore(db_path=temp_db)
        jwt_handler = JWTHandler(secret_key="test_secret")
        return AuthManager(store=store, jwt_handler=jwt_handler)

    def test_create_user(self, auth_manager):
        """测试创建用户"""
        user = auth_manager.create_user(
            username="newuser",
            email="new@example.com",
            password="password123",
        )

        assert user.id is not None
        assert user.username == "newuser"
        assert user.email == "new@example.com"
        assert user.hashed_password != "password123"

    def test_create_duplicate_user(self, auth_manager):
        """测试创建重复用户"""
        auth_manager.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
        )

        with pytest.raises(ValueError):
            auth_manager.create_user(
                username="testuser",
                email="another@example.com",
                password="password123",
            )

    def test_authenticate_user_success(self, auth_manager):
        """测试认证成功"""
        auth_manager.create_user(
            username="testuser",
            email="test@example.com",
            password="correct_password",
        )

        user = auth_manager.authenticate_user("testuser", "correct_password")

        assert user is not None
        assert user.username == "testuser"

    def test_authenticate_user_wrong_password(self, auth_manager):
        """测试密码错误"""
        auth_manager.create_user(
            username="testuser",
            email="test@example.com",
            password="correct_password",
        )

        user = auth_manager.authenticate_user("testuser", "wrong_password")

        assert user is None

    def test_authenticate_nonexistent_user(self, auth_manager):
        """测试认证不存在的用户"""
        user = auth_manager.authenticate_user("nonexistent", "password")
        assert user is None

    def test_create_access_token(self, auth_manager):
        """测试创建访问令牌"""
        from langchain_llm_toolkit.auth import User

        user = User(
            id="user-1",
            username="testuser",
            email="test@example.com",
            hashed_password="hashed",
            scopes=["read"],
        )

        token = auth_manager.create_access_token(user)

        assert token is not None
        assert isinstance(token, str)

    def test_create_api_key(self, auth_manager):
        """测试创建 API Key"""
        user = auth_manager.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
        )

        api_key = auth_manager.create_api_key(user.id, "Test Key")

        assert api_key is not None
        assert api_key.startswith("lk-")

    def test_validate_api_key(self, auth_manager):
        """测试验证 API Key"""
        user = auth_manager.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
        )
        api_key = auth_manager.create_api_key(user.id, "Test Key")

        key_data = auth_manager.validate_api_key(api_key)

        assert key_data is not None
        assert key_data["user_id"] == user.id

    def test_validate_invalid_api_key(self, auth_manager):
        """测试验证无效 API Key"""
        key_data = auth_manager.validate_api_key("lk-invalid_key")
        assert key_data is None


class TestTokenData:
    """测试 Token 数据"""

    def test_create_token_data(self):
        """测试创建 Token 数据"""
        data = TokenData(
            user_id="user-1",
            username="testuser",
            scopes=["read", "write"],
        )

        assert data.user_id == "user-1"
        assert data.username == "testuser"
        assert len(data.scopes) == 2

    def test_token_data_default_scopes(self):
        """测试默认权限"""
        data = TokenData(
            user_id="user-1",
            username="testuser",
        )

        assert data.scopes == []
