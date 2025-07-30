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
from datetime import datetime
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
    "EMAIL_RECIPIENT": "2802033546@qq.com",
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
            system_prompt = """你的任务是为昊昊起草一条给女友盼盼的每天鼓励语。请仔细阅读以下信息，并按照指示撰写。
距离考研的天数:
<days_left>
DAYS_LEFT
</days_left>
鼓励语内容可围绕给盼盼加油打气、表达支持等方面，总字数约200字，一段话呈现，不要分段。
在撰写鼓励语时，请遵循以下指南:
1. 开头为"亲爱的盼盼，距离考研还有DAYS_LEFT天啦，"。
2. 内容要真诚、温暖，能起到鼓励的作用。
3. 结尾为"—— 爱你的昊昊"，并居右对齐。
请在<encouragement>标签内写下你的鼓励语。"""
            
            # 用户提示词
            user_prompt = f"请为我生成距离考研还有{days}天的鼓励语"
            
            # 调用DeepSeek API
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
{encouragement}
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

    # 发送每日邮件
    logger.info("准备发送每日邮件...")

    try:
        # 显示倒计时信息
        countdown = system.calculate_countdown()
        if countdown:
            logger.info(f"距离考研还有 {countdown['days']} 天")
        else:
            logger.error("无法计算倒计时")
            return

        # 发送每日邮件（send_email方法内部会生成鼓励语）
        logger.info("正在发送邮件...")
        if system.send_email(subject="每日考研倒计时"):
            logger.info("邮件发送成功")
            print("邮件发送成功")
        else:
            logger.error("邮件发送失败")
            print("邮件发送失败")

    except Exception as e:
        logger.error(f"邮件发送过程中发生错误: {e}")
        logger.error(traceback.format_exc())
        print(f"邮件发送失败: {e}")
        return  # 发生错误时退出

    logger.info("程序执行完成")
    print("程序执行完成")


if __name__ == "__main__":
    main()