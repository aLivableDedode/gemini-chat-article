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
PROMPT_FILE_PATH = "html生成提示词"

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
            "temperature": 0.7, # HTML 排版需要更稳定的输出
            "maxOutputTokens": 4096  # HTML 代码可能较长
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

def generate_html(content: str) -> str:
    """
    读取提示词文件，替换内容占位符，并调用API生成HTML
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
    # 将提示词中的 {{content}} 替换为用户输入的文本内容
    final_prompt = template.replace("{{content}}", content)
    
    # 3. 调用 API
    return get_gemini_response(final_prompt)

def read_content_from_file(file_path: str) -> str:
    """
    从文件读取文本内容
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        raise FileNotFoundError(f"找不到文件: {file_path}")
    except Exception as e:
        raise Exception(f"读取文件失败: {e}")

# ================= 主程序入口 =================

if __name__ == "__main__":
    # 1. 获取输入内容
    user_content = None
    
    if len(sys.argv) > 1:
        # 如果第一个参数是文件路径，尝试读取文件
        arg = sys.argv[1]
        if os.path.isfile(arg):
            print(f"从文件读取内容: {arg}")
            user_content = read_content_from_file(arg)
        else:
            # 否则将参数作为直接输入的内容
            user_content = " ".join(sys.argv[1:])
    else:
        # 交互式输入
        print("="*50)
        print("请输入要转换为 HTML 的文本内容")
        print("(可以直接输入文本，或输入文件路径，或按 Ctrl+D 结束多行输入)")
        print("="*50)
        
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        
        user_content = "\n".join(lines).strip()
        
        # 如果输入的是文件路径，尝试读取
        if os.path.isfile(user_content):
            print(f"检测到文件路径，从文件读取: {user_content}")
            user_content = read_content_from_file(user_content)

    if not user_content:
        print("错误: 内容不能为空！")
        sys.exit(1)
    
    print(f"\n正在生成 HTML 排版...\n")
    print(f"原文预览（前100字符）: {user_content[:100]}...\n")

    try:
        # 2. 生成 HTML
        html_output = generate_html(user_content)
        
        # 3. 控制台输出
        print("-" * 20 + " 生成结果 " + "-" * 20)
        print(html_output)
        print("-" * 50)
        
        # 4. 保存文件
        output_filename = "output_html.html"
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(html_output)
            
        print(f"✅ HTML 已保存到: {output_filename}")

    except Exception as e:
        print(f"❌ 执行出错: {e}")
        sys.exit(1)

