"""
公共 API 调用工具
"""
import requests
import os
from utils.logger import logger


def get_gemini_response(prompt: str, temperature: float = 0.7, max_tokens: int = 4096) -> str:
    """
    请求 Gemini 接口并返回生成的文本内容
    
    :param prompt: 提示词字符串
    :param temperature: 温度参数，控制创造性（0.0-1.0）
    :param max_tokens: 最大输出token数
    :return: 模型生成的纯文本
    """
    API_KEY = os.getenv("GEMINI_API_KEY")
    BASE_URL = "http://1003.2.gptuu.cc:1003"
    MODEL_NAME = "gemini-3-pro-preview"

    logger.info(f"开始调用Gemini API: temperature={temperature}, max_tokens={max_tokens}, prompt_length={len(prompt)}")
    
    if not API_KEY:
        logger.error("GEMINI_API_KEY 未设置")
        raise ValueError("错误：环境变量 GEMINI_API_KEY 未设置！")
    
    # 诊断信息：检查API_KEY格式
    api_key_preview = f"{API_KEY[:10]}...{API_KEY[-5:]}" if len(API_KEY) > 15 else "***"
    logger.info(f"API_KEY 诊断信息: 长度={len(API_KEY)}, 预览={api_key_preview}")
    
    # 检查API_KEY是否包含换行符或空格
    if '\n' in API_KEY or '\r' in API_KEY:
        logger.warning("API_KEY 包含换行符，正在清理...")
        API_KEY = API_KEY.strip().replace('\n', '').replace('\r', '')
        logger.info(f"清理后的API_KEY长度: {len(API_KEY)}")
    
    # 检查API_KEY是否包含前后空格
    if API_KEY != API_KEY.strip():
        logger.warning("API_KEY 包含前后空格，正在清理...")
        API_KEY = API_KEY.strip()
        logger.info(f"清理后的API_KEY长度: {len(API_KEY)}")

    # 构造URL（不包含key）
    url = f"{BASE_URL}/v1beta/models/{MODEL_NAME}:generateContent"

    # 设置请求头
    headers = {
        "Content-Type": "application/json"
    }
    
    # 检查API_KEY是否是占位符
    if "your_gemin" in API_KEY.lower() or "your_api_key" in API_KEY.lower() or "placeholder" in API_KEY.lower():
        logger.error(f"API_KEY 看起来是占位符文本，请检查 .env 文件中的 GEMINI_API_KEY 配置")
        raise ValueError("API_KEY 配置错误：检测到占位符文本，请设置真实的 API key")

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens
        }
    }

    try:
        logger.debug(f"发送API请求到: {BASE_URL}, 模型: {MODEL_NAME}")
        logger.debug(f"请求URL: {url}")
        logger.debug(f"请求方式: POST")
        
        # 尝试方式1: 使用 X-Goog-Api-Key header（Gemini API 标准方式）
        headers_with_key = {**headers, "X-Goog-Api-Key": API_KEY}
        logger.debug(f"尝试方式1: 使用 X-Goog-Api-Key header")
        
        response = requests.post(
            url, 
            headers=headers_with_key, 
            json=payload, 
            timeout=60
        )
        
        # 如果401错误，尝试方式2: 使用URL参数（兼容旧方式）
        if response.status_code == 401:
            logger.warning("方式1失败（401），尝试方式2: 使用URL参数传递key")
            response = requests.post(
                url, 
                headers=headers, 
                json=payload, 
                params={"key": API_KEY},
                timeout=60
            )
        
        # 记录实际请求的URL（隐藏key部分）
        actual_url = response.url if hasattr(response, 'url') else url
        if 'key=' in actual_url:
            # 隐藏key部分
            safe_url = actual_url.split('key=')[0] + 'key=***'
            logger.debug(f"实际请求URL: {safe_url}")
        else:
            logger.debug(f"实际请求URL: {actual_url}")

        if response.status_code != 200:
            logger.error(f"API请求失败: status_code={response.status_code}")
            logger.error(f"响应内容: {response.text[:500]}")
            logger.error(f"请求URL (隐藏key): {url}?key=***")
            raise Exception(f"API 请求失败 [Code: {response.status_code}]: {response.text}")

        result = response.json()

        # 尝试提取文本
        try:
            content = result['candidates'][0]['content']['parts'][0]['text']
            logger.info(f"API调用成功，返回内容长度: {len(content)} 字符")
            return content.strip()
        except (KeyError, IndexError) as e:
            logger.error(f"数据解析失败: {e}, result={result}")
            # 兼容某些情况下没有content但有finishReason的情况
            raise Exception(f"数据解析失败，API可能拒绝了生成: {result}")

    except requests.exceptions.RequestException as e:
        logger.error(f"网络连接异常: {e}", exc_info=True)
        raise Exception(f"网络连接异常: {e}")

