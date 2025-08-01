#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
考研倒计时邮件发送系统（无界面版本）
- 计算考研倒计时
- 调用DeepSeek API生成鼓励语
- 发送包含倒计时和鼓励语的邮件
"""

import os
import sys
import logging
import traceback
import time
# datetime用于处理日期和时间计算
from datetime import datetime, timedelta
# 用于创建邮件内容
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# 用于发送邮件
import smtplib
import ssl
# 用于调用DeepSeek API
from openai import OpenAI
# 用于解析命令行参数
import argparse

# 设置日志配置
LOG_DIR = './log'
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'exam_countdown.log'), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('exam_countdown')

# 默认配置
DEFAULT_CONFIG = {
    # DeepSeek大模型API配置
    "DEEPSEEK_API_KEY": "sk-c30056b032634329b3264541d3aa9593",
    "DEEPSEEK_API_BASE_URL": "https://api.deepseek.com",
    "DEEPSEEK_MODEL": "deepseek-chat",

    # 邮件配置 - QQ邮箱SMTP配置
    "EMAIL_HOST": "smtp.qq.com",
    "EMAIL_PORT_SSL": 465,  # SSL端口
    "EMAIL_PORT_TLS": 587,  # TLS端口
    "EMAIL_USER": "1969365257@qq.com",
    "EMAIL_PASSWORD": "rxjizuniwsukfaef",
    "EMAIL_RECIPIENT": "1801169454@qq.com",
    # 测试邮箱
    # "EMAIL_RECIPIENT": "1969365257@qq.com",
    "EMAIL_CONNECTION_TYPE": "SSL",  # SSL或TLS
}

# 考研日期（2025年12月21日）
EXAM_DATE = datetime(2025, 12, 21, 0, 0, 0)


class ExamCountdownSystem:
    """考研倒计时系统主类"""
    
    def __init__(self):
        """初始化系统配置和API客户端"""
        # 优先使用环境变量中的配置，否则使用默认配置
        self.config = {
            "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY", DEFAULT_CONFIG["DEEPSEEK_API_KEY"]),
            "DEEPSEEK_API_BASE_URL": os.getenv("DEEPSEEK_API_BASE_URL", DEFAULT_CONFIG["DEEPSEEK_API_BASE_URL"]),
            "DEEPSEEK_MODEL": os.getenv("DEEPSEEK_MODEL", DEFAULT_CONFIG["DEEPSEEK_MODEL"]),
            "EMAIL_HOST": os.getenv("EMAIL_HOST", DEFAULT_CONFIG["EMAIL_HOST"]),
            "EMAIL_PORT_SSL": int(os.getenv("EMAIL_PORT_SSL", DEFAULT_CONFIG["EMAIL_PORT_SSL"])),
            "EMAIL_PORT_TLS": int(os.getenv("EMAIL_PORT_TLS", DEFAULT_CONFIG["EMAIL_PORT_TLS"])),
            "EMAIL_USER": os.getenv("EMAIL_USER", DEFAULT_CONFIG["EMAIL_USER"]),
            "EMAIL_PASSWORD": os.getenv("EMAIL_PASSWORD", DEFAULT_CONFIG["EMAIL_PASSWORD"]),
            "EMAIL_RECIPIENT": os.getenv("EMAIL_RECIPIENT", DEFAULT_CONFIG["EMAIL_RECIPIENT"]),
            "EMAIL_CONNECTION_TYPE": os.getenv("EMAIL_CONNECTION_TYPE", DEFAULT_CONFIG["EMAIL_CONNECTION_TYPE"]),
        }
        
        # 记录关键配置信息（不记录密码）
        logger.info(f"邮件配置: 收件人={self.config['EMAIL_RECIPIENT']}, 服务器={self.config['EMAIL_HOST']}")
        
        # 初始化DeepSeek API客户端
        self.client = OpenAI(
            api_key=self.config["DEEPSEEK_API_KEY"],
            base_url=self.config["DEEPSEEK_API_BASE_URL"]
        )

        # 新增倒计时缓存，提高性能
        self._cached_countdown = None
        
    def calculate_countdown(self):
        """计算考研倒计时"""
        try:
            # 如果已有缓存且当前时间未超过考试时间，直接返回缓存结果
            now = datetime.now()
            if self._cached_countdown is not None and now < EXAM_DATE:
                return self._cached_countdown
            
            now = datetime.now()
            time_diff = EXAM_DATE - now
            
            if time_diff.total_seconds() > 0:
                days = time_diff.days
                hours, remainder = divmod(time_diff.seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                self._cached_countdown = {
                    "days": days,
                    "hours": hours,
                    "minutes": minutes,
                    "seconds": seconds
                }
                return self._cached_countdown
            else:
                self._cached_countdown = None
                return None
        except Exception as e:
            logger.error(f"计算倒计时失败: {e}")
            return None

    def generate_encouragement(self):
        """调用DeepSeek API生成完整的邮件正文内容"""
        try:
            countdown = self.calculate_countdown()
            if not countdown:
                return "考研时间已到！"
            
            days = countdown["days"]
            
            # 系统提示词，定义AI助手的角色和生成内容的要求
            system_prompt = """你是一个温柔体贴的男朋友，正在给自己的女朋友(盼盼)写考研倒计时鼓励邮件。你的任务是根据考研剩余天数生成一段完整的邮件正文内容，帮助她保持积极心态。请遵循以下要求：
1. 语气要温柔、关爱、亲密，像男朋友在安慰女朋友一样
2. 内容要真诚，避免过于正式或官方的语言
3. 可以适当引用一些励志名言或诗句，但要自然融入对话中，避免重复使用相同名言
4. 不要包含任何负面或消极的内容
5. 输出格式为纯文本，不要使用任何Markdown或HTML标记
6. 内容应该包含对她努力的认可和对她能力的信任
7. 可以提醒她注意休息，表达你对她的支持
8. 不要使用"考研人"这样的称呼，应该用更亲密的称呼如"盼盼"
9. 生成的内容必须在250字以内
10. 只生成一段连贯的内容，不要分段
11. 内容要简洁有力，表达真挚情感
12. 生成完整的邮件正文内容，包含开头称呼，但不包含结尾署名
13. 开头使用"亲爱的盼盼，距离考研还有{天数}天啦，"的格式
14. 不要包含"—— 爱你的昊昊"，这个会在邮件模板中添加
15. 不要在内容中重复盼盼的名字
16. 避免重复使用相同或类似的名言，如泰戈尔的"天空没有翅膀的痕迹"等常见名句
17. 尽量每天生成不同的鼓励内容，可以提及她的进步、努力或者未来的美好"""
            
            # 用户提示词，提供具体信息给AI
            user_prompt = f"请生成一封考研倒计时鼓励邮件的正文内容，考研还剩{days}天，开头使用'亲爱的盼盼，距离考研还有{days}天啦，'，内容要连贯自然，不要包含结尾署名，不要重复盼盼的名字，避免使用过于常见的名言。"
            
            # 调用DeepSeek API生成完整的邮件正文
            response = self.client.chat.completions.create(
                model=self.config["DEEPSEEK_MODEL"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=250,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"生成鼓励语失败: {e}")
            logger.error(traceback.format_exc())
            return None

    def send_email(self, subject="考研倒计时"):
        """发送邮件"""
        try:
            # 获取倒计时和鼓励语
            countdown = self.calculate_countdown()
            encouragement = self.generate_encouragement()
            
            return self.send_email_with_content(countdown, encouragement, subject)
        except Exception as e:
            logger.error(f"发送邮件过程中发生致命错误: {e}")
            logger.error(traceback.format_exc())
            return False
            
    def send_email_with_content(self, countdown, encouragement, subject="考研倒计时"):
        """使用已生成的内容发送邮件"""
        try:
            # 检查必要内容是否存在
            if not countdown or not encouragement:
                logger.error("缺少倒计时或鼓励语，无法发送邮件")
                return False
            
            # 获取邮件配置
            host = self.config["EMAIL_HOST"]
            user = self.config["EMAIL_USER"]
            password = self.config["EMAIL_PASSWORD"]
            recipient = self.config["EMAIL_RECIPIENT"]
            connection_type = self.config["EMAIL_CONNECTION_TYPE"]
            
            # 已在初始化时记录过配置信息，避免重复日志
            
            # 根据连接类型选择端口
            if connection_type.upper() == "SSL":
                port = self.config["EMAIL_PORT_SSL"]
            else:
                port = self.config["EMAIL_PORT_TLS"]
            
            # 构建HTML邮件内容，使用AI生成的完整内容
            html_content = f"""
            <html>
            <body style="font-family: 'Microsoft YaHei', sans-serif; background: linear-gradient(135deg, #87CEEB 0%, #98D8E8 100%); padding: 20px; margin: 0;">
                <div style="max-width: 600px; margin: 40px auto; background: white; border-radius: 15px; padding: 0; box-shadow: 0 10px 30px rgba(0,0,0,0.15);">
                    <!-- 头部区域 -->
                    <div style="background: linear-gradient(135deg, #87CEEB 0%, #4682B4 100%); color: white; padding: 30px; text-align: center; border-radius: 15px 15px 0 0;">
                        <h1 style="margin: 0; font-size: 28px; font-weight: bold;">📚 考研倒计时</h1>
                        <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">距离梦想实现还有</p>
                    </div>
                    
                    <!-- 倒计时数字 -->
                    <div style="text-align: center; padding: 30px 20px;">
                        <div style="display: inline-block; position: relative;">
                            <!-- 翻页日历效果的倒计时 -->
                            <div style="background: linear-gradient(135deg, #87CEEB, #4682B4); border-radius: 12px; padding: 20px 30px; box-shadow: 0 8px 20px rgba(0,0,0,0.2); display: inline-block; position: relative; overflow: hidden;">
                                <div style="position: relative; z-index: 2;">
                                    <div style="font-size: 64px; font-weight: bold; color: white; text-shadow: 0 2px 4px rgba(0,0,0,0.3);">{countdown['days']}</div>
                                    <div style="font-size: 20px; color: rgba(255,255,255,0.9); font-weight: bold; margin-top: 5px;">天</div>
                                </div>
                                <!-- 装饰性元素，模拟翻页效果 -->
                                <div style="position: absolute; top: 0; left: 0; width: 100%; height: 50%; background: rgba(255,255,255,0.1); border-radius: 12px 12px 0 0;"></div>
                                <div style="position: absolute; top: 50%; left: 0; width: 100%; height: 50%; background: rgba(0,0,0,0.05); border-radius: 0 0 12px 12px;"></div>
                            </div>
                        </div>
                        <!-- 时间单位说明 -->
                        <div style="display: flex; justify-content: center; gap: 20px; margin-top: 20px; flex-wrap: wrap;">
                            <div style="background: #e6f3ff; padding: 10px 15px; border-radius: 8px; min-width: 80px;">
                                <div style="font-size: 24px; font-weight: bold; color: #4682B4;">{countdown['hours']}</div>
                                <div style="font-size: 14px; color: #666;">小时</div>
                            </div>
                            <div style="background: #e6f3ff; padding: 10px 15px; border-radius: 8px; min-width: 80px;">
                                <div style="font-size: 24px; font-weight: bold; color: #4682B4;">{countdown['minutes']}</div>
                                <div style="font-size: 14px; color: #666;">分钟</div>
                            </div>
                            <div style="background: #e6f3ff; padding: 10px 15px; border-radius: 8px; min-width: 80px;">
                                <div style="font-size: 24px; font-weight: bold; color: #4682B4;">{countdown['seconds']}</div>
                                <div style="font-size: 14px; color: #666;">秒</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- 鼓励语 -->
                    <div style="padding: 0 30px 30px 30px;">
                        <div style="background: #f0f8ff; padding: 25px; border-radius: 12px; margin-bottom: 25px; border-left: 4px solid #87CEEB;">
                            <div style="font-size: 16px; color: #333; line-height: 1.7; white-space: pre-line;">
{encouragement}
<div style="text-align: right; margin-top: 15px; font-weight: bold; color: #4682B4;">—— 爱你的昊昊</div>
                            </div>
                        </div>
                        
                        <!-- 温馨提示 -->
                        <div style="text-align: center; color: #666; font-size: 14px; padding: 15px; background: #e6f3ff; border-radius: 8px;">
                            <p style="margin: 0;">💡 加油！你的每一份努力都在为未来铺路</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # 创建邮件对象
            msg = MIMEMultipart()
            msg['From'] = user
            msg['To'] = recipient
            msg['Subject'] = f"{subject} - 距离考研还有 {countdown['days']} 天"
            
            # 添加HTML内容
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            # 发送邮件
            try:
                # 根据连接类型选择端口
                if connection_type.upper() == "SSL":
                    # SSL连接
                    context = ssl.create_default_context()
                    server = smtplib.SMTP_SSL(host, port, context=context)
                else:
                    # TLS连接
                    server = smtplib.SMTP(host, port)
                    server.starttls(context=ssl.create_default_context())
                
                # 登录并发送邮件
                server.login(user, password)
                server.send_message(msg)
                server.quit()
                
                logger.info(f"邮件发送成功: 发件人={user}, 收件人={recipient}")
                return True
                
            except Exception as e:
                logger.error(f"邮件发送失败: {e}")
                logger.error(traceback.format_exc())
                
                # 如果SSL连接失败，尝试TLS连接作为备用方案
                try:
                    logger.info("尝试备用连接方式...")
                    if connection_type.upper() == "SSL":
                        # 如果之前是SSL，现在尝试TLS
                        server = smtplib.SMTP(host, self.config["EMAIL_PORT_TLS"])
                        server.starttls(context=ssl.create_default_context())
                    else:
                        # 如果之前是TLS，现在尝试SSL
                        context = ssl.create_default_context()
                        server = smtplib.SMTP_SSL(host, self.config["EMAIL_PORT_SSL"], context=context)
                    
                    server.login(user, password)
                    server.send_message(msg)
                    server.quit()
                    
                    logger.info(f"使用备用连接方式邮件发送成功: 发件人={user}, 收件人={recipient}")
                    return True
                    
                except Exception as backup_e:
                    logger.error(f"备用连接方式也失败了: {backup_e}")
                    logger.error(traceback.format_exc())
                    return False
                    
        except Exception as e:
            logger.error(f"发送邮件过程中发生致命错误: {e}")
            logger.error(traceback.format_exc())
            return False


def main():
    """主函数"""
    system = ExamCountdownSystem()
    
    # 显示启动信息
    logger.info("考研倒计时邮件系统已启动...")
    
    # 重试次数计数器
    retry_count = 0
    max_retries = 3  # 最大重试次数
    
    # 显示倒计时信息并发送邮件
    while retry_count < max_retries:
        try:
            # 显示倒计时信息
            countdown = system.calculate_countdown()
            if countdown:
                logger.info(f"距离考研还有 {countdown['days']} 天")
            else:
                logger.error("无法计算倒计时")
                # 如果考研时间已过，退出程序
                logger.info("考研时间已过，程序退出")
                print("考研时间已过，程序退出")
                return

            # 发送每日邮件（在发送时生成最新的倒计时和鼓励语）
            logger.info("正在发送邮件...")
            if system.send_email(subject="每日考研倒计时"):
                logger.info("邮件发送成功")
                print("邮件发送成功")
            else:
                logger.error("邮件发送失败")
                print("邮件发送失败")

            logger.info("程序执行完成")
            print("程序执行完成")
            
            # 每天执行一次即可，成功发送邮件后退出
            return
            
        except Exception as e:
            retry_count += 1
            error_msg = f"发生错误: {e} (第 {retry_count} 次重试)"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            print(error_msg)
            
            # 发送错误通知邮件
            try:
                send_error_notification(system, e, traceback.format_exc())
            except Exception as notification_error:
                logger.error(f"发送错误通知邮件也失败了: {notification_error}")
            
            # 如果达到最大重试次数，则退出程序
            if retry_count >= max_retries:
                logger.error(f"已达到最大重试次数 ({max_retries})，程序退出")
                print(f"已达到最大重试次数 ({max_retries})，程序退出")
                return
            
            # 等待一段时间后重试，使用指数退避算法
            wait_time = min(3600 * (2 ** (retry_count - 1)), 3600)  # 最多等待1小时
            logger.info(f"等待 {wait_time} 秒后进行第 {retry_count + 1} 次重试...")
            time.sleep(wait_time)


def send_error_notification(system, error, traceback_info):
    """发送错误通知邮件给开发者"""
    try:
        # 邮件配置使用系统配置
        host = system.config["EMAIL_HOST"]
        user = system.config["EMAIL_USER"]
        password = system.config["EMAIL_PASSWORD"]
        recipient = "1969365257@qq.com"  # 错误通知发送给开发者
        connection_type = system.config["EMAIL_CONNECTION_TYPE"]
        
        # 端口选择
        if connection_type.upper() == "SSL":
            port = system.config["EMAIL_PORT_SSL"]
        else:
            port = system.config["EMAIL_PORT_TLS"]
        
        # 构建错误通知邮件内容
        subject = "考研倒计时系统错误通知"
        html_content = f"""
        <html>
        <body style="font-family: 'Microsoft YaHei', sans-serif; background: linear-gradient(135deg, #ff6b6b 0%, #ff5252 100%); padding: 20px; margin: 0;">
            <div style="max-width: 600px; margin: 40px auto; background: white; border-radius: 15px; padding: 0; box-shadow: 0 10px 30px rgba(0,0,0,0.15);">
                <!-- 头部区域 -->
                <div style="background: linear-gradient(135deg, #ff6b6b 0%, #ff5252 100%); color: white; padding: 30px; text-align: center; border-radius: 15px 15px 0 0;">
                    <h1 style="margin: 0; font-size: 28px; font-weight: bold;">❌ 系统错误通知</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">考研倒计时邮件系统出现问题</p>
                </div>
                
                <div style="padding: 30px;">
                    <div style="background: #fff5f5; padding: 20px; border-radius: 10px; border-left: 4px solid #ff6b6b; margin-bottom: 20px;">
                        <h2 style="color: #ff5252; margin-top: 0;">错误摘要</h2>
                        <p style="color: #333; font-size: 16px; line-height: 1.6;"><strong>错误信息:</strong> {str(error)}</p>
                        <p style="color: #333; font-size: 16px; line-height: 1.6;"><strong>发生时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <p style="color: #333; font-size: 16px; line-height: 1.6;"><strong>系统环境:</strong> GitHub Actions</p>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                        <h2 style="color: #4682B4; margin-top: 0;">详细错误信息</h2>
                        <pre style="background: #2d3748; color: #fff; padding: 15px; border-radius: 8px; overflow-x: auto; font-size: 14px; line-height: 1.5;">{traceback_info}</pre>
                    </div>
                    
                    <div style="text-align: center; color: #666; font-size: 14px; padding: 15px; background: #fff8e6; border-radius: 8px;">
                        <p style="margin: 0;">🔧 请及时检查并修复问题，确保系统正常运行</p>
                        <p style="margin: 5px 0 0 0; font-size: 12px;">此通知来自 GitHub Actions 自动化任务</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        # 创建邮件对象
        msg = MIMEMultipart()
        msg['From'] = user
        msg['To'] = recipient
        msg['Subject'] = subject
        
        # 添加HTML内容
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        
        # 发送邮件
        try:
            # 根据连接类型选择端口
            if connection_type.upper() == "SSL":
                # SSL连接
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(host, port, context=context)
            else:
                # TLS连接
                server = smtplib.SMTP(host, port)
                server.starttls(context=ssl.create_default_context())
            
            # 登录并发送邮件
            server.login(user, password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"错误通知邮件发送成功: 发件人={user}, 收件人={recipient}")
            
        except Exception as e:
            logger.error(f"错误通知邮件发送失败: {e}")
            # 如果SSL连接失败，尝试TLS连接作为备用方案
            try:
                logger.info("尝试备用连接方式发送错误通知...")
                if connection_type.upper() == "SSL":
                    # 如果之前是SSL，现在尝试TLS
                    server = smtplib.SMTP(host, system.config["EMAIL_PORT_TLS"])
                    server.starttls(context=ssl.create_default_context())
                else:
                    # 如果之前是TLS，现在尝试SSL
                    context = ssl.create_default_context()
                    server = smtplib.SMTP_SSL(host, system.config["EMAIL_PORT_SSL"], context=context)
                
                server.login(user, password)
                server.send_message(msg)
                server.quit()
                
                logger.info(f"使用备用连接方式错误通知邮件发送成功: 发件人={user}, 收件人={recipient}")
                
            except Exception as backup_e:
                logger.error(f"备用连接方式发送错误通知也失败了: {backup_e}")
                raise
                
    except Exception as e:
        logger.error(f"发送错误通知过程中发生致命错误: {e}")
        raise


if __name__ == "__main__":
    main()