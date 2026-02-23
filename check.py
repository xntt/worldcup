import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("❌ 没有找到 API KEY")
else:
    genai.configure(api_key=api_key)
    try:
        print("正在尝试列出可用模型...")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"✅ 可用模型: {m.name}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("提示：如果你在国内，请确保 VPN 开启，并在代码中设置代理。")