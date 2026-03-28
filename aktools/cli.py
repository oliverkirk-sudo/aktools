# -*- coding:utf-8 -*-
# !/usr/bin/env python
"""
Date: 2022/9/27 19:05
Desc: CLI 命令文件
"""
import os
import sys
from pathlib import Path
from subprocess import run
from typing import Optional

import akshare as ak
import typer

import aktools
from aktools.config import get_request_security_settings
from aktools.security import is_local_bind_host

app = typer.Typer()


def version_callback(value: bool):
    if value:
        typer.echo(f"{aktools.__title__} v{aktools.__version__}")
        raise typer.Exit()


@app.command()
def main(
    host: str = typer.Option("127.0.0.1", "--host", "-H", help="设置主机地址"),
    port: int = typer.Option(
        8080, "--port", "-P", min=0, max=65535, clamp=True, help="设置端口"
    ),
    auto: bool = typer.Option(False, "--auto", "-A", help="自动打开游览器，默认为不打开"),
    token: Optional[str] = typer.Option(
        None,
        "--token",
        envvar="AKTOOLS_API_TOKEN",
        help="设置 API 请求 token；也可以通过环境变量 AKTOOLS_API_TOKEN 配置",
    ),
    token_header: Optional[str] = typer.Option(
        None,
        "--token-header",
        envvar="AKTOOLS_TOKEN_HEADER",
        help="设置自定义 token 请求头名称；也可以通过环境变量 AKTOOLS_TOKEN_HEADER 配置",
    ),
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="查看 AKTools 的版本",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    if token is not None:
        os.environ["AKTOOLS_API_TOKEN"] = token
    if token_header is not None:
        os.environ["AKTOOLS_TOKEN_HEADER"] = token_header
    get_request_security_settings.cache_clear()
    security_settings = get_request_security_settings()
    app_dir = Path(__file__).parent
    order_str = (
        f"{sys.executable} -m uvicorn main:app --host {host} --port {port} --app-dir {app_dir}"
    )
    typer.echo(
        f"请访问：http://{host}:{port}/version 来获取最新的库版本信息，确保使用最新版本的 AKShare 和 AKTools"
    )
    typer.echo(f"当前的 AKTools 版本为：{aktools.__version__}，AKShare 版本为：{ak.__version__}")
    typer.echo(f"点击打开 HTTP API 主页：http://{host}:{port}/")
    typer.echo(f"点击打开接口导览：http://{host}:{port}/docs")
    if security_settings.api_token.strip():
        typer.echo(
            "请求 token 验证已启用，请在请求头中携带 "
            f"`{security_settings.token_header_name}: <token>`"
        )
    elif is_local_bind_host(host):
        typer.echo("当前未配置请求 token，本机访问 `/api` 无需额外鉴权")
    else:
        typer.echo(
            "当前未配置请求 token，远程访问 `/api` 将被拒绝。"
            "如需远程访问，请通过 `--token` 或环境变量 `AKTOOLS_API_TOKEN` 开启鉴权"
        )
    if auto:
        typer.launch(f"http://{host}:{port}/")
    run(order_str, shell=True)


if __name__ == "__main__":
    typer.run(main)
