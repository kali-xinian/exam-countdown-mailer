#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
系统验证脚本 - 检查所有配置是否正确
"""

import os
import sys
from datetime import datetime

def verify_system():
    """验证系统配置"""
    print("🔍 开始验证考研倒计时邮件系统配置...")
    print("=" * 60)
    
    issues = []
    
    # 1. 检查文件存在性
    print("📁 检查必要文件...")
    required_files = [
        'exam_countdown.py',
        'requirements.txt',
        'debug_config.py',
        'test_error_notification.py',
        '.github/workflows/exam-countdown.yml',
        'README.md'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - 文件缺失")
            issues.append(f"缺少文件: {file}")
    
    # 2. 检查GitHub Actions配置
    print("\n⚙️ 检查GitHub Actions配置...")
    try:
        with open('.github/workflows/exam-countdown.yml', 'r', encoding='utf-8') as f:
            workflow_content = f.read()
            
        if "cron: '0 0 * * *'" in workflow_content:
            print("  ✅ 定时任务配置正确 (每天UTC 0点 = 北京时间8点)")
        else:
            print("  ❌ 定时任务配置错误")
            issues.append("GitHub Actions定时任务配置错误")
            
        if "DEEPSEEK_API_KEY" in workflow_content and "EMAIL_PASSWORD" in workflow_content:
            print("  ✅ 环境变量配置正确")
        else:
            print("  ❌ 环境变量配置缺失")
            issues.append("GitHub Actions环境变量配置缺失")
            
    except Exception as e:
        print(f"  ❌ 无法读取工作流配置: {e}")
        issues.append(f"无法读取GitHub Actions配置: {e}")
    
    # 3. 检查邮件配置
    print("\n📧 检查邮件配置...")
    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from exam_countdown import DEFAULT_CONFIG
        
        recipient = DEFAULT_CONFIG.get("EMAIL_RECIPIENT")
        sender = DEFAULT_CONFIG.get("EMAIL_USER")
        
        if recipient == "1801169454@qq.com":
            print(f"  ✅ 收件人配置正确: {recipient} (盼盼的邮箱)")
        else:
            print(f"  ⚠️ 收件人配置: {recipient} (请确认是否正确)")
            
        if sender == "1969365257@qq.com":
            print(f"  ✅ 发件人配置正确: {sender}")
        else:
            print(f"  ❌ 发件人配置错误: {sender}")
            issues.append(f"发件人配置错误: {sender}")
            
    except Exception as e:
        print(f"  ❌ 无法读取邮件配置: {e}")
        issues.append(f"无法读取邮件配置: {e}")
    
    # 4. 检查考研日期
    print("\n📅 检查考研日期配置...")
    try:
        from exam_countdown import EXAM_DATE
        
        if EXAM_DATE.year == 2025 and EXAM_DATE.month == 12 and EXAM_DATE.day == 21:
            days_left = (EXAM_DATE - datetime.now()).days
            print(f"  ✅ 考研日期配置正确: {EXAM_DATE.strftime('%Y年%m月%d日')}")
            print(f"  📊 距离考研还有: {days_left} 天")
        else:
            print(f"  ❌ 考研日期配置错误: {EXAM_DATE}")
            issues.append(f"考研日期配置错误: {EXAM_DATE}")
            
    except Exception as e:
        print(f"  ❌ 无法读取考研日期: {e}")
        issues.append(f"无法读取考研日期: {e}")
    
    # 5. 检查错误通知配置
    print("\n🚨 检查错误通知配置...")
    try:
        with open('exam_countdown.py', 'r', encoding='utf-8') as f:
            code_content = f.read()
            
        if 'send_error_notification' in code_content:
            print("  ✅ 错误通知功能已实现")
        else:
            print("  ❌ 错误通知功能缺失")
            issues.append("错误通知功能缺失")
            
        if 'recipient = "1969365257@qq.com"' in code_content:
            print("  ✅ 错误通知收件人配置正确 (您的邮箱)")
        else:
            print("  ❌ 错误通知收件人配置错误")
            issues.append("错误通知收件人配置错误")
            
    except Exception as e:
        print(f"  ❌ 无法检查错误通知配置: {e}")
        issues.append(f"无法检查错误通知配置: {e}")
    
    # 总结
    print("\n" + "=" * 60)
    if not issues:
        print("🎉 系统验证完成 - 所有配置正确！")
        print("\n📋 系统配置摘要:")
        print("  • 每天早上8点准时发送邮件给盼盼")
        print("  • 发送失败时立即通知您的邮箱")
        print("  • 包含详细日志和处理建议")
        print("  • 自动重试机制确保可靠性")
        print("\n✅ 系统已准备就绪，明天早上8点将自动发送邮件！")
        return True
    else:
        print("❌ 系统验证发现问题:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        print("\n🔧 请修复上述问题后重新验证")
        return False

if __name__ == "__main__":
    success = verify_system()
    sys.exit(0 if success else 1)
