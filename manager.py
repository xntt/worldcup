import json
import os
import random
import time
import feedparser  # 新增库
import google.generativeai as genai
from datetime import datetime, timedelta

# --- 1. 配置 ---
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

SITES_FILE = 'sites.json'

# --- 2. 真实新闻源 (RSS Feeds) ---
# 这里收集了一些免费且高质量的足球/体育新闻源
RSS_SOURCES = [
    "https://www.espn.com/espn/rss/soccer/news",  # ESPN 足球
    "https://feeds.bbci.co.uk/sport/football/rss.xml", # BBC 足球
    "https://www.goal.com/feeds/en/news" # Goal.com
]

# --- 3. 核心功能函数 ---

def fetch_real_news_and_rewrite(domain, theme):
    """
    1. 从 RSS 获取真新闻
    2. 用 Gemini 改写成博彩风格
    """
    news_items = []
    
    # A. 随机选一个源抓取
    source = random.choice(RSS_SOURCES)
    print(f"📡 Fetching RSS from: {source}")
    
    try:
        feed = feedparser.parse(source)
        # 只取前 3 条最新新闻
        entries = feed.entries[:3]
        
        if not entries:
            print("⚠️ RSS Empty, using fallback.")
            return get_fallback_news()

        # B. 遍历新闻并改写
        for entry in entries:
            original_title = entry.title
            original_link = entry.link
            
            # 如果没有 AI Key，直接用原标题 (降级模式)
            if not GEMINI_KEY:
                news_items.append({
                    "title": original_title,
                    "date": datetime.now().strftime("%b %d"),
                    "excerpt": "Click to read full story on official sports news network."
                })
                continue

            # C. 调用 AI 改写 (赋予博彩属性)
            prompt = f"""
            Rewrite this sports news title into a catchy headline for a {theme} betting site: "{original_title}".
            Then write a 1-sentence summary enticing users to bet on the outcome.
            Output JSON: {{"title": "...", "excerpt": "..."}}
            """
            
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(prompt)
                # 清洗 AI 返回的 JSON
                text = response.text.replace('```json', '').replace('```', '').strip()
                ai_data = json.loads(text)
                
                news_items.append({
                    "title": ai_data.get("title", original_title),
                    "date": datetime.now().strftime("%b %d"),
                    "excerpt": ai_data.get("excerpt", "Check latest odds now.")
                })
            except Exception as e:
                print(f"AI Rewrite Error: {e}")
                # 改写失败就用原标题
                news_items.append({
                    "title": original_title,
                    "date": datetime.now().strftime("%b %d"),
                    "excerpt": "Latest update from the world of football."
                })
                
            # 限制速度，防止 API 报错
            time.sleep(1.5)
            
        return news_items

    except Exception as e:
        print(f"RSS Error: {e}")
        return get_fallback_news()

def get_fallback_news():
    """兜底假新闻"""
    return [
        {"title": "World Cup 2026 Updates", "date": "Live", "excerpt": "Tracking qualifiers and team rosters live."},
        {"title": "Betting Market Watch", "date": "Today", "excerpt": "Odds are shifting fast as teams prepare."},
        {"title": "Exclusive Promo", "date": "Limited", "excerpt": "Don't miss out on the 500% deposit bonus."}
    ]

def generate_matches():
    """自动化生成未来赛事 (模拟真实赛程)"""
    # 技巧：这里可以写一个逻辑，永远生成“明天”和“后天”的比赛
    matches = []
    teams = ["Mexico", "USA", "Canada", "Brazil", "Argentina", "France", "Spain", "Germany"]
    stadiums = ["Azteca", "MetLife Stadium", "SoFi Stadium", "BC Place"]
    
    today = datetime.now()
    for i in range(3): # 生成3场
        t1, t2 = random.sample(teams, 2)
        match_date = (today + timedelta(days=i+1)).strftime("%b %d - 20:00")
        
        # 随机生成一个看起来像真的赔率
        odds = round(random.uniform(1.8, 3.2), 2)
        
        matches.append({
            "team_a": t1,
            "team_b": t2,
            "date": match_date,
            "stadium": random.choice(stadiums),
            "odds": str(odds)
        })
    return matches

def generate_seo_footer(domain, theme):
    """自动化 SEO 文案"""
    if not GEMINI_KEY:
        return f"The best {theme} guide for {domain}. Safe and Verified."
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"Write a 2-sentence SEO footer for a gambling site '{domain}'. Mention 'safe payouts' and '2026 World Cup'."
        resp = model.generate_content(prompt)
        return resp.text.strip()
    except:
        return f"Official betting partner guide for {domain}."

# --- 4. 主程序 ---

def main():
    print("🚀 Real-Time Agent Starting...")
    
    if not os.path.exists(SITES_FILE):
        print("sites.json not found.")
        return

    with open(SITES_FILE, 'r') as f:
        sites = json.load(f)

    # 遍历更新
    for site in sites:
        domain = site.get('hostname', 'unknown')
        theme = site.get('theme', 'modern')
        print(f"Processing: {domain}...")

        # 1. 获取真新闻 + AI 改写
        site['news_data'] = fetch_real_news_and_rewrite(domain, theme)
        
        # 2. 自动更新赛事时间表 (永远显示未来日期)
        site['matches_data'] = generate_matches()
        
        # 3. 自动更新 SEO 文案
        if 'seo_content' not in site: site['seo_content'] = {}
        site['seo_content']['body'] = generate_seo_footer(domain, theme)
        site['seo_content']['title'] = f"{domain} Guide"
        
        # 4. 确保布局完整
        if 'layout_order' not in site:
             site['layout_order'] = ["hero", "matches", "offers", "news", "partners", "seo"]

    # 保存
    with open(SITES_FILE, 'w') as f:
        json.dump(sites, f, indent=2)
    
    print("✅ All sites updated with REAL content!")

if __name__ == "__main__":
    main()
