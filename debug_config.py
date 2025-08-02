#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
调试配置脚本 - 检查环境变量和配置
"""

import os
import sys
from datetime import datetime

def check_environment():
    """检查环境变量配置"""
    print("=== 环境变量检查 ===")
    
    # 检查关键环境变量
    env_vars = [
        "DEEPSEEK_API_KEY",
        "EMAIL_PASSWORD",
        "EMAIL_USER",
        "EMAIL_RECIPIENT"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # 隐藏敏感信息
            if "KEY" in var or "PASSWORD" in var:
                masked_value = value[:4] + "*" * (len(value) - 8) + value[-4:] if len(value) > 8 else "*" * len(value)
                print(f"✅ {var}: {masked_value}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: 未设置")
    
    print("\n=== 时间信息 ===")
    now = datetime.now()
    print(f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"时区信息: {now.astimezone().tzinfo}")
    
    print("\n=== 系统信息 ===")
    print(f"Python版本: {sys.version}")
    print(f"操作系统: {os.name}")
    
    # 检查是否在GitHub Actions环境中
    if os.getenv("GITHUB_ACTIONS"):
        print("✅ 运行在GitHub Actions环境中")
        print(f"GitHub仓库: {os.getenv('GITHUB_REPOSITORY', '未知')}")
        print(f"GitHub事件: {os.getenv('GITHUB_EVENT_NAME', '未知')}")
    else:
        print("ℹ️ 运行在本地环境中")

if __name__ == "__main__":
    check_environment()
