import json
import os
import random
import time
import google.generativeai as genai
import feedparser # 👈 新增：用于抓取 RSS
from datetime import datetime, timedelta

# --- 1. 配置 ---
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

SITES_FILE = 'sites.json'
OFFERS_FILE = 'offers.json'

# --- 真实新闻源 (RSS Feeds) ---
# 这里汇集了全球各大体育新闻源
RSS_SOURCES = [
    "https://www.espn.com/espn/rss/soccer/news", 
    "https://feeds.bbci.co.uk/sport/football/rss.xml",
    "https://www.goal.com/feeds/en/news"
]

# --- 2. 核心功能函数 ---

def fetch_real_news_from_rss():
    """从 RSS 源抓取最新新闻"""
    print("📡 Fetching Real News from RSS...")
    raw_articles = []
    
    for url in RSS_SOURCES:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:2]: # 每个源只取前2条，避免太长
                raw_articles.append({
                    "title": entry.title,
                    "summary": getattr(entry, 'summary', entry.title)
                })
        except Exception as e:
            print(f"RSS Error ({url}): {e}")
            
    # 打乱顺序，让每次看起来不一样
    random.shuffle(raw_articles)
    return raw_articles[:3] # 只返回前3条给 AI 改写

def ai_rewrite_content(domain, theme, geo, raw_news):
    """调用 Gemini 改写新闻 + 生成 SEO + 生成赛事预测"""
    
    # 构造给 AI 的素材
    news_context = json.dumps(raw_articles) if 'raw_articles' in locals() else "Global Football News"
    
    prompt = f"""
    Role: Senior Betting Editor for {domain} ({geo}).
    Task: 
    1. Rewrite these 3 news headlines/summaries to be exciting for bettors. Focus on odds and winning.
    2. Create 1 sentence SEO footer description.
    3. Generate 2 "Upcoming Matches" based on real teams mentioned in the news (or top teams). Include realistic odds.

    Input News Data: {news_context}

    Output JSON ONLY:
    {{
      "news": [
        {{"title": "...", "date": "Today", "excerpt": "..."}},
        {{"title": "...", "date": "Today", "excerpt": "..."}},
        {{"title": "...", "date": "Today", "excerpt": "..."}}
      ],
      "seo": "...",
      "matches": [
        {{"team_a": "...", "team_b": "...", "date": "Tomorrow 20:00", "stadium": "MetLife Stadium", "odds": "2.10"}},
        {{"team_a": "...", "team_b": "...", "date": "Next Day 18:00", "stadium": "Azteca", "odds": "1.85"}}
      ]
    }}
    """
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(text)
    except Exception as e:
        print(f"❌ AI Generation Error: {e}")
        return None

# --- 3. 主程序 ---

def main():
    # 读取配置
    with open(OFFERS_FILE, 'r') as f:
        all_offers = json.load(f)
    
    with open(SITES_FILE, 'r') as f:
        sites = json.load(f)

    # 1. 先抓取一次真实新闻 (所有站点共用这个素材，省流量)
    raw_news = fetch_real_news_from_rss()
    
    print(f"🔄 Updating {len(sites)} sites with REAL data...")
    
    for site in sites:
        domain = site.get('hostname')
        theme = site.get('theme', 'modern')
        
        # 简单判断 Geo
        if '.mx' in domain or 'mexico' in domain: geo = "Mexico"
        elif '.ca' in domain: geo = "Canada"
        else: geo = "Global"

        print(f"👉 Processing: {domain} [{geo}]")

        # A. 调用 AI (传入真实新闻素材)
        ai_data = ai_rewrite_content(domain, theme, geo, raw_news)
        
        if ai_data:
            # 填入 AI 生成的真实改写数据
            site['news_data'] = ai_data.get('news', [])
            site['matches_data'] = ai_data.get('matches', [])
            
            if 'seo_content' not in site: site['seo_content'] = {}
            site['seo_content']['body'] = ai_data.get('seo', "")
            site['seo_content']['title'] = f"{domain} Betting Guide"
        else:
            print("⚠️ AI failed, skipping content update for this site.")

        # B. 确保 Offer 存在
        site['offer_ids'] = [o['id'] for o in all_offers[:3]]
        
        # C. 确保 Partners 存在 (静态)
        site['partners_data'] = [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/Mastercard-logo.svg/200px-Mastercard-logo.svg.png",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b5/PayPal.svg/200px-PayPal.svg.png",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fa/Apple_logo_black.svg/100px-Apple_logo_black.svg.png"
        ]
        
        # D. 补全布局
        site['layout_order'] = ["hero", "matches", "offers", "news", "partners", "seo"]

        # 休息一下
        time.sleep(3)

    # 保存
    with open(SITES_FILE, 'w') as f:
        json.dump(sites, f, indent=2)
    print("✅ Real News Update Complete!")

if __name__ == "__main__":
    main()
