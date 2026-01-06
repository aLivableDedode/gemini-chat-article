import requests
import json
import os
import sys

# ================= 配置区域 =================

# 从环境变量获取 Key (请确保已设置 GEMINI_API_KEY)
API_KEY = os.getenv("GEMINI_API_KEY")
BASE_URL = "http://1003.2.gptuu.cc:1003"
# 注意：如果该模型版本不稳定，可尝试更换为 "gemini-1.5-pro-latest"
MODEL_NAME = "gemini-3-pro-preview" 

# 提示词文件路径
PROMPT_FILE_PATH = "标题生成提示词"

# ================= 核心功能函数 =================

def get_gemini_response(prompt: str) -> str:
    """
    请求 Gemini 接口并返回生成的文本内容。
    """
    if not API_KEY:
        raise ValueError("错误：环境变量 GEMINI_API_KEY 未设置！")

    url = f"{BASE_URL}/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"
    
    headers = {"Content-Type": "application/json"}

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.8, # 稍微调高一点创造性，毒舌更狠
            "maxOutputTokens": 2048
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code != 200:
            raise Exception(f"API 请求失败 [Code: {response.status_code}]: {response.text}")

        result = response.json()
        
        # 尝试提取文本
        try:
            content = result['candidates'][0]['content']['parts'][0]['text']
            return content.strip() # 去除首尾空格
        except (KeyError, IndexError):
            # 兼容某些情况下没有content但有finishReason的情况
            raise Exception(f"数据解析失败，API可能拒绝了生成: {result}")

    except requests.exceptions.RequestException as e:
        raise Exception(f"网络连接异常: {e}")

def generate_titles(topic: str) -> str:
    """
    读取提示词文件，替换主题，并调用API
    """
    # 1. 读取模板文件
    try:
        if not os.path.exists(PROMPT_FILE_PATH):
            raise FileNotFoundError(f"找不到提示词文件: {PROMPT_FILE_PATH}")
            
        with open(PROMPT_FILE_PATH, "r", encoding="utf-8") as f:
            template = f.read()
    except Exception as e:
        raise Exception(f"读取提示词模板失败: {e}")

    # 2. 关键步骤：替换占位符
    # 将 prompt.txt 中的 {{topic}} 替换为用户输入的 topic
    final_prompt = template.replace("{{topic}}", topic)
    
    # 3. 调用 API
    return get_gemini_response(final_prompt)

# ================= 主程序入口 =================

if __name__ == "__main__":
    # 1. 获取输入
    if len(sys.argv) > 1:
        user_topic = " ".join(sys.argv[1:])
    else:
        print("="*50)
        user_topic = input("请输入文章主题 (例如: 职场甩锅): ").strip()
        print("="*50)

    if not user_topic:
        print("错误: 主题不能为空！")
        sys.exit(1)
    
    print(f"正在为主题【{user_topic}】生成毒舌标题...\n")

    try:
        # 2. 生成标题
        titles = generate_titles(user_topic)
        
        # 3. 控制台输出
        print("-" * 20 + " 生成结果 " + "-" * 20)
        print(titles)
        print("-" * 50)
        
        # 4. 保存文件
        output_filename = "output_titles.txt"
        # 使用追加模式 'a'，这样可以记录多次生成的结果，如果想覆盖用 'w'
        with open(output_filename, "a", encoding="utf-8") as f:
            f.write(f"\n\n=== 主题: {user_topic} ===\n")
            f.write(titles)
            
        print(f"✅ 结果已追加保存到: {output_filename}")

    except Exception as e:
        print(f"❌ 执行出错: {e}")
        sys.exit(1)
