"""安全模块测试。

测试 AES 加密解密和数据脱敏功能：
- encrypt_data/decrypt_data 测试
- encrypt_dict/decrypt_dict 测试
- mask_phone/mask_email 测试
"""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.core.security import (
    decrypt_data,
    decrypt_dict,
    encrypt_data,
    encrypt_dict,
    mask_email,
    mask_phone,
)


# ==================== encrypt_data 测试 ====================

class TestEncryptData:
    """encrypt_data 函数测试类。"""

    def test_encrypt_simple_string(self, mock_settings: MagicMock) -> None:
        """测试加密简单字符串。"""
        with patch("src.core.security.get_settings", return_value=mock_settings):
            encrypted = encrypt_data("hello world")

            assert isinstance(encrypted, str)
            assert len(encrypted) > 0
            assert encrypted != "hello world"

    def test_encrypt_chinese_string(self, mock_settings: MagicMock) -> None:
        """测试加密中文字符串。"""
        with patch("src.core.security.get_settings", return_value=mock_settings):
            encrypted = encrypt_data("张三")

            assert isinstance(encrypted, str)
            assert len(encrypted) > 0
            assert encrypted != "张三"

    def test_encrypt_phone_number(self, mock_settings: MagicMock) -> None:
        """测试加密手机号。"""
        with patch("src.core.security.get_settings", return_value=mock_settings):
            encrypted = encrypt_data("13800138000")

            assert isinstance(encrypted, str)
            assert len(encrypted) > 0
            assert encrypted != "13800138000"

    def test_encrypt_email(self, mock_settings: MagicMock) -> None:
        """测试加密邮箱。"""
        with patch("src.core.security.get_settings", return_value=mock_settings):
            encrypted = encrypt_data("zhangsan@example.com")

            assert isinstance(encrypted, str)
            assert len(encrypted) > 0
            assert encrypted != "zhangsan@example.com"

    def test_encrypt_empty_string(self, mock_settings: MagicMock) -> None:
        """测试加密空字符串。"""
        with patch("src.core.security.get_settings", return_value=mock_settings):
            encrypted = encrypt_data("")

            assert encrypted == ""

    def test_encrypt_long_string(self, mock_settings: MagicMock) -> None:
        """测试加密长字符串。"""
        with patch("src.core.security.get_settings", return_value=mock_settings):
            long_text = "a" * 10000
            encrypted = encrypt_data(long_text)

            assert isinstance(encrypted, str)
            assert len(encrypted) > 0

    def test_encrypt_special_characters(self, mock_settings: MagicMock) -> None:
        """测试加密特殊字符。"""
        with patch("src.core.security.get_settings", return_value=mock_settings):
            special_chars = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
            encrypted = encrypt_data(special_chars)

            assert isinstance(encrypted, str)
            assert len(encrypted) > 0


# ==================== decrypt_data 测试 ====================

class TestDecryptData:
    """decrypt_data 函数测试类。"""

    def test_decrypt_simple_string(self, mock_settings: MagicMock) -> None:
        """测试解密简单字符串。"""
        with patch("src.core.security.get_settings", return_value=mock_settings):
            original = "hello world"
            encrypted = encrypt_data(original)
            decrypted = decrypt_data(encrypted)

            assert decrypted == original

    def test_decrypt_chinese_string(self, mock_settings: MagicMock) -> None:
        """测试解密中文字符串。"""
        with patch("src.core.security.get_settings", return_value=mock_settings):
            original = "张三"
            encrypted = encrypt_data(original)
            decrypted = decrypt_data(encrypted)

            assert decrypted == original

    def test_decrypt_phone_number(self, mock_settings: MagicMock) -> None:
        """测试解密手机号。"""
        with patch("src.core.security.get_settings", return_value=mock_settings):
            original = "13800138000"
            encrypted = encrypt_data(original)
            decrypted = decrypt_data(encrypted)

            assert decrypted == original

    def test_decrypt_email(self, mock_settings: MagicMock) -> None:
        """测试解密邮箱。"""
        with patch("src.core.security.get_settings", return_value=mock_settings):
            original = "zhangsan@example.com"
            encrypted = encrypt_data(original)
            decrypted = decrypt_data(encrypted)

            assert decrypted == original

    def test_decrypt_empty_string(self, mock_settings: MagicMock) -> None:
        """测试解密空字符串。"""
        with patch("src.core.security.get_settings", return_value=mock_settings):
            decrypted = decrypt_data("")

            assert decrypted == ""

    def test_decrypt_invalid_data(self, mock_settings: MagicMock) -> None:
        """测试解密无效数据。"""
        with patch("src.core.security.get_settings", return_value=mock_settings):
            with pytest.raises(ValueError):
                decrypt_data("invalid_encrypted_data")

    def test_decrypt_non_base64_data(self, mock_settings: MagicMock) -> None:
        """测试解密非 Base64 数据。"""
        with patch("src.core.security.get_settings", return_value=mock_settings):
            with pytest.raises(ValueError):
                decrypt_data("这不是加密数据")


# ==================== encrypt_dict 测试 ====================

class TestEncryptDict:
    """encrypt_dict 函数测试类。"""

    def test_encrypt_dict_single_field(self, mock_settings: MagicMock) -> None:
        """测试加密字典单个字段。"""
        with patch("src.core.security.get_settings", return_value=mock_settings):
            data = {"name": "张三", "phone": "13800138000"}
            result = encrypt_dict(data, ["phone"])

            assert result["name"] == "张三"
            assert result["phone"] != "13800138000"

    def test_encrypt_dict_multiple_fields(self, mock_settings: MagicMock) -> None:
        """测试加密字典多个字段。"""
        with patch("src.core.security.get_settings", return_value=mock_settings):
            data = {
                "name": "张三",
                "phone": "13800138000",
                "email": "zhangsan@example.com",
            }
            result = encrypt_dict(data, ["phone", "email"])

            assert result["name"] == "张三"
            assert result["phone"] != "13800138000"
            assert result["email"] != "zhangsan@example.com"

    def test_encrypt_dict_empty_fields(self, mock_settings: MagicMock) -> None:
        """测试加密字典空字段列表。"""
        with patch("src.core.security.get_settings", return_value=mock_settings):
            data = {"name": "张三", "phone": "13800138000"}
            result = encrypt_dict(data, [])

            assert result["name"] == "张三"
            assert result["phone"] == "13800138000"

    def test_encrypt_dict_missing_field(self, mock_settings: MagicMock) -> None:
        """测试加密字典中不存在的字段。"""
        with patch("src.core.security.get_settings", return_value=mock_settings):
            data = {"name": "张三"}
            result = encrypt_dict(data, ["phone"])

            assert result["name"] == "张三"
            assert "phone" not in result

    def test_encrypt_dict_empty_value(self, mock_settings: MagicMock) -> None:
        """测试加密字典中空值字段。"""
        with patch("src.core.security.get_settings", return_value=mock_settings):
            data = {"name": "张三", "phone": ""}
            result = encrypt_dict(data, ["phone"])

            assert result["phone"] == ""

    def test_encrypt_dict_preserves_original(self, mock_settings: MagicMock) -> None:
        """测试加密字典保留原始数据。"""
        with patch("src.core.security.get_settings", return_value=mock_settings):
            data = {"name": "张三", "phone": "13800138000"}
            result = encrypt_dict(data, ["phone"])

            # 原始数据应该不变
            assert data["phone"] == "13800138000"
            # 返回的数据应该是加密的
            assert result["phone"] != "13800138000"


# ==================== decrypt_dict 测试 ====================

class TestDecryptDict:
    """decrypt_dict 函数测试类。"""

    def test_decrypt_dict_single_field(self, mock_settings: MagicMock) -> None:
        """测试解密字典单个字段。"""
        with patch("src.core.security.get_settings", return_value=mock_settings):
            original_phone = "13800138000"
            encrypted_phone = encrypt_data(original_phone)
            data = {"name": "张三", "phone": encrypted_phone}
            result = decrypt_dict(data, ["phone"])

            assert result["name"] == "张三"
            assert result["phone"] == original_phone

    def test_decrypt_dict_multiple_fields(self, mock_settings: MagicMock) -> None:
        """测试解密字典多个字段。"""
        with patch("src.core.security.get_settings", return_value=mock_settings):
            original_phone = "13800138000"
            original_email = "zhangsan@example.com"
            data = {
                "name": "张三",
                "phone": encrypt_data(original_phone),
                "email": encrypt_data(original_email),
            }
            result = decrypt_dict(data, ["phone", "email"])

            assert result["name"] == "张三"
            assert result["phone"] == original_phone
            assert result["email"] == original_email

    def test_decrypt_dict_empty_fields(self, mock_settings: MagicMock) -> None:
        """测试解密字典空字段列表。"""
        with patch("src.core.security.get_settings", return_value=mock_settings):
            data = {"name": "张三", "phone": encrypt_data("13800138000")}
            result = decrypt_dict(data, [])

            assert result["phone"] != "13800138000"

    def test_decrypt_dict_missing_field(self, mock_settings: MagicMock) -> None:
        """测试解密字典中不存在的字段。"""
        with patch("src.core.security.get_settings", return_value=mock_settings):
            data = {"name": "张三"}
            result = decrypt_dict(data, ["phone"])

            assert result["name"] == "张三"
            assert "phone" not in result

    def test_decrypt_dict_invalid_encrypted_value(self, mock_settings: MagicMock) -> None:
        """测试解密字典中无效加密值。"""
        with patch("src.core.security.get_settings", return_value=mock_settings):
            data = {"name": "张三", "phone": "invalid_encrypted"}
            result = decrypt_dict(data, ["phone"])

            # 无效加密值应该保留原值
            assert result["phone"] == "invalid_encrypted"

    def test_decrypt_dict_preserves_original(self, mock_settings: MagicMock) -> None:
        """测试解密字典保留原始数据。"""
        with patch("src.core.security.get_settings", return_value=mock_settings):
            encrypted_phone = encrypt_data("13800138000")
            data = {"name": "张三", "phone": encrypted_phone}
            result = decrypt_dict(data, ["phone"])

            # 原始数据应该不变
            assert data["phone"] == encrypted_phone
            # 返回的数据应该是解密的
            assert result["phone"] == "13800138000"


# ==================== mask_phone 测试 ====================

class TestMaskPhone:
    """mask_phone 函数测试类。"""

    def test_mask_standard_phone(self) -> None:
        """测试脱敏标准手机号。"""
        result = mask_phone("13800138000")

        assert result == "138****8000"

    def test_mask_short_phone(self) -> None:
        """测试脱敏短手机号。"""
        result = mask_phone("123456")

        assert result == "123456"

    def test_mask_empty_phone(self) -> None:
        """测试脱敏空手机号。"""
        result = mask_phone("")

        assert result == ""

    def test_mask_none_phone(self) -> None:
        """测试脱敏 None 手机号。"""
        result = mask_phone(None)  # type: ignore

        assert result is None

    def test_mask_phone_with_country_code(self) -> None:
        """测试脱敏带国家代码的手机号。"""
        result = mask_phone("8613800138000")

        assert result == "861****8000"

    def test_mask_phone_exactly_7_chars(self) -> None:
        """测试脱敏恰好 7 位手机号。"""
        result = mask_phone("1234567")

        assert result == "123****4567"


# ==================== mask_email 测试 ====================

class TestMaskEmail:
    """mask_email 函数测试类。"""

    def test_mask_standard_email(self) -> None:
        """测试脱敏标准邮箱。"""
        result = mask_email("zhangsan@example.com")

        assert result == "z****n@example.com"

    def test_mask_short_username_email(self) -> None:
        """测试脱敏短用户名邮箱。"""
        result = mask_email("ab@example.com")

        assert result == "a***@example.com"

    def test_mask_single_char_username_email(self) -> None:
        """测试脱敏单字符用户名邮箱。"""
        result = mask_email("a@example.com")

        assert result == "a***@example.com"

    def test_mask_empty_email(self) -> None:
        """测试脱敏空邮箱。"""
        result = mask_email("")

        assert result == ""

    def test_mask_none_email(self) -> None:
        """测试脱敏 None 邮箱。"""
        result = mask_email(None)  # type: ignore

        assert result is None

    def test_mask_invalid_email_no_at(self) -> None:
        """测试脱敏无效邮箱（无 @ 符号）。"""
        result = mask_email("invalid-email")

        assert result == "invalid-email"

    def test_mask_email_with_subdomain(self) -> None:
        """测试脱敏带子域名的邮箱。"""
        result = mask_email("user@mail.example.com")

        assert "@mail.example.com" in result

    def test_mask_long_username_email(self) -> None:
        """测试脱敏长用户名邮箱。"""
        result = mask_email("verylongusername@example.com")

        assert result == "v****e@example.com"


# ==================== 边界情况测试 ====================

class TestEdgeCases:
    """边界情况测试类。"""

    def test_encrypt_decrypt_cycle(self, mock_settings: MagicMock) -> None:
        """测试加密解密循环。"""
        with patch("src.core.security.get_settings", return_value=mock_settings):
            test_cases = [
                "simple text",
                "中文文本",
                "13800138000",
                "test@example.com",
                "!@#$%^&*()",
                "a" * 1000,
                "混合 Mixed 内容 123 !@#",
            ]

            for original in test_cases:
                encrypted = encrypt_data(original)
                decrypted = decrypt_data(encrypted)
                assert decrypted == original, f"Failed for: {original}"

    def test_encrypt_different_values_produce_different_results(
        self, mock_settings: MagicMock
    ) -> None:
        """测试不同值产生不同加密结果。"""
        with patch("src.core.security.get_settings", return_value=mock_settings):
            encrypted1 = encrypt_data("value1")
            encrypted2 = encrypt_data("value2")

            assert encrypted1 != encrypted2

    def test_encrypt_same_value_produces_different_results(
        self, mock_settings: MagicMock
    ) -> None:
        """测试相同值产生不同加密结果（由于随机 IV）。"""
        with patch("src.core.security.get_settings", return_value=mock_settings):
            encrypted1 = encrypt_data("same_value")
            encrypted2 = encrypt_data("same_value")

            # Fernet 每次加密相同值会产生不同结果（由于时间戳）
            assert encrypted1 != encrypted2

    def test_dict_encrypt_decrypt_cycle(self, mock_settings: MagicMock) -> None:
        """测试字典加密解密循环。"""
        with patch("src.core.security.get_settings", return_value=mock_settings):
            original = {
                "name": "张三",
                "phone": "13800138000",
                "email": "zhangsan@example.com",
                "other": "其他数据",
            }

            encrypted = encrypt_dict(original, ["phone", "email"])
            decrypted = decrypt_dict(encrypted, ["phone", "email"])

            assert decrypted["name"] == original["name"]
            assert decrypted["phone"] == original["phone"]
            assert decrypted["email"] == original["email"]
            assert decrypted["other"] == original["other"]

    def test_unicode_handling(self, mock_settings: MagicMock) -> None:
        """测试 Unicode 字符处理。"""
        with patch("src.core.security.get_settings", return_value=mock_settings):
            unicode_strings = [
                "你好世界",
                "🎉🎊🎈",
                "日本語テスト",
                "한국어 테스트",
                "Привет мир",
            ]

            for original in unicode_strings:
                encrypted = encrypt_data(original)
                decrypted = decrypt_data(encrypted)
                assert decrypted == original

    def test_whitespace_handling(self, mock_settings: MagicMock) -> None:
        """测试空白字符处理。"""
        with patch("src.core.security.get_settings", return_value=mock_settings):
            whitespace_strings = [
                "  leading spaces",
                "trailing spaces  ",
                "  both sides  ",
                "\ttab\t",
                "\nnewline\n",
                " \t \n mixed \n \t ",
            ]

            for original in whitespace_strings:
                encrypted = encrypt_data(original)
                decrypted = decrypt_data(encrypted)
                assert decrypted == original
