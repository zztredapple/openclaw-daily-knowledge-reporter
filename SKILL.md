---
name: daily-knowledge-reporter
description: 每日知识日报系统 - 自动发送金融知识、AI知识、英文单词详解。支持动态轮换、库存提醒、邮件发送。
version: 3.0.0
author: 孔明
license: MIT
---

# Daily Knowledge Reporter Skill

用于 OpenClaw 平台的每日知识日报系统 Skill。

## 安装方式

### 方式一：从 GitHub 安装（推荐）

```bash
# 克隆到 OpenClaw skills 目录
git clone https://github.com/你的用户名/openclaw-daily-knowledge-reporter.git ~/.openclaw/workspace/skills/daily-knowledge-reporter
```

### 方式二：手动复制

把整个仓库复制到 `~/.openclaw/workspace/skills/daily-knowledge-reporter/`

## 依赖配置

确保 `.env` 文件或系统环境变量中有邮件配置：

```env
SMTP_SERVER=smtp.163.com
SMTP_PORT=465
EMAIL=your_email@163.com
AUTHORIZATION_CODE=your_auth_code
TO_EMAIL=recipient@email.com
CC_EMAIL=
```

## 定时任务

```bash
# 日报发送
0 7 * * * python3 ~/.openclaw/workspace/skills/daily-knowledge-reporter/scripts/daily_knowledge_v3.py >> ~/.openclaw/workspace/logs/daily_knowledge.log 2>&1

# 知识库自动扩展检查
5 7 * * * python3 ~/.openclaw/workspace/skills/daily-knowledge-reporter/scripts/auto_expand_kb.py >> ~/.openclaw/workspace/logs/auto_expand.log 2>&1
```

## OpenClaw 内使用

安装后在 OpenClaw 中可以通过 Skill 系统触发：

- 手动发送日报：`python3 scripts/daily_knowledge_v3.py`
- 检查库存：`python3 scripts/auto_expand_kb.py`
- 测试邮件发送：直接运行脚本观察日志
