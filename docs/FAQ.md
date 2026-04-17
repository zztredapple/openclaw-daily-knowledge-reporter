# 常见问题解答

## 邮件发送相关

### SMTP authentication error
授权码填错了。163邮箱授权码在 mail.163.com → 设置 → POP3/SMTP → 开启服务 → 生成授权码。授权码不等于邮箱密码。

### 邮件内容乱码
检查 `daily_knowledge_v3.py` 中邮件编码设置，确保使用 UTF-8：
```python
msg['Content-Type'] = 'text/html; charset=utf-8'
```

### 邮件被标记为垃圾邮件
- 邮件标题避免「免费」「赚钱」等词
- 发件邮箱和收件邮箱尽量用同一平台（如都用163）
- 每天发送量不要过大

---

## 定时任务相关

### crontab 不生效
1. 确认 crontab 已保存（`:wq` 退出）
2. 确认 Python 路径正确：`which python3`
3. 用完整绝对路径代替相对路径
4. 查看日志：`cat logs/daily.log`

### 任务重复执行
检查 crontab 是否有重复行，删除多余的。

---

## 知识库相关

### state.json 是什么
记录每条知识是否已发送过，保证不重复。删除它会重置轮换状态。

### 知识数量不够用了
运行 `python3 scripts/auto_expand_kb.py` 自动追加新内容。

### 如何查看剩余数量
运行脚本后查看日志输出的 `remaining` 数字，或直接查看 `knowledge_base/state.json` 的 `used` 数组长度。
