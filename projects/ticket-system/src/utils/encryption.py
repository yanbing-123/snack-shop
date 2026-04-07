"""
加密工具模块
"""
from cryptography.fernet import Fernet
from src.config.settings import settings
import base64
import hashlib


def get_encryption_key() -> bytes:
    """获取加密密钥"""
    # 将配置的密钥转换为适合 Fernet 的格式
    key = settings.ENCRYPTION_KEY.encode('utf-8')
    # 使用 SHA256 生成 32 字节密钥
    key = hashlib.sha256(key).digest()
    # Base64 编码
    return base64.urlsafe_b64encode(key)


def encrypt_password(password: str) -> str:
    """加密密码"""
    f = Fernet(get_encryption_key())
    encrypted = f.encrypt(password.encode('utf-8'))
    return encrypted.decode('utf-8')


def decrypt_password(encrypted_password: str) -> str:
    """解密密码"""
    f = Fernet(get_encryption_key())
    decrypted = f.decrypt(encrypted_password.encode('utf-8'))
    return decrypted.decode('utf-8')


def hash_data(data: str) -> str:
    """哈希数据（不可逆）"""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()
