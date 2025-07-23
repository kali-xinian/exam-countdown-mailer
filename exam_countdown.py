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
    # "EMAIL_RECIPIENT": "1801169454@qq.com",
    "EMAIL_RECIPIENT": "2698620537@qq.com",
    "EMAIL_CONNECTION_TYPE": "SSL",  # SSL或TLS

    # 考研日期
    "EXAM_YEAR": 2025,
    "EXAM_MONTH": 12,
    "EXAM_DAY": 21
}


class ExamCountdownSystem:
    def __init__(self, config=None):
        self.config = config if config else DEFAULT_CONFIG.copy()
        self.encouragement = ""

    def calculate_countdown(self):
        """计算距离考研的剩余时间"""
        try:
            exam_date = datetime(
                self.config["EXAM_YEAR"],
                self.config["EXAM_MONTH"],
                self.config["EXAM_DAY"]
            )
            now = datetime.now()
            delta = exam_date - now

            if delta.total_seconds() < 0:
                return {
                    "days": 0,
                    "hours": 0,
                    "minutes": 0,
                    "seconds": 0,
                    "total_seconds": delta.total_seconds()
                }

            days = delta.days
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            return {
                "days": days,
                "hours": hours,
                "minutes": minutes,
                "seconds": seconds,
                "total_seconds": delta.total_seconds()
            }
        except Exception as e:
            logger.error(f"计算倒计时出错: {e}")
            logger.error(traceback.format_exc())
            return None

    def generate_encouragement(self):
        """调用DeepSeek API生成鼓励语"""
        try:
            countdown = self.calculate_countdown()
            if not countdown or countdown["total_seconds"] < 0:
                logger.warning("考研日期已过，无法生成鼓励语")
                return "考研日期已过，恭喜你完成了这场战役！"

            days_left = countdown["days"]

            # 获取API配置
            api_key = self.config["DEEPSEEK_API_KEY"]
            api_base = self.config["DEEPSEEK_API_BASE_URL"]
            model = self.config["DEEPSEEK_MODEL"]

            if not api_key or not api_base or not model:
                logger.error("DeepSeek API配置不完整")
                return None

            # 初始化客户端
            client = OpenAI(
                base_url=api_base,
                api_key=api_key
            )

            # 构造提示词
            system_prompt = "你是盼盼的男朋友昊昊，用亲昵、温柔的语气写考研鼓励语，符合男朋友的身份。注意使用正确的中文标点符号，如逗号、句号、感叹号等，保持语言流畅自然。"
            user_prompt = f"""请以昊昊的口吻给盼盼写一段鼓励语，包含以下要点：
            1. 距离考研还有{days_left}天
            2. 称呼用"盼盼"或"亲爱的"
            3. 表达支持和信任，强调她的潜力
            4. 长度100-150字，不要在结尾署名，不要添加任何符号如"——"
            5. 请正确使用标点符号，不要省略标点，保持语言流畅自然
            直接输出鼓励语，不要多余内容。"""

            # 调用API
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,
                max_tokens=300
            )

            # 处理结果
            encouragement = response.choices[0].message.content.strip()
            encouragement = encouragement.replace("爱你的昊昊", "").replace("——", "").strip()
            self.encouragement = encouragement

            logger.info("鼓励语生成成功")
            return self.encouragement
        except Exception as e:
            logger.error(f"生成鼓励语出错: {e}")
            logger.error(traceback.format_exc())
            self.encouragement = None
            return None

    def send_email(self):
        """发送包含倒计时和鼓励语的邮件"""
        try:
            # 检查鼓励语
            if not self.encouragement:
                logger.warning("没有可用的鼓励语，尝试生成...")
                self.generate_encouragement()
                if not self.encouragement:
                    logger.error("无法生成鼓励语，邮件发送失败")
                    return False

            # 检查倒计时
            countdown = self.calculate_countdown()
            if not countdown:
                logger.error("无法计算倒计时，邮件发送失败")
                return False

            days_left = countdown["days"]
            countdown_text = f"距离考研还有 {days_left} 天 {countdown['hours']} 小时 {countdown['minutes']} 分 {countdown['seconds']} 秒"

            # 获取邮件配置
            email_host = self.config["EMAIL_HOST"]
            email_user = self.config["EMAIL_USER"]
            email_password = self.config["EMAIL_PASSWORD"]
            email_recipient = self.config["EMAIL_RECIPIENT"]
            connection_type = self.config["EMAIL_CONNECTION_TYPE"]

            # 根据连接类型选择端口
            if connection_type == "SSL":
                email_port = self.config["EMAIL_PORT_SSL"]
            else:  # TLS
                email_port = self.config["EMAIL_PORT_TLS"]

            if not all([email_host, email_user, email_password, email_recipient]):
                logger.error("邮件配置不完整")
                return False

            logger.info(f"尝试使用{connection_type}连接到{email_host}:{email_port}发送邮件")

            # 构建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"📚 考研倒计时：{days_left} 天！（测试邮件）"  # 测试邮件标题添加标识
            msg['From'] = email_user
            msg['To'] = email_recipient

            # HTML内容
            html_template = """
            <html>
            <head>
                <style>
                    body {{font-family: "Microsoft YaHei", Arial, sans-serif; line-height: 1.8; color: #ffffff; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #000000;}}
                    h1 {{color: #ffffff; text-align: center; font-size: 24px; margin-bottom: 25px; text-shadow: 0 0 10px rgba(30, 144, 255, 0.7);}}
                    .countdown {{font-size: 18px; color: #ffffff; border-top: 1px solid #1e90ff; border-bottom: 1px solid #1e90ff; padding: 10px 0; margin: 15px 0;}}
                    .encouragement {{color: #ffffff; padding: 10px 0; margin: 0; line-height: 1.8; text-indent: 1em;}}
                    .signature {{text-align: right; color: #ffffff; margin-top: 20px; font-style: italic;}}
                    .blue-bar {{
                        background: linear-gradient(to bottom, #00bfff, #1e90ff);
                        width: 5px;
                        height: 100%;
                        margin-right: 8px;
                        float: left;
                        border-radius: 3px;
                        box-shadow: 0 0 8px rgba(30, 144, 255, 0.8);
                    }}
                    .content {{margin-left: 0; flex: 1;}}
                    .message-container {{
                        background-color: rgba(30, 144, 255, 0.1);
                        border-radius: 10px;
                        padding: 20px;
                        margin-top: 15px;
                        box-shadow: 0 0 15px rgba(0, 0, 0, 0.5) inset, 0 0 5px rgba(30, 144, 255, 0.3);
                        border: 1px solid rgba(30, 144, 255, 0.2);
                    }}
                    .emoji {{font-size: 24px; margin-right: 5px;}}
                    .flex-container {{display: flex; align-items: stretch;}}
                    .test-note {{color: #ffff00; text-align: center; margin-bottom: 15px; font-weight: bold;}}
                </style>
            </head>
            <body>
                <div class="test-note">这是一封测试邮件，验证系统是否正常运行</div>
                <h1>📚 考研倒计时：{days_left} 天！</h1>
                <div class="message-container">
                    <div class="flex-container">
                        <div class="blue-bar"></div>
                        <div class="content">
                            <p class="encouragement">{encouragement}</p>
                            <p class="signature">—— 爱你的昊昊</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """

            # 替换换行符
            formatted_encouragement = self.encouragement.replace('\n', '<br>')

            # 使用format方法格式化HTML
            html_content = html_template.format(
                days_left=days_left,
                encouragement=formatted_encouragement
            )
            msg.attach(MIMEText(html_content, 'html'))

            # 发送邮件 - 优化连接处理逻辑
            sent_successfully = False

            # 首先尝试主要连接方式
            try:
                if connection_type == "SSL":
                    # 使用SSL连接
                    context = ssl.create_default_context()
                    server = smtplib.SMTP_SSL(email_host, email_port, context=context, timeout=10)
                    logger.info(f"已建立SSL连接到{email_host}:{email_port}")
                else:
                    # 使用TLS连接
                    server = smtplib.SMTP(email_host, email_port, timeout=10)
                    logger.info(f"已建立普通连接到{email_host}:{email_port}")
                    server.starttls(context=ssl.create_default_context())
                    logger.info("已升级为TLS加密连接")

                server.login(email_user, email_password)
                logger.info(f"已登录邮箱: {email_user}")
                server.sendmail(email_user, email_recipient, msg.as_string())
                logger.info(f"邮件发送成功，收件人: {email_recipient}")
                sent_successfully = True

                # 安全关闭连接
                try:
                    server.quit()
                except Exception as e:
                    logger.warning(f"关闭SMTP连接时出现非致命错误: {str(e)}")
                    # 忽略关闭连接时的错误，因为邮件已经成功发送

            except Exception as e:
                logger.error(f"{connection_type}连接发送失败: {str(e)}")

                # 如果第一种方式失败，尝试备用连接方式
                if not sent_successfully:
                    alternative_type = "TLS" if connection_type == "SSL" else "SSL"
                    alternative_port = self.config["EMAIL_PORT_TLS"] if connection_type == "SSL" else self.config[
                        "EMAIL_PORT_SSL"]
                    logger.info(f"尝试使用备用{alternative_type}连接方式...")

                    try:
                        if alternative_type == "SSL":
                            server = smtplib.SMTP_SSL(email_host, alternative_port,
                                                      context=ssl.create_default_context(), timeout=10)
                            logger.info(f"已建立备用SSL连接到{email_host}:{alternative_port}")
                        else:
                            server = smtplib.SMTP(email_host, alternative_port, timeout=10)
                            logger.info(f"已建立备用普通连接到{email_host}:{alternative_port}")
                            server.starttls(context=ssl.create_default_context())
                            logger.info("已升级为TLS加密连接")

                        server.login(email_user, email_password)
                        logger.info(f"已登录邮箱: {email_user}")
                        server.sendmail(email_user, email_recipient, msg.as_string())
                        logger.info(f"使用备用{alternative_type}连接成功发送邮件")
                        sent_successfully = True

                        # 更新配置为成功的连接方式
                        self.config["EMAIL_CONNECTION_TYPE"] = alternative_type
                        logger.info(f"已更新配置为{alternative_type}连接")

                        # 安全关闭连接
                        try:
                            server.quit()
                        except Exception as close_e:
                            logger.warning(f"关闭备用SMTP连接时出现非致命错误: {str(close_e)}")
                            # 忽略关闭连接时的错误

                    except Exception as alt_e:
                        logger.error(f"备用{alternative_type}连接也失败: {str(alt_e)}")

            if sent_successfully:
                logger.info(f"邮件发送成功，收件人: {email_recipient}，距离考研还有 {days_left} 天")
                return True
            else:
                logger.error("所有发送尝试均失败")
                return False

        except Exception as e:
            logger.error(f"发送邮件过程中出现错误: {e}")
            logger.error(traceback.format_exc())
            return False


def main():
    # 初始化系统
    system = ExamCountdownSystem()

    # 显示启动信息
    logger.info("考研倒计时邮件系统已启动，首先发送测试邮件验证运行状态...")
    print("考研倒计时邮件系统已启动，首先发送测试邮件验证运行状态...")

    # 启动时先发送测试邮件
    try:
        logger.info("开始发送测试邮件...")
        print("开始发送测试邮件...")

        # 生成鼓励语
        logger.info("正在生成测试鼓励语...")
        encouragement = system.generate_encouragement()
        if encouragement:
            logger.info("测试鼓励语生成成功")
            print("测试鼓励语生成成功")
        else:
            logger.error("测试鼓励语生成失败")
            print("测试鼓励语生成失败")

        # 发送测试邮件
        logger.info("正在发送测试邮件...")
        print("正在发送测试邮件...")
        if system.send_email():
            logger.info("测试邮件发送成功")
            print("测试邮件发送成功")
        else:
            logger.error("测试邮件发送失败，请检查配置")
            print("测试邮件发送失败，请检查配置")

    except Exception as e:
        logger.error(f"测试邮件发送过程中发生错误: {e}")
        logger.error(traceback.format_exc())
        print(f"测试邮件发送失败: {e}")

    # 测试完成后进入定时发送循环
    logger.info("测试流程结束，进入日常定时发送模式（每天早上8点发送）...")
    print("测试流程结束，进入日常定时发送模式（每天早上8点发送）...")

    try:
        while True:
            now = datetime.now()

            # 显示当前倒计时
            countdown = system.calculate_countdown()
            if countdown:
                days, hours, minutes, seconds = countdown["days"], countdown["hours"], countdown["minutes"], countdown[
                    "seconds"]
                logger.info(f"当前倒计时: {days}天 {hours}小时 {minutes}分 {seconds}秒")

            # 检查是否是早上8点
            if now.hour == 8 and now.minute == 0:
                logger.info("到达设定时间，准备发送每日邮件...")
                print("到达设定时间，准备发送每日邮件...")

                # 生成鼓励语
                logger.info("正在生成每日鼓励语...")
                encouragement = system.generate_encouragement()
                if encouragement:
                    logger.info("每日鼓励语生成成功")
                else:
                    logger.error("每日鼓励语生成失败")

                # 发送每日邮件
                logger.info("正在发送每日邮件...")
                if system.send_email():
                    logger.info("每日邮件发送成功")
                    print("每日邮件发送成功")
                else:
                    logger.error("每日邮件发送失败")
                    print("每日邮件发送失败")

                # 发送完邮件后等待61秒，避免在同一分钟内重复发送
                import time
                time.sleep(61)

            # 每分钟检查一次
            import time
            time.sleep(60)

    except KeyboardInterrupt:
        logger.info("程序被用户中断")
        print("程序已停止")
    except Exception as e:
        logger.error(f"程序发生异常: {e}")
        logger.error(traceback.format_exc())
        print(f"程序发生异常: {e}")


if __name__ == "__main__":
    main()