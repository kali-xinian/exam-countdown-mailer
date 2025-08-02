#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试错误通知功能的脚本
"""

import os
import sys
import logging
import traceback

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入项目模块
try:
    from exam_countdown import ExamCountdownSystem, send_error_notification
except Exception as e:
    print(f"导入模块失败: {e}")
    sys.exit(1)

def test_error_notification():
    """测试错误通知功能"""
    print("开始测试错误通知功能...")
    
    try:
        # 初始化系统
        system = ExamCountdownSystem()
        print("系统初始化成功")
        
        # 模拟邮件发送失败的错误
        test_error = Exception("测试邮件发送失败 - 这是一个模拟的错误")
        test_traceback = """Traceback (most recent call last):
  File "exam_countdown.py", line 361, in main
    email_success = system.send_email(subject="每日考研倒计时")
  File "exam_countdown.py", line 181, in send_email
    return self.send_email_with_content(countdown, encouragement, subject)
  File "exam_countdown.py", line 298, in send_email_with_content
    server.send_message(msg)
Exception: 测试邮件发送失败 - 这是一个模拟的错误"""
        
        print("模拟错误已创建，准备发送错误通知邮件...")
        
        # 发送错误通知
        try:
            send_error_notification(system, test_error, test_traceback)
            print("✅ 错误通知邮件发送完成")
            return True
        except Exception as notification_error:
            print(f"❌ 发送错误通知失败: {notification_error}")
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("考研倒计时系统 - 错误通知功能测试")
    print("=" * 50)
    
    success = test_error_notification()
    
    print("=" * 50)
    if success:
        print("✅ 测试成功完成 - 错误通知功能正常")
        print("请检查您的邮箱 (1969365257@qq.com) 是否收到错误通知邮件")
        sys.exit(0)
    else:
        print("❌ 测试失败 - 错误通知功能异常")
        sys.exit(1)
