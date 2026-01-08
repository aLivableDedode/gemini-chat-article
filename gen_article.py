import requests
import json
import os
import sys

# ================= 配置区域 =================

# 从环境变量获取 Key
# 从config模块获取配置（优先）
try:
    from config import API_KEY, BASE_URL, MODEL_NAME
except ImportError:
    # 如果config模块不存在，从环境变量获取
    API_KEY = os.getenv("GEMINI_API_KEY")
    BASE_URL = os.getenv("GEMINI_BASE_URL", "http://1003.2.gptuu.cc:1003")
    MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-3-pro-preview")
MODEL_NAME = "gemini-3-pro-preview"

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
        response = requests.post(url, headers=headers, json=payload, timeout=180)
        
        # 检查 HTTP 状态码
        if response.status_code != 200:
            raise Exception(f"API 请求失败 [Code: {response.status_code}]: {response.text}")

        # 解析 JSON
        result = response.json()
        
        # 提取文本
        try:
            candidate = result['candidates'][0]
            content_obj = candidate['content']
            parts = content_obj['parts']
            
            # 对于 thinking 模型，可能需要从多个 parts 中提取最终结果
            # 优先选择包含中文且不是思考过程的内容
            final_content = None
            all_texts = []
            
            for part in parts:
                if 'text' in part:
                    text = part['text']
                    all_texts.append(text)
                    
                    # 检查是否是思考过程（通常包含英文的思考标记）
                    is_thinking = (
                        text.strip().startswith('**Reflections') or 
                        text.strip().startswith('Okay, here') or
                        'running through my mind' in text.lower() or
                        'I\'m thinking' in text or
                        'I need to' in text and 'I want to' in text
                    )
                    
                    # 检查是否包含中文内容
                    has_chinese = any('\u4e00' <= char <= '\u9fff' for char in text)
                    
                    # 如果包含中文且不是思考过程，优先使用
                    if has_chinese and not is_thinking:
                        final_content = text
                        break
            
            # 如果没找到，使用最后一个文本部分（通常是最终输出）
            if final_content is None and all_texts:
                final_content = all_texts[-1]
            
            # 如果仍然没找到，使用第一个文本部分
            if final_content is None and parts:
                final_content = parts[0].get('text', '')
            
            if final_content:
                # 如果内容包含思考过程标记，尝试提取中文部分
                if '**Reflections' in final_content or 'Okay, here' in final_content:
                    # 尝试找到中文段落（通常在思考过程之后）
                    lines = final_content.split('\n')
                    chinese_lines = []
                    found_chinese_section = False
                    for line in lines:
                        # 跳过明显的思考过程标记
                        if line.strip().startswith('**Reflections') or 'running through my mind' in line.lower():
                            continue
                        # 如果找到包含中文的行，开始收集
                        if any('\u4e00' <= char <= '\u9fff' for char in line):
                            found_chinese_section = True
                            chinese_lines.append(line)
                        elif found_chinese_section and line.strip():
                            # 继续收集后续的中文内容
                            chinese_lines.append(line)
                    
                    if chinese_lines:
                        final_content = '\n'.join(chinese_lines)
                
                return final_content.strip()
            else:
                raise Exception("未能从响应中提取有效内容")
                
        except (KeyError, IndexError) as e:
            raise Exception(f"数据解析失败，返回结构异常: {result}, 错误: {e}")

    except requests.exceptions.RequestException as e:
        raise Exception(f"网络连接异常: {e}")

# ================= 短文生成功能 =================

def load_prompt_template(template_file: str = "qx-短文提示词") -> str:
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

def generate_article(topic: str, template_file: str = "qx-短文提示词") -> str:
    """
    根据主题生成短文
    
    :param topic: 文章主题（通常是标题）
    :param template_file: 提示词模板文件路径
    :return: 生成的短文内容
    """
    # 1. 读取模板
    template = load_prompt_template(template_file)
    
    # 2. 替换主题占位符
    prompt = template.replace("[在此输入你的主题]", topic)
    
    # 3. 添加明确指令：只返回最终的中文短文，不要包含思考过程
    prompt += "\n\n**重要提示**：请直接输出最终的中文短文，不要包含任何思考过程、英文内容或中间步骤。只返回按照上述框架创作的中文短文正文。"
    
    # 4. 调用API生成短文
    return get_gemini_response(prompt)

# ================= 主程序入口 =================

if __name__ == "__main__":
    # 从命令行参数获取主题，如果没有则提示用户输入
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
    else:
        topic = input("请输入文章主题（标题）: ").strip()
        if not topic:
            print("错误: 主题不能为空！")
            sys.exit(1)
    
    print(f"主题: {topic}")
    print("正在生成短文...")

    try:
        # 生成短文
        article = generate_article(topic)
        
        # 输出结果
        print("\n" + "="*50)
        print("生成的短文:")
        print("="*50)
        print(article)
        print("="*50)
        
        # 保存到文件
        with open("output_article.txt", "w", encoding="utf-8") as f:
            f.write(f"主题: {topic}\n\n")
            f.write(article)
            
        print(f"\n短文已保存到 output_article.txt 文件")

    except Exception as e:
        # 捕获所有可能的错误（网络错误、Key错误、解析错误、文件错误）
        print(f"流程执行出错: {e}")
        sys.exit(1)

