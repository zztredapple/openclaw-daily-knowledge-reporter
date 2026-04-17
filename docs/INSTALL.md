# 详细安装指南

本文档提供分步指导，帮你从零开始搭建知识日报系统。

---

## 环境要求

- Python 3.7+
- 一个能发邮件的邮箱（SMTP服务）
- 定时任务工具（crontab，Mac/Linux自带，Windows用任务计划程序）

---

## Windows 用户特别说明

Windows 没有 crontab，推荐用**任务计划程序**：

1. 按 `Win + R`，输入 `taskschd.msc`
2. 创建基本任务 → 取名「知识日报」
3. 触发器：每天 7:00
4. 操作：启动程序
5. 程序：`python.exe`的完整路径
6. 参数：`scripts\daily_knowledge_v3.py`
7. 起始位置：`C:\Users\你的用户名\openclaw-daily-knowledge-reporter`

---

## 目录权限说明

确保以下目录有写入权限：

```bash
# 创建日志目录
mkdir -p logs

# 给日志目录写入权限（Linux/Mac）
chmod 755 logs

# 确保知识库文件可写
chmod 644 knowledge_base/*.json
```
