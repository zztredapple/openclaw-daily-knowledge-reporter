#!/usr/bin/env python3
"""
auto_expand_kb.py - 知识库自动扩展脚本
触发条件：
  1. 任一类别已用 >90% -> 归档已用内容，重置轮换
  2. 任一类别剩余 <= 6 -> 自动扩展知识库
"""

import json
import os
import sys
from datetime import datetime

KB_DIR = "/root/.openclaw/workspace/data/knowledge_base"
STATE_FILE = f"{KB_DIR}/state.json"
REVIEW_DIR = f"{KB_DIR}/review"
THRESHOLD = 6
ARCHIVE_THRESHOLD = 0.9  # 已用超过90%则归档
EXPANSION_BATCH_SIZE = 20

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [auto_expand] {msg}", flush=True)

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def validate_json(path):
    try:
        load_json(path)
        return True
    except Exception as e:
        log(f"JSON验证失败 {path}: {e}")
        return False

def check_stock():
    state = load_json(STATE_FILE)
    needs = []
    archive_cats = []
    for cat in ["finance", "ai"]:
        total = state[cat]["total"]
        used = len(state[cat]["used"])
        rem = total - used
        usage_ratio = used / total if total > 0 else 0
        log(f"{cat}: {rem}/{total} remaining (used {used}, ratio {usage_ratio:.0%})")
        if usage_ratio > ARCHIVE_THRESHOLD:
            archive_cats.append(cat)
        elif rem <= THRESHOLD:
            needs.append(cat)
    words_data = load_json(f"{KB_DIR}/words.json")
    enriched = [i for i, w in enumerate(words_data["items"]) if w.get("synonyms")]
    used_ids = [i for i in state["words"]["used"]
                if i < len(words_data["items"]) and words_data["items"][i].get("synonyms")]
    words_rem = len(enriched) - len(used_ids)
    words_usage = len(used_ids) / len(enriched) if len(enriched) > 0 else 0
    log(f"words (enriched): {words_rem}/{len(enriched)} remaining (used {len(used_ids)}, ratio {words_usage:.0%})")
    if words_usage > ARCHIVE_THRESHOLD:
        archive_cats.append("words")
    elif words_rem <= THRESHOLD:
        needs.append("words")
    return archive_cats, needs

def archive_used(category):
    """将已用内容归档到复习文件，重置已用列表"""
    os.makedirs(REVIEW_DIR, exist_ok=True)
    state = load_json(STATE_FILE)
    data = load_json(f"{KB_DIR}/{category}.json")
    
    if category == "words":
        # words 用数组索引跟踪
        enriched = [i for i, w in enumerate(data["items"]) if w.get("synonyms")]
        used_set = set(state["words"]["used"])
        archived = [data["items"][i] for i in sorted(used_set) if i < len(data["items"])]
    else:
        used_ids = set(state[category]["used"])
        items_by_id = {item["id"]: item for item in data["items"]}
        archived = [items_by_id[uid] for uid in sorted(used_ids) if uid in items_by_id]
    
    if not archived:
        log(f"{category}: 无内容需要归档")
        return 0
    
    today = datetime.now().strftime("%Y-%m-%d")
    archive_file = f"{REVIEW_DIR}/{category}_{today}.json"
    archive_data = {
        "category": category,
        "archived_date": today,
        "count": len(archived),
        "items": archived
    }
    with open(archive_file, 'w', encoding='utf-8') as f:
        json.dump(archive_data, f, ensure_ascii=False, indent=2)
    
    # 重置已用
    state[category]["used"] = []
    state[category]["last_reset"] = today
    save_json(STATE_FILE, state)
    
    log(f"{category}: 已归档 {len(archived)} 条到 {archive_file}")
    return len(archived)

def append_items(category, items):
    path = f"{KB_DIR}/{category}.json"
    data = load_json(path)
    # 获取当前最大ID
    current_max_id = max((item["id"] for item in data["items"]), default=0)
    if isinstance(items[0], dict):
        data["items"].extend(items)
        data["total"] = len(data["items"])
    else:
        for entry in items:
            # 使用递增ID而非固定ID，避免重复
            current_max_id += 1
            item = {"id": current_max_id, "title": entry[1], "en": entry[2],
                    "definition": entry[3], "plain": entry[4], "usage": entry[5]}
            data["items"].append(item)
        data["total"] = max(item["id"] for item in data["items"])
    save_json(path, data)
    state = load_json(STATE_FILE)
    if category == "words":
        enriched = [i for i, w in enumerate(data["items"]) if w.get("synonyms")]
        state[category]["total"] = len(enriched)
    else:
        state[category]["total"] = data["total"]
    save_json(STATE_FILE, state)
    log(f"Appended {len(items)} items to {category}, new total: {data['total']}")


FINANCE_EXPANSION = [
    (None,"不良资产","Non-Performing Assets","借款人无法按约定还本付息的资产，包括不良贷款、违约债券、困境房地产等","还不上的债。借钱的人跑路了或者彻底还不起，这笔债就变成了银行的坏账。","银行资产质量监控、AMC资产管理公司、困境投资、债转股"),
    (None,"固收+","Fixed Income Plus","以固定收益资产为主，辅以少量权益或可转债等资产追求增强收益的策略","稳稳的幸福plus。债券打底保证不亏，再配点股票希望多赚点。","银行理财替代、稳健型基金、中低风险偏好投资者"),
    (None,"雪球结构","Snowball Structure","一种障碍期权结构，只要标的价格不跌破敲入线，投资者获得票息收益","震荡行情的收割机。只要股价不暴跌，一直拿利息，暴跌了就亏大钱。","结构化理财、机构衍生品销售、高净值投资者"),
    (None,"香草期权","Vanilla Option","最标准的期权合约，赋予持有者买入（看涨）或卖出（看跌）的权利而非义务","期权界的小白。买入看涨期权，股价涨了你赚，股价跌了最多亏权利金。","投机、对冲、保险型策略、权益类收益增强"),
    (None,"可转债","Convertible Bond","可以在约定条件下转换为上市公司股票的债券，兼具债底保护和上涨弹性","进可攻退可守。债券价格有保底，股市行情好又能换成股票赚大钱。","A股特色品种、低风险偏好资金、条款博弈"),
    (None,"同业存单","Negotiable Certificate of Deposit","存款类金融机构在全国银行间市场上发行的记账式定期存款凭证","银行之间互相借钱。中小银行通过发行同业存单向大银行借钱，利率比存款高。","银行流动性管理、货币基金配置、短期资金市场"),
    (None,"梯度费率","Tiered Fee Structure","根据持有时长或资产规模递减收取管理费用的收费模式","持有越久交费越少。鼓励长期持有，减少频繁赎回对基金的冲击。","基金销售激励设计、机构投资者议价、持有期优惠"),
    (None,"绝对收益","Absolute Return","追求正回报而非相对基准收益的投资目标，不关注跑赢或跑输市场","不管大盘涨跌，目标是赚钱。采用对冲、套利等策略与市场涨跌脱钩。","对冲基金、FOF母基金、机构资管部、养老金投资"),
    (None,"相对收益","Relative Return","以跑赢基准指数为目标，收益来源是相对表现的业绩评价方式","赢了基准才算赚。指数涨10%你涨15%，这才叫超额收益。","公募基金主流评价标准、基金排名、主动管理型基金"),
    (None,"最大回撤","Maximum Drawdown","投资组合从峰值到谷底的最大跌幅，衡量最坏情况的亏损","曾经最惨跌多少。从100万跌到70万，最大回撤就是30%。","风险控制指标、量化对冲基金、客户适当性管理"),
    (None,"卡玛比率","Calmar Ratio","年化收益除以最大回撤，衡量每承受一单位亏损风险能获得多少收益","性价比最高的回撤指标。比夏普比率更能反映极端风险下的收益效率。","CTA基金评价、对冲基金筛选、风险调整收益"),
    (None,"尾部风险","Tail Risk","资产收益率分布在极端负值区域的风险，即发生罕见大幅亏损的可能性","小概率大灾难。市场99%时间正常，但1%时间可能暴跌50%，这就是尾部风险。","风险管理、期权对冲、宏观对冲、风险预算"),
    (None,"风险平价","Risk Parity","让各资产对组合总风险的贡献相同的配置方法，而非按金额平分","风险均等分配。100万股票和100万债券，股票波动大所以配少些，最终风险一样。","桥水全天候策略、组合优化、机构资产配置"),
    (None,"全天候策略","All Weather Portfolio","Risk Parity基础上，增加通胀保护债券等资产，在所有经济环境中都能表现","经济好坏都能赢。经济增长持有股票，通胀上升持有大宗商品，啥环境都有应对。","桥水基金代表作、长期资产配置、养老金投资"),
    (None,"耶鲁模式","Yale Model","耶鲁大学捐赠基金开创的重仓私募股权和绝对收益资产的配置模式","大学基金里的异类。不买国债股票，大钱投入私募股权和风投，长期业绩惊人。","捐赠基金配置、另类资产配置、长期投资机构"),
    (None,"并购重组","M&A","企业间的合并（Merge）与收购（Acquire），或上市公司重大资产重组","买公司或卖公司。行业龙头收购竞争对手，或上市公司把资产整体卖掉换新业务。","投资银行业务、PE投资、产业升级、企业转型"),
    (None,"杠杆收购","Leveraged Buyout (LBO)","以少量自有资金加大量债务融资收购目标公司的交易结构","借钱买公司。用被收购公司的资产和现金流作抵押借钱，买下整个公司。","KKR、黑石等PE经典策略、收购兼并、债务融资"),
    (None,"私有化退市","Privatization/Delisting","上市公司大股东收购全部股份使其退出公开股票市场的行为","把上市公司买回家。不让散户买卖了，公司重新变回私人公司。","企业重组、PE退出、二次上市、战略转型"),
    (None,"SPAC上市","SPAC IPO","Special Purpose Acquisition Company，通过空壳公司先上市再并购实体企业的上市方式","先上车后补票。成立一个空壳基金上市，再去找实体公司合并变相上市。","美股上市创新途径、李泽楷、Rothschild公司、空壳并购"),
    (None,"市销率","Price-to-Sales Ratio","股票价格除以每股销售额的比率，适用于暂无盈利或盈利较少的公司估值","按收入算公司值不值。收入100亿的公司市值50亿，PS=0.5倍。","SaaS公司估值、电商平台、成长股早期估值、科创板公司"),
]


AI_EXPANSION = [
    (None,"Cursor AI","Cursor","基于大模型的AI代码编辑器，内置多模型支持和代码补全、对话式编程功能","专门为程序员打造的AI IDE。写代码不用离开编辑器，AI直接帮你写、改、解释。","程序员日常开发、AI编程工具、代码补全、学生开发者"),
    (None,"Claude Code","Claude Code","Anthropic推出的命令行AI编程工具，让Claude在终端直接执行代码任务","命令行里的程序员。描述你想做什么，Claude自己打开终端执行，git、部署都能干。","DevOps自动化、代码审查、脚本编写、开发者工作流"),
    (None,"OpenAI o1/o3","OpenAI o1 & o3","OpenAI推出的推理模型系列，通过强化学习在推理阶段进行深度思考","会思考的AI。不是立刻给答案，而是一步步推理，适合数学证明和复杂逻辑。","数学研究、代码竞赛、科研推理、复杂问题求解"),
    (None,"Gemini Ultra","Google Gemini Ultra","Google最强大的多模态大模型，支持文本、图像、音频、视频的统一理解","Google的终极AI。能处理的数据类型最全，PPT、代码、音频、视频一起理解。","Google生态集成、多模态应用、企业AI、Bard背后模型"),
    (None,"Llama 开源生态","Llama Open Ecosystem","Meta开源的LLaMA系列大模型及其社区衍生态，包括微调版本和工具链","AI的Linux。开源模型谁都能用，全球开发者一起改进，衍生出几千个版本。","开源模型部署、企业私有化部署、模型微调、学术研究"),
    (None,"RAG 中文优化","RAG for Chinese","针对中文语义和文档结构的检索增强生成优化技术","中文知识库必备。让AI更好地理解中文分段、标点和专业术语的检索匹配。","中文企业知识库、法律文档问答、医疗知识库"),
    (None,"长上下文窗口","Long Context Window","大模型单次能处理的输入长度，GPT-4 128K、Claude 200K、Gemini 1M+","AI能一口气读一本小说了。不用分段喂，完整一本书丢进去直接理解。","长文档分析、书籍摘要、代码库理解、法律合同审查"),
    (None,"KV Cache","Key-Value Cache","Transformer推理中缓存注意力键值对以避免重复计算的技术","记住之前的计算。已经算过的注意力不用再算，生成速度翻倍。","大模型推理优化、LLM serving、成本降低"),
    (None,"投机解码","Speculative Decoding","用小模型快速生成多个token，再由大模型验证的推理加速技术","小模型打草稿大模型检查。小模型快速猜，大模型负责验证正确性，整体加速明显。","实时对话、推理延迟优化、流式输出"),
    (None,"Continuous Batching","Continuous Batching","动态批处理技术，将不同请求的不同生成阶段放在同一批次处理","不浪费算力。别人的请求在生成，你的请求在预热，合并成一锅炖，GPU利用率拉满。","大模型服务部署、吞吐量优化、云端推理"),
    (None,"Flash Attention","Flash Attention","一种内存高效注意力机制，通过IO感知设计大幅降低注意力计算显存占用","注意力计算的工程奇迹。不用占那么多显存，4090也能跑大模型了。","大模型训练与推理、长序列处理、显存优化"),
    (None,"Prefix Caching","Prefix Caching","缓存对话前缀的KV值，多轮对话中复用已计算过的系统提示词","重复的话不用重复说。系统提示词算一遍，多轮对话直接复用，省token省时间。","AI助手多轮对话、企业知识库问答、客服机器人"),
    (None,"MCP 协议","Model Context Protocol","Anthropic提出的让AI模型与外部数据源和工具进行标准化交互的协议","AI的USB接口。不管什么工具，插上MCP就能用，AI就能调用各种外部系统了。","AI Agent工具调用、Claude生态、插件系统"),
    (None,"A2A 协议","Agent to Agent Protocol","让不同厂商、不同架构的AI Agent之间能互相通信协作的协议","AI之间的HTTP协议。让不同公司造的AI Agent能够互相打电话，协同工作。","多智能体系统、企业AI集成、异构Agent协作"),
    (None,"OpenAI Assistants API","OpenAI Assistants API","OpenAI提供的用于构建AI助手的API，支持文件检索、代码解释器、函数调用","官方帮你搭AI助手。不用自己实现检索和工具调用，OpenAI给你包圆了。","构建AI客服、垂直领域助手、文档问答"),
    (None,"函数调用/工具调用","Function Calling / Tool Use","让大模型能够调用外部API、数据库查询、代码执行等外部工具的能力","AI学会使用工具。不只是聊天，能真帮用户执行操作：发邮件、查天气、下订单。","AI Agent、插件生态、自动化办公、实时数据"),
    (None,"LangChain","LangChain","用于构建大模型应用的开发框架，提供链式调用、工具集成、内存管理等","AI应用的脚手架。拼装提示词、连接数据库、调用工具，一套框架全搞定。","AI应用开发、RAG系统、聊天机器人、企业AI"),
    (None,"LlamaIndex","LlamaIndex","专门用于构建检索增强生成系统的数据框架，重点在数据连接和索引","RAG专用框架。把PDF、网页、数据库接进来，建索引，让AI能查到最新内容。","企业知识库、文档问答、数据密集型应用"),
    (None,"Semantic Kernel","Semantic Kernel","微软推出的企业级AI应用开发框架，支持Planner和原生工具集成","微软给企业做的LangChain。接入了微软全家桶，Office、Azure都能无缝对接。","企业AI应用、微软生态集成、Copilot开发"),
    (None,"CrewAI 多智能体","CrewAI","开源多智能体编排框架，多个AI Agent扮演不同角色分工协作完成任务","AI团队协作。一个Agent当老板分配任务，一个当研究员查资料，一个当写手出报告。","复杂任务分解、多Agent协作、内容生产、工作流自动化"),
]


WORD_EXPANSION = [
    {"word":"ubiquitous","phonetic":"/ju:bɪkwɪtəs/","meaning":"adj. 无处不在的，普遍存在的","etymology":"拉丁语 ubique（到处）","example":"Smartphones have become ubiquitous in modern society.","cn":"智能手机在现代社会已无处不在。","synonyms":"omnipresent, pervasive, universal, everywhere, prevalent","antonyms":"rare, scarce, uncommon, absent","morphology":"ubique(到处)+-ous(形容词)","usage":"形容某物在各处都很常见，强调渗透到生活的每个角落","collocations":"ubiquitous presence, ubiquitous technology"},
    {"word":"pragmatic","phonetic":"/præɡmætɪk/","meaning":"adj. 务实的，实用主义的","etymology":"希腊语 pragmatikos（适合实践的）","example":"We need a pragmatic approach to solve this problem.","cn":"我们需要一种务实的方法来解决这个问题。","synonyms":"practical, realistic, sensible, down-to-earth","antonyms":"idealistic, impractical, theoretical","morphology":"pragma(行为)+-ic","usage":"强调做事讲究实效，不拘泥于理论，善于变通","collocations":"pragmatic approach, pragmatic solution"},
    {"word":"paradigm","phonetic":"/pærədaɪm/","meaning":"n. 范式，典范，思维框架","etymology":"希腊语 paradeigma（模型、例子）","example":"The smartphone created a new paradigm for communication.","cn":"智能手机开创了通信的新范式。","synonyms":"model, pattern, framework, standard","antonyms":"exception, anomaly","morphology":"para-(旁边)+digma(展示)","usage":"指一个时代或领域公认的理论框架或思维模式","collocations":"shift in paradigm, dominant paradigm"},
    {"word":"heuristic","phonetic":"/hjʊərɪstɪk/","meaning":"adj./n. 启发式的；探索法","etymology":"希腊语 heuriskein（发现）","example":"Using a rule of thumb is a common heuristic in decision-making.","cn":"使用拇指规则是决策中常见的启发式方法。","synonyms":"rule of thumb, mental shortcut, intuitive approach","antonyms":"algorithmic, systematic","morphology":"heuriskein(发现)+-ic","usage":"指快速做出判断的经验法则，不完美但实用","collocations":"heuristic method, heuristic approach"},
    {"word":"arbitrage","phonetic":"/ɑ:bɪtrɑ:ʒ/","meaning":"n. 套利，套汇","etymology":"拉丁语 arbitratus（仲裁，判断）","example":"Traders made millions through currency arbitrage.","cn":"交易员通过货币套利赚了数百万。","synonyms":"speculation, trading, price exploitation","antonyms":"","morphology":"ar-(向)+bitrage(评估)","usage":"金融领域特指利用不同市场价格差异无风险获利","collocations":"risk arbitrage, currency arbitrage"},
    {"word":"proprietary","phonetic":"/prəpraɪətəri/","meaning":"adj. 专有的，专利的","etymology":"拉丁语 proprietas（所有权）","example":"The algorithm is a proprietary trade secret of the firm.","cn":"这个算法是该公司专有的商业机密。","synonyms":"exclusive, patented, owned, private","antonyms":"open-source, public, generic","morphology":"proprietas(所有权)+-ary","usage":"强调排他性，指只有特定公司或人拥有的技术/产品","collocations":"proprietary technology, proprietary trading"},
    {"word":"fiduciary","phonetic":"/fɪdu:ʃəri/","meaning":"adj. 受托的，信托的；n. 受托人","etymology":"拉丁语 fiducia（信任）","example":"As a fiduciary, the fund manager must act in the best interest of clients.","cn":"作为受托人，基金经理必须以客户最佳利益行事。","synonyms":"trustee, guardian, caretaker, steward","antonyms":"","morphology":"fiducia(信任)+-ary","usage":"法律和金融术语，指被信任托付财产或利益的一方","collocations":"fiduciary duty, fiduciary responsibility"},
    {"word":"leverage","phonetic":"/li:vərɪdʒ/","meaning":"n. 杠杆作用；影响力；v. 利用","etymology":"古法语 levier（杠杆）","example":"We can leverage our existing customer base to launch the new product.","cn":"我们可以利用现有的客户基础来推出新产品。","synonyms":"utilize, exploit, capitalize on, maximize","antonyms":"underuse, waste","morphology":"lever(杠杆)+-age","usage":"动词强调巧妙地利用现有优势或资源达到目的","collocations":"leverage technology, leverage resources"},
    {"word":"collateral","phonetic":"/kəlætərəl/","meaning":"n. 抵押品，担保物","etymology":"拉丁语 collateralis（侧面的）","example":"The bank demanded real estate as collateral for the loan.","cn":"银行要求以房产作为贷款的抵押品。","synonyms":"security, guarantee, pledge, backup","antonyms":"","morphology":"col-(一起)+lateral(侧面)","usage":"金融中指借款时提供的质押物，违约时出借方有权处置","collocations":"collateral security, pledge as collateral"},
    {"word":"vignette","phonetic":"/vɪnjet/","meaning":"n. 小插图；简介","etymology":"法语 vignette（葡萄藤小装饰）","example":"The article opens with a touching vignette about her childhood.","cn":"文章以一个感人的童年小故事作为开篇。","synonyms":"sketch, snapshot, brief scene, anecdote","antonyms":"","morphology":"vigne(葡萄园)+-ette(小)","usage":"指简短但生动的场景描写或故事片段","collocations":"vignette scene, opening vignette"},
    {"word":"nuance","phonetic":"/nju:ɑ:ns/","meaning":"n. 细微差别，微妙之处","etymology":"法语 nuance（色调细微变化）","example":"She understands the nuances of the Chinese language.","cn":"她理解中文的细微差别。","synonyms":"subtlety, distinction, refinement, shade","antonyms":"coarseness, crudeness","morphology":"nuance(色调变化)","usage":"指两个事物之间非常细微的差异，需要仔细才能察觉","collocations":"subtle nuance, linguistic nuances"},
    {"word":"ethos","phonetic":"/i:θɒs/","meaning":"n. 精神特质，价值观体系","etymology":"希腊语 ethos（性格、习惯）","example":"The company ethos emphasizes innovation and integrity.","cn":"这家公司的核心价值观强调创新和诚信。","synonyms":"spirit, culture, character, values","antonyms":"","morphology":"ethos(性格)","usage":"指一个组织或文化整体的精神面貌和价值取向","collocations":"company ethos, professional ethos"},
    {"word":"proxy","phonetic":"/prɒksi/","meaning":"n. 代理人，代理权；代替物","etymology":"古法语 prosscurie（委托代理）","example":"I voted by proxy at the shareholder meeting.","cn":"我委托他人代理投票了股东大会。","synonyms":"representative, agent, delegate, substitute","antonyms":"","morphology":"pro-(为了)+-xy","usage":"可指代理投票的人，也可以指用另一个变量代表真实变量","collocations":"vote by proxy, proxy variable"},
    {"word":"anomaly","phonetic":"/ənɒməli/","meaning":"n. 异常现象，反常事物","etymology":"希腊语 anomalia（不平整）","example":"The warm winter was considered a climate anomaly.","cn":"温暖的冬季被视为气候异常。","synonyms":"irregularity, deviation, abnormality, exception","antonyms":"norm, standard, regularity","morphology":"an-(不)+homalos(平坦)","usage":"指偏离正常或预期的事物","collocations":"statistical anomaly, climate anomaly"},
    {"word":"remediation","phonetic":"/rɪmi:dieɪʃən/","meaning":"n. 补救，修复，治理","etymology":"拉丁语 remedium（治疗）","example":"Environmental remediation of the contaminated site cost millions.","cn":"污染场地的环境修复耗费了数百万。","synonyms":"remedy, correction, repair, cleanup","antonyms":"contamination, damage","morphology":"re-(重新)+medius(治疗)+-ation","usage":"常用于环境、IT系统或金融领域的修复纠正工作","collocations":"environmental remediation, remediation plan"},
    {"word":"due diligence","phonetic":"/dju: dɪlɪdʒəns/","meaning":"n. 尽职调查，谨慎调查","etymology":"法律术语，拉丁语 diligentia（勤勉）","example":"The VC firm conducted thorough due diligence before investing.","cn":"这家风投在投资前进行了全面的尽职调查。","synonyms":"investigation, examination, assessment, audit","antonyms":"","morphology":"due(应尽的)+diligence(勤勉)","usage":"商业和法律术语，指重大决策前必须做的全面调查","collocations":"conduct due diligence, due diligence process"},
    {"word":"materiality","phonetic":"/mətɪəriæləti/","meaning":"n. 重要性，实质性","etymology":"拉丁语 materialis（物质相关的）","example":"The auditor assessed the materiality of the misstatement.","cn":"审计员评估了这笔错报的重要性。","synonyms":"significance, relevance, importance, substance","antonyms":"insignificance, triviality","morphology":"material(重要的)+-ity","usage":"审计和财务领域专指对决策有影响的重要程度","collocations":"materiality assessment, materiality threshold"},
    {"word":"covenant","phonetic":"/kʌvənənt/","meaning":"n. 契约条款，约束性条款","etymology":"拉丁语 conventio（协议）","example":"The bond covenant restricts the company from taking on more debt.","cn":"债券契约条款限制了公司再借债。","synonyms":"agreement, clause, stipulation, promise","antonyms":"","morphology":"convenire(集合)+-ant","usage":"金融和法律中指债券或合同中对一方的约束性约定","collocations":"debt covenant, bond covenant"},
    {"word":"cadence","phonetic":"/keɪdəns/","meaning":"n. 节奏，韵律；周期性","etymology":"拉丁语 cadere（落下）","example":"The regular cadence of releases keeps users engaged.","cn":"固定的更新节奏保持了用户的参与度。","synonyms":"rhythm, pace, tempo, cycle","antonyms":"irregularity, chaos","morphology":"cadere(落下)+-ence","usage":"既可指声音的节奏，也可指工作或产品的规律性","collocations":"release cadence, speech cadence"},
    {"word":"prima facie","phonetic":"/praɪmə feɪʃi/","meaning":"adj./adv. 基于表面证据的（初步成立的）","etymology":"拉丁语 prima（第一）+ facie（面貌）","example":"The case appears to be prima facie evidence of fraud.","cn":"这个案件看起来是表面上的欺诈证据。","synonyms":"apparent, surface-level, on the face of it","antonyms":"proven, established, conclusive","morphology":"拉丁短语，字面意思第一眼","usage":"法律术语，指从表面证据看成立，但还需进一步证实","collocations":"prima facie case, prima facie evidence"},
    {"word":"ipso facto","phonetic":"/ɪpsoʊ fæktoʊ/","meaning":"adv. 依据事实本身，直接因事实而…","etymology":"拉丁语 ipso（本身）+ facto（事实）","example":"The contract is ipso facto void under these circumstances.","cn":"在此情况下，合同直接因事实本身而无效。","synonyms":"by that very fact, automatically, necessarily","antonyms":"","morphology":"拉丁短语","usage":"强调某事因另一个事实而自动产生，无须其他程序","collocations":"ipso facto void, ipso facto invalid"},
    {"word":"per se","phonetic":"/pɜ: seɪ/","meaning":"adv. 本身，自身（本质上）","etymology":"拉丁语 per（通过）+ se（自己）","example":"The technology is not harmful per se, but its misuse is.","cn":"技术本身并无害，害的是滥用。","synonyms":"in itself, as such, essentially, intrinsically","antonyms":"","morphology":"拉丁短语","usage":"用于强调某事物本身，而非其衍生的后果或应用","collocations":"not per se, harmful per se"},
    {"word":"de facto","phonetic":"/deɪ fæktoʊ/","meaning":"adj./adv. 事实上的，实际上的","etymology":"拉丁语 de（关于）+ facto（事实）","example":"He is the de facto leader of the company despite having no official title.","cn":"虽然没有正式头衔，他是公司事实上的领袖。","synonyms":"in practice, effectively, actually, in reality","antonyms":"de jure, nominal, official","morphology":"拉丁短语","usage":"指实际存在并发挥作用，但可能未经正式承认","collocations":"de facto standard, de facto leader"},
    {"word":"alpha","phonetic":"/ælfə/","meaning":"n. 阿尔法收益（投资语境）","etymology":"希腊字母α","example":"The fund generated 3% alpha over the benchmark last year.","cn":"该基金去年跑赢基准3%，产生了3%的阿尔法收益。","synonyms":"edge, advantage, excess return","antonyms":"beta, benchmark","morphology":"希腊字母表第一个","usage":"投资领域指主动管理带来的超额收益，不随市场涨跌","collocations":"generate alpha, alpha generation"},
    {"word":"in vitro","phonetic":"/ɪn vi:troʊ/","meaning":"adj./adv. 在体外","etymology":"拉丁语 in（在...中）+ vitrum（玻璃）","example":"In vitro fertilization has helped millions of couples conceive.","cn":"体外受精技术帮助了数百万对夫妇实现生育。","synonyms":"artificial, laboratory-based, test-tube","antonyms":"in vivo, natural","morphology":"in（在...中）+ vitrum（玻璃）","usage":"生物学和医学术语，指在生物体外进行实验或反应","collocations":"in vitro study, in vitro fertilization"},
    {"word":"in vivo","phonetic":"/ɪn vi:voʊ/","meaning":"adj./adv. 在活体内","etymology":"拉丁语 in（在...中）+ vivum（活的）","example":"The drug performed differently in vivo than in vitro.","cn":"这种药物在活体内的表现与体外实验不同。","synonyms":"natural, within a living organism","antonyms":"in vitro, artificial","morphology":"in（在...中）+ vivum（活的）","usage":"生物学和医学术语，与 in vitro 相对","collocations":"in vivo study, in vivo testing"},
    {"word":"sine qua non","phonetic":"/sɪni kwɑ: noʊn/","meaning":"n. 必要条件，必不可少的前提","etymology":"拉丁语 sine（没有）+ qua（哪个）+ non（不）","example":"Hard work is the sine qua non of success.","cn":"努力是成功的必要条件。","synonyms":"prerequisite, essential condition, must-have, necessity","antonyms":"nonessential, optional, luxury","morphology":"拉丁短语，字面意思没有它就不成立","usage":"正式场合指某事成立的不可或缺的条件","collocations":"the sine qua non of"},
    {"word":"ad hoc","phonetic":"/æd hɒk/","meaning":"adj./adv. 临时性的，特设的","etymology":"拉丁语 ad（到）+ hoc（这个）","example":"They set up an ad hoc committee to handle the crisis.","cn":"他们成立了一个临时委员会来处理这场危机。","synonyms":"temporary, improvised, makeshift, one-off","antonyms":"permanent, systematic, planned","morphology":"ad（向）+ hoc（这个）","usage":"指为特定问题临时设立，非长期制度化安排","collocations":"ad hoc committee, ad hoc solution"},
    {"word":"marginal","phonetic":"/mɑ:rdʒɪnəl/","meaning":"adj. 边缘的；微小的；边际的","etymology":"拉丁语 margo（边缘）","example":"The difference is only marginal and not worth worrying about.","cn":"差异微乎其微，不值得担心。","synonyms":"slight, minimal, negligible, insignificant","antonyms":"significant, substantial, major","morphology":"margo(边缘)+-inal","usage":"既可指物理边缘，也常用于经济学边际概念或微不足道","collocations":"marginal improvement, marginal cost"},
    {"word":"vested interest","phonetic":"/vestɪd ɪntrəst/","meaning":"n. 既得利益；盘根错节的利益关系","etymology":"vest（给予权力）+ interest（利益）","example":"Politicians often have vested interests in the policies they promote.","cn":"政客们常对自己推动的政策有既得利益。","synonyms":"self-interest, personal stake, ulterior motive","antonyms":"disinterestedness, impartiality, altruism","morphology":"vested(已赋予的)+interest(利益)","usage":"强调某人从某事中获得的好处，常暗示利益冲突","collocations":"have a vested interest, vested interests in"},
]


def main():
    archive_cats, expand_cats = check_stock()
    
    # 先处理归档
    for cat in archive_cats:
        archive_used(cat)
    
    # 再处理扩展
    if not expand_cats:
        if archive_cats:
            log("归档完成，知识库已重置")
        else:
            log("所有知识库库存充足，无需扩展")
        return

    log(f"检测到以下类别需要扩展: {expand_cats}")

    for cat in expand_cats:
        if cat == "finance":
            append_items("finance", FINANCE_EXPANSION)
        elif cat == "ai":
            append_items("ai", AI_EXPANSION)
        elif cat == "words":
            append_items("words", WORD_EXPANSION)

    log("扩展完成，验证JSON格式...")
    for cat in ["finance", "ai", "words"]:
        if validate_json(f"{KB_DIR}/{cat}.json"):
            log(f"{cat}.json 格式验证通过")

    log("扩展流程结束")
    # 飞书通知
    if os.path.exists("/root/.openclaw/workspace/scripts/feishu_notify.py"):
        try:
            sys.path.insert(0, "/root/.openclaw/workspace/scripts")
            import feishu_notify
            feishu_notify.notify("知识库自动扩展", f"已自动扩展: {', '.join(needs)}")
        except Exception as e:
            log(f"通知发送失败: {e}")


if __name__ == "__main__":
    main()
