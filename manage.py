import os
import json
import markdown
from jinja2 import Template
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# 配置模型
model = None
if api_key:
    try:
        genai.configure(api_key=api_key)
        # 使用你列表里确认可用的模型
        model = genai.GenerativeModel('models/gemini-2.5-flash-lite')
    except Exception as e:
        print(f"⚠️ AI 配置出错: {e}")

# 读取数据
try:
    with open('sites.json', 'r', encoding='utf-8') as f:
        sites = json.load(f)
except FileNotFoundError:
    sites = []

# 读取模板
try:
    with open('template.html', 'r', encoding='utf-8') as f:
        template_str = f.read()
    template = Template(template_str)
except FileNotFoundError:
    print("❌ 找不到 template.html")
    exit()

print(f"🚀 开始构建 {len(sites)} 个站点...\n")

# 用于生成首页导航列表
links = []

for site in sites:
    hostname = site.get('hostname', 'unknown')
    topic = site.get('topic', 'General')
    
    # 记录链接，方便生成总首页
    links.append({'name': hostname, 'url': f"{hostname}/index.html"})

    print(f"[{hostname}] ⚙️ 处理中...")
    
    ai_content = "<p>Default Content</p>"
    if model:
        try:
            prompt = f"Write a short intro article about {topic} in Markdown."
            response = model.generate_content(prompt)
            if response.text:
                ai_content = markdown.markdown(response.text)
        except Exception as e:
            print(f"[{hostname}] AI Error: {e}")

    # 渲染子站点
    html = template.render(site=site, ai_content=ai_content)
    
    # 保存子站点
    output_dir = f"dist/{hostname}"
    os.makedirs(output_dir, exist_ok=True)
    with open(f"{output_dir}/index.html", "w", encoding='utf-8') as f:
        f.write(html)

# --- 新增：生成根目录的导航首页 (index.html) ---
index_html = """
<!DOCTYPE html>
<html>
<head>
    <title>World Cup Sites Hub</title>
    <style>
        body { font-family: sans-serif; padding: 40px; max-width: 800px; margin: 0 auto; }
        h1 { color: #333; }
        ul { list-style: none; padding: 0; }
        li { margin: 10px 0; border: 1px solid #ddd; padding: 15px; border-radius: 8px; }
        a { text-decoration: none; color: #0070f3; font-weight: bold; font-size: 1.2em; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>🌍 站点列表 / Sites Dashboard</h1>
    <p>以下是已生成的站点入口：</p>
    <ul>
"""

for link in links:
    index_html += f'<li>👉 <a href="{link["url"]}">{link["name"]}</a></li>'

index_html += """
    </ul>
</body>
</html>
"""

# 保存总首页到 dist/index.html
with open("dist/index.html", "w", encoding='utf-8') as f:
    f.write(index_html)

print("\n🎉 全部完成！已生成 dist/index.html 导航页。")