"""
认证模块测试
============
验证用户认证相关逻辑。
"""

from boguan.api.auth import _hash_pwd, verify_token, _active_tokens


def test_hash_pwd_deterministic():
    """同一密码哈希结果应一致。"""
    assert _hash_pwd("test123") == _hash_pwd("test123")


def test_hash_pwd_different():
    """不同密码哈希结果应不同。"""
    assert _hash_pwd("abc") != _hash_pwd("xyz")


def test_verify_token_missing():
    """不存在的 token 应返回 None。"""
    assert verify_token("nonexistent-token") is None


def test_verify_token_valid():
    """已注册的 token 应返回用户信息。"""
    test_token = "test-token-12345"
    user_info = {"username": "admin", "role": "admin"}
    _active_tokens[test_token] = user_info
    try:
        result = verify_token(test_token)
        assert result is not None
        assert result["username"] == "admin"
    finally:
        _active_tokens.pop(test_token, None)
