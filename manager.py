import json
import os
import feedparser
import google.generativeai as genai
from datetime import datetime
import time

# 配置 API
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# RSS 源 (涵盖足球、篮球、综合)
RSS_MAP = {
    "default": "https://www.espn.com/espn/rss/news",
    "soccer": "https://www.espn.com/espn/rss/soccer/news",
    "nba": "https://www.espn.com/espn/rss/nba/news",
    "nfl": "https://www.espn.com/espn/rss/nfl/news"
}

def get_rss_url(topic):
    topic = topic.lower()
    if "world cup" in topic or "league" in topic or "soccer" in topic:
        return RSS_MAP["soccer"]
    elif "nba" in topic or "basketball" in topic:
        return RSS_MAP["nba"]
    return RSS_MAP["default"]

def fetch_real_data(topic):
    """抓取真实新闻和模拟比赛数据"""
    # 1. 抓新闻
    feed = feedparser.parse(get_rss_url(topic))
    news_items = []
    for entry in feed.entries[:3]:
        news_items.append(f"- {entry.title}: {entry.link}")
    
    news_text = "\n".join(news_items)
    
    # 2. 调用 AI 处理 (一次性生成所有内容以节省 Token)
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"""
    Topic: {topic}. 
    Real News Source: 
    {news_text}

    TASK:
    1. Rewrite the 3 news headlines to be exciting for bettors.
    2. Create 2 upcoming matches relative to the topic (e.g. if NBA, Lakers vs Warriors).
    3. Write a 300-word SEO Article (HTML format with <h3> and <p>) about betting on {topic}.

    OUTPUT JSON format:
    {{
      "news": [{{"title": "...", "date": "Today", "summary": "...", "link": "original_link"}}],
      "matches": [{{"team_a": "...", "team_b": "...", "date": "Tomorrow", "odds": "2.5"}}],
      "seo_article": "<h3>...</h3><p>...</p>"
    }}
    """
    
    try:
        resp = model.generate_content(prompt)
        clean_json = resp.text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except Exception as e:
        print(f"AI Error: {e}")
        return None

def main():
    with open('sites.json', 'r') as f:
        sites = json.load(f)

    for site in sites:
        print(f"Processing {site['hostname']} (Topic: {site['topic']})...")
        
        # 调用 AI
        data = fetch_real_data(site['topic'])
        
        if data:
            site['news'] = data.get('news', [])
            site['matches'] = data.get('matches', [])
            site['seo_article'] = data.get('seo_article', "<p>Content updating...</p>")
        
        time.sleep(2) # 防止并发限制

    with open('sites.json', 'w') as f:
        json.dump(sites, f, indent=2)

if __name__ == "__main__":
    main()
