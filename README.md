# 📚 OpenClaw 每日知识日报系统

> 让你每天早上醒来，邮箱里躺着一封专属知识日报。
> 金融知识 + AI 概念 + 英文单词，每天自动送达，无需任何操作。

---

## ✨ 功能预览

| 模块 | 内容 | 数量 |
|------|------|------|
| 💰 金融知识 | 复利、资产配置、市盈率、不良资产、雪球结构… | 70条 |
| 🤖 AI 知识 | Transformer、RAG、提示工程、微调、Cursor… | 70条 |
| 📝 英文单词 | 音标、词源、词根、同/反义词、搭配、例句 | 107个 |

**特色：**
- 📅 每天 7:00 自动发送邮件
- 🔄 智能轮换，不重复
- ⚠️ 库存不足自动提醒 + 自动扩展
- 🎨 专业 HTML 邮件模板
- 🔧 零配置即可测试运行

---

## 🚀 5分钟快速安装

### 第一步：下载本仓库

打开**终端**（Windows 用 PowerShell，Mac 用 Terminal），运行：

```bash
# 克隆仓库
git clone https://github.com/你的用户名/openclaw-daily-knowledge-reporter.git

# 进入目录
cd openclaw-daily-knowledge-reporter
```

> ⚠️ 如果你没有 Git，先安装：Windows 下载 [Git for Windows](https://gitforwindows.org)，Mac 装了 Xcode 就自带。

---

### 第二步：安装 Python

检查是否已安装：

```bash
python3 --version
```

如果显示 `Python 3.x.x`（3.7 以上）就OK。没有的话：

- **Windows**：去 https://python.org 下载 Python 3.10+，安装时勾选 "Add Python to PATH"
- **Mac**：`brew install python3`
- **Ubuntu/Debian**：`sudo apt install python3`

---

### 第三步：配置邮件发件人

复制配置文件：

```bash
cp config/email_config.env.example config/email_config.env
```

编辑配置文件：

```bash
# Windows
notepad config/email_config.env

# Mac / Linux
nano config/email_config.env
```

填写内容（以 163 邮箱为例）：

```env
SMTP_SERVER=smtp.163.com
SMTP_PORT=465
EMAIL=你的邮箱@163.com
AUTHORIZATION_CODE=你的授权码   # 不是密码！
TO_EMAIL=收件人邮箱
CC_EMAIL=                      # 留空，或填抄送邮箱
```

#### 如何获取邮箱授权码？

**163 邮箱：**
1. 登录 mail.163.com
2. 点击右上角「设置」→「POP3/SMTP/IMAP」
3. 开启「SMTP服务」，按提示扫码验证
4. 点击「生成授权码」→ 复制16位授权码

**QQ 邮箱：**
1. 登录 mail.qq.com
2. 设置 → 账户 → POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务
3. 开启「SMTP服务」→ 生成授权码

** Gmail：** 需要开启两步验证后去 https://myaccount.google.com/security 创建应用专用密码。

---

### 第四步：测试运行

```bash
cd openclaw-daily-knowledge-reporter

python3 scripts/daily_knowledge_v3.py
```

看到类似输出说明成功：

```
[07:00:00] 开始生成知识日报...
[07:00:01] 选取金融知识: 复利, 资产配置
[07:00:01] 选取AI知识: Transformer架构, RAG检索增强生成
[07:00:01] 选取英文单词: leverage, synergy
[07:00:02] 邮件发送成功！
```

去收件箱查看你的第一封知识日报 📬

---

### 第五步：设置每天自动发送

```bash
# 打开定时任务编辑器
crontab -e
```

在打开的编辑器里按 `i` 进入编辑模式，粘贴这一行：

```
0 7 * * * cd /你/的/完整/路径/openclaw-daily-knowledge-reporter && /usr/bin/python3 scripts/daily_knowledge_v3.py >> logs/daily.log 2>&1
```

> 💡 把 `/你/的/完整/路径/` 换成你电脑上的实际路径，例如 `/Users/你的用户名/openclaw-daily-knowledge-reporter`

按 `Esc`，输入 `:wq` 回车保存。

---

## 📁 目录结构

```
openclaw-daily-knowledge-reporter/
├── README.md                  # 本文件
├── SKILL.md                  # OpenClaw Skill 配置（可选）
├── scripts/
│   ├── daily_knowledge_v3.py   # 日报主脚本
│   └── auto_expand_kb.py       # 自动扩展知识库脚本
├── knowledge_base/
│   ├── finance.json           # 金融知识库（70条）
│   ├── ai.json                # AI知识库（70条）
│   ├── words.json             # 英文单词库（107个）
│   └── state.json             # 轮换状态（自动生成）
├── config/
│   └── email_config.env.example  # 邮件配置模板
├── docs/
│   ├── INSTALL.md               # 详细安装指南
│   ├── FAQ.md                    # 常见问题解答
│   └── ADD_CONTENT.md           # 如何添加新知识
└── logs/                        # 日志目录（自动创建）
```

---

## ⚙️ 自定义配置

### 修改发送时间

编辑 `scripts/daily_knowledge_v3.py`，找到这行：

```python
# 定时任务 crontab：
# 0 7 * * *  早上7点发送
```

crontab 时间格式：`分 时 日 月 周`
- `0 7 * * *` = 每天早上7:00
- `0 8 * * *` = 每天早上8:00
- `30 18 * * *` = 每天傍晚18:30

### 修改每天发送数量

编辑 `scripts/daily_knowledge_v3.py`：

```python
finance_items = get_daily_items("finance", count=2)   # 默认2条，改成3就每天3条
ai_items = get_daily_items("ai", count=2)             # 默认2条
words = get_daily_words(count=2)                      # 默认2个
```

### 修改邮件标题和样式

编辑 `scripts/daily_knowledge_v3.py` 中的 `generate_html()` 函数，可以改颜色、字体、布局。

---

## 🔧 常见问题

### Q: 报错 `SMTP authentication error`
邮箱密码填错了。填的是**授权码**不是登录密码。

### Q: 报错 `554 DT:SPM`
邮件被识别为垃圾邮件。修改邮件标题（去掉「每日」「免费」等词）或换其他邮箱尝试。

### Q: 想发到多个收件人
在 `config/email_config.env` 里：

```env
TO_EMAIL=aa@163.com,bb@qq.com,cc@gmail.com
```

### Q: 知识不够用了怎么办
系统会自动提醒你。也可以手动运行：

```bash
python3 scripts/auto_expand_kb.py
```

### Q: 想添加自己的知识库
编辑 `knowledge_base/finance.json` 或 `knowledge_base/ai.json`，按现有格式添加条目。格式：

```json
{
  "id": 71,
  "title": "你的标题",
  "en": "English Name",
  "definition": "标准定义",
  "plain": "一句话通俗解释",
  "usage": "使用场景"
}
```

---

## 🧹 重置轮换（重新开始发送）

如果所有知识都发送过一遍了，想重新轮换：

```bash
python3 -c "
import json
state_file = 'knowledge_base/state.json'
with open(state_file) as f:
    state = json.load(f)
state['finance']['used'] = []
state['ai']['used'] = []
state['words']['used'] = []
with open(state_file, 'w') as f:
    json.dump(state, f, indent=2, ensure_ascii=False)
print('已重置，所有知识可以重新发送')
"
```

---

## 📦 可选：配合 OpenClaw Skill 使用

如果你使用 [OpenClaw](https://github.com/openclaw/openclaw) 平台，可以把这个系统作为 Skill 安装：

1. 把本仓库放到 `~/.openclaw/workspace/skills/daily-knowledge-reporter/`
2. 在 OpenClaw 配置中添加 Skill
3. 参考 `SKILL.md` 进行配置

---

## 🤝 贡献

欢迎提交 Issue 和 PR！添加新知识、优化邮件模板、修复 bug 都可以。

---

## 📄 许可证

MIT License - 随意使用，修改，分发。

---

*有问题欢迎提 Issue，看到会回。*
