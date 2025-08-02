# 考研倒计时邮件系统

这是一个自动化的考研倒计时邮件发送系统，每天早上8点（北京时间）自动发送包含倒计时和AI生成鼓励语的邮件。

## 功能特性

- 📅 **自动倒计时计算**：精确计算距离考研日期的剩余时间
- 🤖 **AI鼓励语生成**：使用DeepSeek API生成个性化鼓励内容
- 📧 **精美邮件模板**：HTML格式的视觉效果丰富的邮件
- ⏰ **定时自动发送**：通过GitHub Actions每天早上8点准时执行
- 🚨 **智能错误处理**：
  - 自动重试机制（最多3次）
  - 邮件发送失败时立即发送详细错误通知到您的邮箱
  - 包含完整日志信息和处理建议
  - 确保您能及时发现并处理问题

## 配置说明

### GitHub Secrets 配置

在GitHub仓库的Settings > Secrets and variables > Actions中配置以下密钥：

- `DEEPSEEK_API_KEY`: DeepSeek API密钥
- `EMAIL_PASSWORD`: QQ邮箱授权码（不是登录密码）

### 邮件配置

在`exam_countdown.py`中的`DEFAULT_CONFIG`部分配置：

- `EMAIL_USER`: 发件人邮箱
- `EMAIL_RECIPIENT`: 收件人邮箱（盼盼的邮箱）
- 其他SMTP配置已预设为QQ邮箱

### 时间配置

- 考研日期：2025年12月21日
- 发送时间：每天早上8点（北京时间）
- GitHub Actions cron: `'0 0 * * *'`（UTC时间0点 = 北京时间8点）

## 错误处理机制

### 自动错误通知

当邮件发送失败时，系统会：

1. **立即发送错误通知邮件到您的邮箱** (`1969365257@qq.com`)
2. **包含详细信息**：
   - 具体错误信息和发生时间
   - 完整的错误堆栈跟踪
   - 最近50行系统日志
   - 详细的处理建议步骤
3. **自动重试机制**：最多重试3次，使用指数退避算法
4. **最终失败通知**：如果所有重试都失败，会发送最终失败通知

### 错误通知邮件示例

错误通知邮件包含：
- 🚨 醒目的错误标题
- 📋 错误摘要（时间、原因、影响）
- 🔍 详细错误信息和堆栈跟踪
- 📝 最近的系统日志
- 💡 具体的处理建议步骤

## 故障排除

### 1. 邮件未按时发送

**如果您收到了错误通知邮件**，请按照邮件中的建议步骤处理。

**如果没有收到任何邮件**，检查以下项目：

1. **GitHub Actions是否启用**
   - 确保仓库的Actions功能已启用
   - 检查工作流是否正常运行

2. **Secrets配置是否正确**
   ```bash
   # 运行调试脚本检查配置
   python debug_config.py
   ```

3. **时区设置是否正确**
   - GitHub Actions使用UTC时间
   - 北京时间8点 = UTC时间0点

### 2. 邮件发送失败

1. **检查QQ邮箱授权码**
   - 确保使用的是授权码，不是登录密码
   - 确保QQ邮箱已开启SMTP服务

2. **检查网络连接**
   - GitHub Actions可能存在网络限制
   - 系统会自动尝试SSL和TLS连接

### 3. AI生成内容失败

1. **检查DeepSeek API**
   - 确保API密钥有效
   - 检查API配额是否充足

## 手动测试

### 本地测试
```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
export DEEPSEEK_API_KEY="your_api_key"
export EMAIL_PASSWORD="your_email_password"

# 运行程序
python exam_countdown.py
```

### GitHub Actions手动触发
1. 进入仓库的Actions页面
2. 选择"考研倒计时邮件发送"工作流
3. 点击"Run workflow"按钮

## 文件说明

- `exam_countdown.py`: 主程序文件
- `.github/workflows/exam-countdown.yml`: 主要的定时任务配置
- `.github/workflows/test-error-handling.yml`: 错误处理测试工作流
- `debug_config.py`: 配置调试脚本
- `requirements.txt`: Python依赖包列表
- `log/`: 日志文件目录

## 注意事项

- 确保GitHub仓库是私有的，避免泄露敏感信息
- 定期检查API配额和邮箱服务状态
- 如需修改发送时间，请调整cron表达式
- 测试工作流已禁用自动执行，避免频繁发送测试邮件
