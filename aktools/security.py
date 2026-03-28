# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2026/3/28 13:05
Desc: 请求 token 安全校验
"""
import ipaddress
import secrets

from fastapi import HTTPException, Request, status

from aktools.config import get_request_security_settings

_LOCAL_HOSTS = {"127.0.0.1", "::1", "localhost", "testclient"}
QUERY_TOKEN_NAME = "aktools_token"


def _normalize_host(host: str | None) -> str:
    """
    规范化 host，移除可能出现的端口信息
    """

    if not host:
        return ""
    normalized = host.strip()
    if normalized.startswith("[") and "]" in normalized:
        normalized = normalized[1:normalized.index("]")]
    elif normalized.count(":") == 1 and "." in normalized.split(":")[0]:
        normalized = normalized.rsplit(":", maxsplit=1)[0]
    if normalized.startswith("::ffff:"):
        normalized = normalized.replace("::ffff:", "", 1)
    return normalized


def get_request_host(request: Request) -> str:
    """
    获取真实请求来源，按配置决定是否信任代理头
    """

    settings = get_request_security_settings()
    if settings.trust_proxy_headers:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return _normalize_host(forwarded_for.split(",")[0])
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return _normalize_host(real_ip)
    client = request.client.host if request.client else ""
    return _normalize_host(client)


def is_local_request(request: Request) -> bool:
    """
    判断请求是否来自本机回环地址
    """

    host = get_request_host(request)
    if host in _LOCAL_HOSTS:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def is_local_bind_host(host: str) -> bool:
    """
    判断监听地址是否仅对本机开放
    """

    normalized_host = _normalize_host(host)
    if normalized_host in {"0.0.0.0", "::"}:
        return False
    if normalized_host in _LOCAL_HOSTS:
        return True
    try:
        return ipaddress.ip_address(normalized_host).is_loopback
    except ValueError:
        return False


def extract_request_token(
    request: Request,
    token_header_name: str,
) -> str:
    """
    从自定义请求头或查询参数中提取 token
    """

    header_token = request.headers.get(token_header_name)
    if header_token:
        return header_token.strip()
    query_token = request.query_params.get(QUERY_TOKEN_NAME)
    if query_token:
        return query_token.strip()
    return ""


def verify_request_token(
    request: Request,
) -> None:
    """
    统一的请求 token 校验逻辑
    """

    settings = get_request_security_settings()
    expected_token = settings.api_token.strip()
    provided_token = extract_request_token(
        request=request,
        token_header_name=settings.token_header_name,
    )
    if expected_token:
        if provided_token and secrets.compare_digest(provided_token, expected_token):
            return
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "请求 token 校验失败，请通过 "
                f"{settings.token_header_name}: <token> 或 {QUERY_TOKEN_NAME} 查询参数访问接口"
            ),
        )
    if is_local_request(request):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            "当前服务未配置 AKTOOLS_API_TOKEN，仅允许本机访问 API。"
            "如需远程访问，请先配置 AKTOOLS_API_TOKEN 后再发起请求"
        ),
    )
