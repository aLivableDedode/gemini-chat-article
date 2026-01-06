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

    url = f"{BASE_URL}/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"

    headers = {"Content-Type": "application/json"}

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens
        }
    }

    try:
        logger.debug(f"发送API请求到: {BASE_URL}, 模型: {MODEL_NAME}")
        response = requests.post(url, headers=headers, json=payload, timeout=60)

        if response.status_code != 200:
            logger.error(f"API请求失败: status_code={response.status_code}, response={response.text[:200]}")
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

