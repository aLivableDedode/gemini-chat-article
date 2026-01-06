import requests
import json
import os
import sys

# ================= 配置区域 =================

# 从环境变量获取 Key
API_KEY = os.getenv("GEMINI_API_KEY")
BASE_URL = "http://1003.2.gptuu.cc:1003"
MODEL_NAME = "gemini-3-pro-preview-thinking"

# ===========================================

def get_gemini_response(prompt: str) -> str:
    """
    请求 Gemini 接口并返回生成的文本内容。
    如果不成功，将抛出 Exception 供上层代码处理。
    
    :param prompt: 提示词字符串
    :return: 模型生成的纯文本
    """
    
    # 1. 安全检查
    if not API_KEY:
        raise ValueError("环境变量 GEMINI_API_KEY 未设置！")

    # 2. 构造 URL
    url = f"{BASE_URL}/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"
    
    headers = {
        "Content-Type": "application/json"
    }

    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 8192
        }
    }

    # 3. 发送请求
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        
        # 检查 HTTP 状态码
        if response.status_code != 200:
            raise Exception(f"API 请求失败 [Code: {response.status_code}]: {response.text}")

        # 解析 JSON
        result = response.json()
        
        # 提取文本
        try:
            content = result['candidates'][0]['content']['parts'][0]['text']
            return content
        except (KeyError, IndexError):
            raise Exception(f"数据解析失败，返回结构异常: {result}")

    except requests.exceptions.RequestException as e:
        raise Exception(f"网络连接异常: {e}")

# ================= 标题生成功能 =================

def load_prompt_template(template_file: str = "标题生成提示词") -> str:
    """
    读取提示词模板文件
    
    :param template_file: 模板文件路径
    :return: 模板内容字符串
    """
    try:
        with open(template_file, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"提示词模板文件 '{template_file}' 不存在！")
    except Exception as e:
        raise Exception(f"读取模板文件失败: {e}")

def generate_titles(topic: str, template_file: str = "标题生成提示词") -> str:
    """
    根据主题生成标题
    
    :param topic: 文章主题
    :param template_file: 提示词模板文件路径
    :return: 生成的标题内容
    """
    # 1. 读取模板
    template = load_prompt_template(template_file)
    
    # 2. 替换主题占位符
    prompt = template.replace("[这里填写你的主题]", topic)
    
    # 3. 添加明确指令：只返回中文标题，不要包含思考过程
    prompt += "\n\n**重要提示**：请直接输出中文标题列表，不要包含任何思考过程、英文内容或中间步骤。只返回按照上述要求生成的中文标题，每个标题一行。"
    
    # 4. 调用API生成标题
    return get_gemini_response(prompt)

# ================= 主程序入口 =================

if __name__ == "__main__":
    # 从命令行参数获取主题，如果没有则提示用户输入
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
    else:
        topic = input("请输入文章主题: ").strip()
        if not topic:
            print("错误: 主题不能为空！")
            sys.exit(1)
    
    print(f"主题: {topic}")
    print("正在生成标题...")

    try:
        # 生成标题
        titles = generate_titles(topic)
        
        # 输出结果
        print("\n" + "="*50)
        print("生成的标题:")
        print("="*50)
        print(titles)
        print("="*50)
        
        # 保存到文件
        with open("output_data.txt", "w", encoding="utf-8") as f:
            f.write(f"主题: {topic}\n\n")
            f.write(titles)
            
        print(f"\n标题已保存到 output_data.txt 文件")

    except Exception as e:
        # 捕获所有可能的错误（网络错误、Key错误、解析错误、文件错误）
        print(f"流程执行出错: {e}")
        sys.exit(1)
