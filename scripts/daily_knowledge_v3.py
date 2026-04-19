#!/usr/bin/env python3
# daily_knowledge_v3.py - 知识日报 v3（动态轮换 + 自动更新提醒）

import json
import os
import random
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(SCRIPT_DIR)
KB_DIR = os.path.join(REPO_DIR, "knowledge_base")
STATE_FILE = os.path.join(KB_DIR, "state.json")
OUTPUT_DIR = os.path.join(REPO_DIR, "data")

def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"[{ts}] {msg}")

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_daily_items(category, count=2):
    data = load_json(f"{KB_DIR}/{category}.json")
    state = load_json(STATE_FILE)
    cat_state = state[category]
    used = set(cat_state["used"])
    existing_ids = set(item["id"] for item in data["items"])
    available = [i for i in range(1, data["total"] + 1) if i not in used and i in existing_ids]
    
    if len(available) < count:
        log(f"{category} 内容即将耗尽，重置轮换")
        used = set()
        available = [i for i in range(1, data["total"] + 1) if i in existing_ids]
        cat_state["used"] = []
        cat_state["last_reset"] = datetime.now().strftime("%Y-%m-%d")
    
    selected = random.sample(available, min(count, len(available)))
    cat_state["used"].extend(selected)
    state[category] = cat_state
    save_json(STATE_FILE, state)
    return [item for item in data["items"] if item["id"] in selected]

def get_daily_words(count=2):
    data = load_json(f"{KB_DIR}/words.json")
    state = load_json(STATE_FILE)
    cat_state = state["words"]
    used = set(cat_state["used"])
    
    # 只选择已扩充详细内容的单词（有synonyms字段的）
    enriched_indices = [i for i, item in enumerate(data["items"]) if item.get("synonyms")]
    available = [i for i in enriched_indices if i not in used]
    
    # 如果已扩充的单词不足
    if len(available) < count:
        if len(enriched_indices) < count:
            # 严重情况：已扩充的单词总数都不够
            log(f"警告：已扩充单词仅{len(enriched_indices)}个，需要补充词库")
            #  fallback：从所有单词中选
            available = [i for i in range(data["total"]) if i not in used]
        else:
            # 重置轮换，只重置已扩充单词的使用记录
            log("已扩充单词轮换完毕，重置使用记录")
            used = set()
            available = enriched_indices.copy()
            cat_state["used"] = []
            cat_state["last_reset"] = datetime.now().strftime("%Y-%m-%d")
    
    selected = random.sample(available, min(count, len(available)))
    cat_state["used"].extend(selected)
    state["words"] = cat_state
    save_json(STATE_FILE, state)
    return [data["items"][i] for i in selected]

def check_low_stock():
    state = load_json(STATE_FILE)
    data = load_json(f"{KB_DIR}/words.json")
    alerts = []
    
    # 检查金融和AI知识库
    for cat in ["finance", "ai"]:
        total = state[cat]["total"]
        used = len(state[cat]["used"])
        remaining = total - used
        if remaining <= state.get("low_threshold", 5):
            alerts.append(f"{cat}: 仅剩 {remaining}/{total} 条未使用")
    
    # 检查单词库 - 只统计已扩充的单词
    enriched_count = sum(1 for item in data["items"] if item.get("synonyms"))
    enriched_used = len([i for i in state["words"]["used"] if i < len(data["items"]) and data["items"][i].get("synonyms")])
    enriched_remaining = enriched_count - enriched_used
    
    if enriched_remaining <= state.get("low_threshold", 3):
        alerts.append(f"words: 已扩充单词仅剩 {enriched_remaining}/{enriched_count} 个未使用，需更新词库")
    elif enriched_count < 20:  # 如果扩充的单词总数太少
        alerts.append(f"words: 已扩充单词仅{enriched_count}个，建议扩充至至少20个")
    
    return alerts

def generate_html(finance_items, ai_items, words, alerts):
    today = datetime.now().strftime("%Y-%m-%d")
    
    html_parts = []
    html_parts.append(f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>每日知识简报 - {today}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); min-height: 100vh; padding: 40px 20px; color: #333; }}
.container {{ max-width: 800px; margin: 0 auto; }}
.header {{ text-align: center; margin-bottom: 40px; color: white; }}
.header h1 {{ font-size: 2.2em; font-weight: 700; margin-bottom: 8px; }}
.header .date {{ font-size: 1.1em; opacity: 0.8; }}
.section-title-main {{ color: white; font-size: 1.3em; margin: 30px 0 15px; padding-left: 15px; border-left: 4px solid #e94560; }}
.knowledge-card {{ background: white; border-radius: 16px; padding: 25px; margin-bottom: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }}
.knowledge-card.ai {{ border-left: 4px solid #00d9ff; }}
.knowledge-tag {{ display: inline-block; background: #e94560; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.75em; font-weight: 600; margin-bottom: 10px; }}
.knowledge-tag.ai-tag {{ background: #00d9ff; color: #1a1a2e; }}
.knowledge-header h3 {{ font-size: 1.4em; color: #1a1a2e; margin-top: 8px; }}
.en-term {{ font-size: 0.85em; color: #666; font-weight: 400; }}
.section {{ margin-bottom: 18px; }}
.section-title {{ font-weight: 600; color: #1a1a2e; margin-bottom: 8px; display: block; }}
.section p {{ color: #555; line-height: 1.7; font-size: 0.95em; }}
.words-section {{ margin-top: 30px; }}
.words-header {{ color: white; font-size: 1.3em; margin-bottom: 20px; display: flex; align-items: center; gap: 10px; }}
.words-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 15px; }}
.word-card {{ background: white; border-radius: 12px; padding: 20px; box-shadow: 0 8px 30px rgba(0,0,0,0.15); }}
.word-title {{ font-size: 1.4em; font-weight: 700; color: #1a1a2e; margin-bottom: 5px; }}
.word-phonetic {{ color: #888; font-size: 0.9em; margin-bottom: 8px; }}
.word-meaning {{ color: #e94560; font-weight: 600; margin-bottom: 12px; font-size: 0.95em; }}
.word-detail {{ color: #555; font-size: 0.85em; line-height: 1.6; margin-bottom: 12px; padding: 10px; background: #f8f9fa; border-radius: 8px; }}
.word-example {{ color: #555; font-size: 0.9em; line-height: 1.5; margin-bottom: 8px; font-style: italic; border-left: 3px solid #00d9ff; padding-left: 10px; }}
.word-cn {{ color: #777; font-size: 0.85em; }}
.alert-box {{ background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; padding: 15px; margin-bottom: 20px; color: #856404; }}
.footer {{ text-align: center; color: rgba(255,255,255,0.6); margin-top: 40px; font-size: 0.85em; }}
</style>
</head>
<body>
<div class="container">
<div class="header"><h1>📚 每日知识简报</h1><div class="date">{today} · 每日更新</div></div>""")
    
    # 库存警告
    if alerts:
        html_parts.append('<div class="alert-box"><h4>⚠️ 知识库库存提醒</h4><ul>')
        for alert in alerts:
            html_parts.append(f'<li>{alert}</li>')
        html_parts.append('</ul><p style="margin-top:10px;font-size:0.9em;">建议尽快更新知识库内容。</p></div>')
    
    # 金融知识
    html_parts.append('<div class="section-title-main">💰 金融知识</div>')
    for item in finance_items:
        en = f' <span class="en-term">{item.get("en", "")}</span>' if item.get("en") else ""
        html_parts.append(f'<div class="knowledge-card"><div class="knowledge-header"><span class="knowledge-tag">金融知识 #{item["id"]}</span><h3>{item["title"]}{en}</h3></div>')
        html_parts.append(f'<div class="section"><span class="section-title">📘 严格定义</span><p>{item["definition"]}</p></div>')
        html_parts.append(f'<div class="section"><span class="section-title">💬 大白话</span><p>{item["plain"]}</p></div>')
        html_parts.append(f'<div class="section"><span class="section-title">🎯 应用场景</span><p>{item["usage"]}</p></div></div>')
    
    # AI知识
    html_parts.append('<div class="section-title-main">🤖 AI 知识</div>')
    for item in ai_items:
        en = f' <span class="en-term">{item.get("en", "")}</span>' if item.get("en") else ""
        html_parts.append(f'<div class="knowledge-card ai"><div class="knowledge-header"><span class="knowledge-tag ai-tag">AI知识 #{item["id"]}</span><h3>{item["title"]}{en}</h3></div>')
        html_parts.append(f'<div class="section"><span class="section-title">📘 严格定义</span><p>{item["definition"]}</p></div>')
        html_parts.append(f'<div class="section"><span class="section-title">💬 大白话</span><p>{item["plain"]}</p></div>')
        html_parts.append(f'<div class="section"><span class="section-title">🎯 应用场景</span><p>{item["usage"]}</p></div></div>')
    
    # 单词
    html_parts.append('<div class="words-section"><div class="words-header"><span style="font-size:1.5em;">📚</span><h3>今日单词详解</h3></div><div class="words-grid">')
    for word in words:
        html_parts.append(f'<div class="word-card"><div class="word-title">{word["word"]}</div><div class="word-phonetic">{word["phonetic"]}</div><div class="word-meaning">{word["meaning"]}</div>')
        
        # 词源
        html_parts.append(f'<div class="word-detail"><strong>📖 词源：</strong>{word["etymology"]}</div>')
        
        # 词根词缀（如果有）
        if word.get("morphology"):
            html_parts.append(f'<div class="word-detail"><strong>🔤 词根词缀：</strong>{word["morphology"]}</div>')
        
        # 用法说明（如果有）
        if word.get("usage"):
            html_parts.append(f'<div class="word-detail"><strong>💡 用法：</strong>{word["usage"]}</div>')
        
        # 同义词（如果有）
        if word.get("synonyms"):
            html_parts.append(f'<div class="word-detail"><strong>✅ 同义词：</strong>{word["synonyms"]}</div>')
        
        # 反义词（如果有）
        if word.get("antonyms"):
            html_parts.append(f'<div class="word-detail"><strong>❌ 反义词：</strong>{word["antonyms"]}</div>')
        
        # 搭配短语（如果有）
        if word.get("collocations"):
            html_parts.append(f'<div class="word-detail"><strong>🔗 常见搭配：</strong>{word["collocations"]}</div>')
        
        # 例句
        html_parts.append(f'<div class="word-example">&quot;{word["example"]}&quot;</div><div class="word-cn">{word["cn"]}</div></div>')
    html_parts.append('</div></div>')
    
    # 页脚
    html_parts.append('<div class="footer"><p>Generated by 孔明 · 每日知识简报 · 动态轮换系统</p></div>')
    html_parts.append('</div></body></html>')
    
    return ''.join(html_parts)

def load_email_config():
    """从 config/email_config.env 加载邮件配置（优先级高于硬编码）"""
    config_path = os.path.join(REPO_DIR, "config", "email_config.env")
    if os.path.exists(config_path):
        with open(config_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip())
    return {
        "SMTP_SERVER": os.environ.get("SMTP_SERVER", "smtp.163.com"),
        "SMTP_PORT": int(os.environ.get("SMTP_PORT", "465")),
        "EMAIL": os.environ.get("EMAIL", ""),
        "AUTHORIZATION_CODE": os.environ.get("AUTHORIZATION_CODE", ""),
        "TO_EMAIL": os.environ.get("TO_EMAIL", ""),
        "CC_EMAIL": os.environ.get("CC_EMAIL", ""),
    }

def send_email(html_content, alerts):
    cfg = load_email_config()
    SMTP_SERVER = cfg["SMTP_SERVER"]
    SMTP_PORT = cfg["SMTP_PORT"]
    EMAIL = cfg["EMAIL"]
    AUTHORIZATION_CODE = cfg["AUTHORIZATION_CODE"]
    TO_EMAIL = cfg["TO_EMAIL"]
    CC_EMAIL = cfg["CC_EMAIL"]
    TODAY = datetime.now().strftime("%Y-%m-%d")

    if not EMAIL or not AUTHORIZATION_CODE or not TO_EMAIL:
        log("邮件配置不完整，请检查 config/email_config.env")
        return False
    
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = Header(f"每日知识简报 <{EMAIL}>", 'utf-8')
        msg['To'] = Header(TO_EMAIL, 'utf-8')
        msg['Cc'] = Header(CC_EMAIL, 'utf-8')
        
        subject = f"每日知识简报 - {TODAY}"
        if alerts:
            subject += " [库存提醒]"
        msg['Subject'] = Header(subject, 'utf-8')
        
        text_content = f"每日知识简报 - {TODAY}\n\n今日内容：\n• 2个金融知识\n• 2个AI知识\n• 2个英文单词详解\n\n请查看HTML版本获取完整内容。"
        
        msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))
        
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(EMAIL, AUTHORIZATION_CODE)
        server.sendmail(EMAIL, [TO_EMAIL, CC_EMAIL], msg.as_string())
        server.quit()
        log(f"邮件发送成功: {TO_EMAIL}")
        return True
    except Exception as e:
        log(f"邮件发送失败: {e}")
        return False

def main():
    log("开始生成知识日报...")

    # 获取今日内容
    finance_items = get_daily_items("finance", 2)
    ai_items = get_daily_items("ai", 2)
    words = get_daily_words(2)
    alerts = check_low_stock()
    
    log(f"选中金融知识: {[i['id'] for i in finance_items]}")
    log(f"选中AI知识: {[i['id'] for i in ai_items]}")
    log(f"选中单词: {[w['word'] for w in words]}")
    
    if alerts:
        log(f"库存警告: {alerts}")
    
    # 生成HTML
    html = generate_html(finance_items, ai_items, words, alerts)
    
    # 保存文件
    today = datetime.now().strftime("%Y-%m-%d")
    output_file = f"{OUTPUT_DIR}/daily-knowledge-{today}.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    log(f"HTML保存完成: {output_file}")
    
    # 发送邮件
    send_email(html, alerts)
    
    log("日报生成完成")

if __name__ == "__main__":
    main()
