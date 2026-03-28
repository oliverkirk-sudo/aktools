# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2022/10/2 20:20
Desc: 配置文件
此处需要配置为 SQLite 数据库
"""
from functools import lru_cache
import logging

from dotenv import load_dotenv

try:
    from pydantic_settings import BaseSettings
    from pydantic import Field
except ImportError:
    try:
        from pydantic.v1 import BaseSettings, Field
    except ImportError:
        from pydantic import BaseSettings, Field

load_dotenv()

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    filename='../log/msscore.log',
                    filemode='a+')

log = logging.getLogger("uvicorn")


class Settings(BaseSettings):
    """
    数据库配置模型类
    """
    env_name: str = "Local"

    class Config:
        env_file = "../.env"


class AuthSettings(Settings):
    """
    授权配置类
    """
    secret_key: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30


class RequestSecuritySettings(Settings):
    """
    请求安全配置类
    """

    api_token: str = Field(default="", env="AKTOOLS_API_TOKEN")
    token_header_name: str = Field(default="X-AKTOOLS-TOKEN", env="AKTOOLS_TOKEN_HEADER")
    trust_proxy_headers: bool = Field(default=False, env="AKTOOLS_TRUST_PROXY_HEADERS")


class LocalSettings(Settings):
    mysql_db: str = "score"
    mysql_user: str = "root"
    mysql_passwd: str = "king"
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306


class ServerSettings(Settings):
    env_name: str = "Server"
    base_url: str = "1.1.1.1:8000"
    db_url: str = "mysql+pymysql://root@king"

    class Config:
        env_file = "../.env"


@lru_cache
def get_local_settings() -> Settings:
    settings = LocalSettings()
    log.info(f"Loading local settings for: {settings.env_name}")
    return settings


@lru_cache()
def get_auth_settings() -> Settings:
    settings = AuthSettings()
    log.info(f"加载授权环境变量成功")
    return settings


@lru_cache()
def get_request_security_settings() -> Settings:
    settings = RequestSecuritySettings()
    log.info("加载请求 token 配置成功")
    return settings
