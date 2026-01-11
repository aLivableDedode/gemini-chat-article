import requests
import json
import os
import sys
import logging
from urllib.parse import urlparse, urlunparse

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

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('gen_article.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def get_gemini_response(prompt: str) -> str:
    """
    请求 Gemini 接口并返回生成的文本内容。
    如果不成功，将抛出 Exception 供上层代码处理。
    
    :param prompt: 提示词字符串
    :return: 模型生成的纯文本
    """
    logger.info("=" * 80)
    logger.info("开始调用 Gemini API")
    logger.info(f"提示词长度: {len(prompt)} 字符")
    
    # 1. 安全检查
    if not API_KEY:
        logger.error("API_KEY 未设置")
        raise ValueError("环境变量 GEMINI_API_KEY 未设置！")
    
    # 记录 API_KEY 信息（隐藏敏感部分）
    api_key_preview = f"{API_KEY[:10]}...{API_KEY[-5:]}" if len(API_KEY) > 15 else "***"
    logger.info(f"API_KEY 长度: {len(API_KEY)}, 预览: {api_key_preview}")
    logger.info(f"BASE_URL: {BASE_URL}")
    logger.info(f"MODEL_NAME: {MODEL_NAME}")

    # 2. 构造 URL
    try:
        # 先尝试直接构造 URL
        url_with_key = f"{BASE_URL}/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"
        logger.info(f"构造的完整 URL (隐藏 key): {BASE_URL}/v1beta/models/{MODEL_NAME}:generateContent?key=***")
        
        # 验证 URL 格式
        parsed_url = urlparse(url_with_key)
        logger.info(f"URL 解析结果:")
        logger.info(f"  scheme: {parsed_url.scheme}")
        logger.info(f"  netloc: {parsed_url.netloc}")
        logger.info(f"  path: {parsed_url.path}")
        logger.info(f"  query 长度: {len(parsed_url.query)} 字符")
        logger.info(f"  query 预览: {parsed_url.query[:50]}...")
        
        # 检查 URL 中是否有特殊字符
        if any(ord(c) > 127 for c in url_with_key):
            logger.warning("URL 中包含非 ASCII 字符，可能导致编码问题")
        
        # 检查 API_KEY 中是否有特殊字符
        special_chars = [c for c in API_KEY if not c.isalnum() and c not in '-_./']
        if special_chars:
            logger.warning(f"API_KEY 中包含特殊字符: {set(special_chars)}")
        
    except Exception as e:
        logger.error(f"URL 构造或验证失败: {e}", exc_info=True)
        raise Exception(f"URL 构造失败: {e}")
    
    headers = {
        "Content-Type": "application/json"
    }
    logger.info(f"请求头: {headers}")

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
    logger.info(f"请求体大小: {len(json.dumps(payload))} 字节")

    # 3. 发送请求
    try:
        logger.info("准备发送 HTTP POST 请求...")
        logger.info(f"目标 URL: {BASE_URL}/v1beta/models/{MODEL_NAME}:generateContent")
        logger.info(f"超时设置: 180 秒")
        
        response = requests.post(url_with_key, headers=headers, json=payload, timeout=180)
        
        logger.info(f"请求已发送，收到响应")
        logger.info(f"响应状态码: {response.status_code}")
        logger.info(f"响应头: {dict(response.headers)}")
        logger.info(f"响应内容长度: {len(response.text)} 字符")
        
        # 检查 HTTP 状态码
        if response.status_code != 200:
            logger.error(f"API 请求失败，状态码: {response.status_code}")
            logger.error(f"响应内容 (前500字符): {response.text[:500]}")
            raise Exception(f"API 请求失败 [Code: {response.status_code}]: {response.text}")

        # 解析 JSON
        logger.info("开始解析 JSON 响应...")
        try:
            result = response.json()
            logger.info(f"JSON 解析成功，响应结构: {list(result.keys())}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            logger.error(f"响应内容 (前1000字符): {response.text[:1000]}")
            raise Exception(f"JSON 解析失败: {e}, 响应内容: {response.text[:500]}")
        
        # 提取文本
        try:
            logger.info("开始提取响应中的文本内容...")
            if 'candidates' not in result:
                logger.error(f"响应中缺少 'candidates' 字段，响应结构: {list(result.keys())}")
                raise Exception(f"响应结构异常，缺少 'candidates' 字段: {result}")
            
            if not result['candidates']:
                logger.error("响应中 'candidates' 为空")
                raise Exception("响应中 'candidates' 为空")
            
            candidate = result['candidates'][0]
            logger.info(f"找到候选结果，结构: {list(candidate.keys())}")
            
            if 'content' not in candidate:
                logger.error(f"候选结果中缺少 'content' 字段，结构: {list(candidate.keys())}")
                raise Exception(f"候选结果结构异常，缺少 'content' 字段: {candidate}")
            
            content_obj = candidate['content']
            if 'parts' not in content_obj:
                logger.error(f"content 中缺少 'parts' 字段，结构: {list(content_obj.keys())}")
                raise Exception(f"content 结构异常，缺少 'parts' 字段: {content_obj}")
            
            parts = content_obj['parts']
            logger.info(f"找到 {len(parts)} 个 parts")
            
            # 对于 thinking 模型，可能需要从多个 parts 中提取最终结果
            # 优先选择包含中文且不是思考过程的内容
            final_content = None
            all_texts = []
            
            for idx, part in enumerate(parts):
                logger.debug(f"处理 part {idx + 1}/{len(parts)}: {list(part.keys())}")
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
                logger.info(f"提取到最终内容，长度: {len(final_content)} 字符")
                logger.debug(f"内容预览 (前200字符): {final_content[:200]}")
                
                # 如果内容包含思考过程标记，尝试提取中文部分
                if '**Reflections' in final_content or 'Okay, here' in final_content:
                    logger.info("检测到思考过程标记，尝试提取中文部分...")
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
                        logger.info(f"提取到 {len(chinese_lines)} 行中文内容")
                        final_content = '\n'.join(chinese_lines)
                
                logger.info("=" * 80)
                logger.info("API 调用成功完成")
                return final_content.strip()
            else:
                logger.error("未能从响应中提取有效内容")
                logger.error(f"all_texts 数量: {len(all_texts)}")
                logger.error(f"parts 数量: {len(parts)}")
                raise Exception("未能从响应中提取有效内容")
                
        except (KeyError, IndexError) as e:
            logger.error(f"数据解析失败: {e}", exc_info=True)
            logger.error(f"响应结构: {json.dumps(result, indent=2, ensure_ascii=False)[:1000]}")
            raise Exception(f"数据解析失败，返回结构异常: {result}, 错误: {e}")

    except requests.exceptions.InvalidURL as e:
        logger.error(f"无效的 URL: {e}", exc_info=True)
        logger.error(f"尝试使用的 URL: {BASE_URL}/v1beta/models/{MODEL_NAME}:generateContent?key=***")
        raise Exception(f"无效的 URL: {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"网络连接异常: {e}", exc_info=True)
        logger.error(f"异常类型: {type(e).__name__}")
        raise Exception(f"网络连接异常: {e}")
    except Exception as e:
        logger.error(f"未预期的错误: {e}", exc_info=True)
        logger.error(f"异常类型: {type(e).__name__}")
        logger.error(f"异常消息: {str(e)}")
        raise

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
    logger.info("=" * 80)
    logger.info("开始生成短文")
    logger.info(f"主题: {topic}")
    logger.info(f"模板文件: {template_file}")
    
    # 1. 读取模板
    try:
        logger.info("读取提示词模板...")
        template = load_prompt_template(template_file)
        logger.info(f"模板读取成功，长度: {len(template)} 字符")
    except Exception as e:
        logger.error(f"读取模板失败: {e}", exc_info=True)
        raise
    
    # 2. 替换主题占位符
    logger.info("替换主题占位符...")
    prompt = template.replace("[在此输入你的主题]", topic)
    logger.info(f"替换后提示词长度: {len(prompt)} 字符")
    
    # 3. 添加明确指令：只返回最终的中文短文，不要包含思考过程
    prompt += "\n\n**重要提示**：请直接输出最终的中文短文，不要包含任何思考过程、英文内容或中间步骤。只返回按照上述框架创作的中文短文正文。"
    logger.info(f"添加指令后提示词长度: {len(prompt)} 字符")
    
    # 4. 调用API生成短文
    logger.info("准备调用 API 生成短文...")
    try:
        result = get_gemini_response(prompt)
        logger.info(f"短文生成成功，长度: {len(result)} 字符")
        return result
    except Exception as e:
        logger.error(f"生成短文失败: {e}", exc_info=True)
        raise

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

