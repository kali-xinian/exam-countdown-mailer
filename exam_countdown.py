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
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl
from openai import OpenAI

# 设置日志
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
    "EMAIL_CONNECTION_TYPE": "SSL",  # SSL或TLS
}

# 考研日期（2025年12月21日）
EXAM_DATE = datetime(2025, 12, 21, 0, 0, 0)


class ExamCountdownSystem:
    def __init__(self):
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

        # 新增倒计时缓存
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
        """调用DeepSeek API生成鼓励语"""
        try:
            countdown = self.calculate_countdown()
            if not countdown:
                return "考研时间已到！"
            
            days = countdown["days"]
            
            # 系统提示词
            system_prompt = """你是一个温柔体贴的男朋友，正在给自己的女朋友(盼盼)写考研倒计时鼓励信息。你的任务是根据考研剩余天数生成一段鼓励语，帮助她保持积极心态。请遵循以下要求：
1. 语气要温柔、关爱、亲密，像男朋友在安慰女朋友一样
2. 内容要真诚，避免过于正式或官方的语言
3. 可以适当引用一些励志名言或诗句，但要自然融入对话中
4. 不要包含任何负面或消极的内容
5. 输出格式为纯文本，不要使用任何Markdown或HTML标记
6. 内容应该包含对她努力的认可和对她能力的信任
7. 可以提醒她注意休息，表达你对她的支持
8. 不要使用"考研人"这样的称呼，应该用更亲密的称呼如"盼盼"
9. 生成的内容必须在200字以内
10. 只生成一段连贯的内容，不要分段
11. 不要在开头重复"盼盼"或者"还有XX天"等与邮件开头重复的内容
12. 内容要简洁有力，表达真挚情感"""
            
            # 用户提示词
            user_prompt = f"考研还剩{days}天，请生成一段200字以内的鼓励语，不要在开头重复盼盼的名字或天数。"
            
            # 调用DeepSeek API
            response = self.client.chat.completions.create(
                model=self.config["DEEPSEEK_MODEL"],
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=200,
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
            
            # 构建HTML邮件内容
            html_content = f"""
            <html>
            <body style="font-family: 'Microsoft YaHei', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 10px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2);">
                    <h2 style="color: #333; text-align: center; margin-bottom: 30px;">📚 考研倒计时</h2>
                    
                    <div style="text-align: center; margin-bottom: 30px;">
                        <div style="font-size: 48px; font-weight: bold; color: #667eea; margin-bottom: 10px;">{countdown['days']}</div>
                        <div style="font-size: 18px; color: #666;">天</div>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px;">
                        <div style="font-size: 16px; color: #333; line-height: 1.6; white-space: pre-line;">
亲爱的盼盼，距离考研还有{countdown['days']}天啦，
{encouragement}

<div style="text-align: right;">—— 爱你的昊昊</div>
                        </div>
                    </div>
                    
                    <div style="text-align: center; color: #999; font-size: 14px;">
                        <p>加油！你的努力终将成就更好的自己！</p>
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

    # 等待到早上8点
    wait_until_8am()
    
    # 显示倒计时信息并发送邮件
    while True:
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
            logger.error(f"发生错误: {e}")
            logger.error(traceback.format_exc())
            print(f"发生错误: {e}")
            
            # 等待一段时间后重试
            logger.info("等待1小时后重试...")
            time.sleep(3600)  # 等待1小时


def wait_until_8am():
    """等待到当天早上8点"""
    now = datetime.now()
    next_8am = now.replace(hour=8, minute=0, second=0, microsecond=0)
    
    # 如果当前时间已经过了今天的8点，则等待明天的8点
    if now >= next_8am:
        next_8am += timedelta(days=1)
    
    # 计算需要等待的时间
    wait_seconds = (next_8am - now).total_seconds()
    
    if wait_seconds > 0:
        logger.info(f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"等待到: {next_8am.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"需要等待 {wait_seconds} 秒")
        
        # 如果需要等待的时间超过1小时，记录警告信息
        if wait_seconds > 3600:
            logger.warning(f"等待时间较长 ({wait_seconds/3600:.1f} 小时)，请确认系统时间设置正确")
        
        # 分批等待，避免长时间阻塞
        while wait_seconds > 0:
            # 每次最多等待1分钟
            sleep_time = min(wait_seconds, 60)
            time.sleep(sleep_time)
            wait_seconds -= sleep_time
            
            # 更新当前时间和剩余等待时间
            now = datetime.now()
            wait_seconds = (next_8am - now).total_seconds()
            
            # 每10分钟记录一次等待状态
            if int(wait_seconds) % 600 == 0 or wait_seconds < 60:
                logger.info(f"仍在等待中...预计还需要 {wait_seconds:.0f} 秒")

    logger.info("已到达指定时间，开始执行任务")


if __name__ == "__main__":
    main()