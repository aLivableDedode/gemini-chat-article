"""
Coze API调用服务
"""
import requests
import os
from typing import Dict, Optional
from utils.logger import logger

# Coze API配置
COZE_API_URL = "https://api.coze.cn/v1/workflow/stream_run"
COZE_WORKFLOW_ID = "7590055614313087003"


def _get_coze_authorization() -> str:
    """获取Coze API授权令牌"""
    # 优先使用完整的Bearer token
    token = os.getenv("COZE_API_TOKEN", "")
    if token:
        # 如果已经包含Bearer前缀，直接返回
        if token.startswith("Bearer "):
            return token
        # 否则添加Bearer前缀
        return f"Bearer {token}"
    
    # 备用：使用单独的bearer token
    bearer_token = os.getenv("COZE_BEARER_TOKEN", "")
    if bearer_token:
        return f"Bearer {bearer_token}"
    
    # 如果都没有设置，返回空字符串（会在调用时报错）
    logger.warning("Coze API授权令牌未设置，请设置环境变量 COZE_API_TOKEN 或 COZE_BEARER_TOKEN")
    return ""


def call_coze_api(title: str, content: str) -> Dict:
    """
    调用Coze API接口
    
    :param title: 标题
    :param content: 内容（HTML）
    :return: API响应结果字典
    """
    logger.info(f"开始调用Coze API: title='{title}', content_length={len(content)}")
    
    authorization = _get_coze_authorization()
    if not authorization:
        raise ValueError("错误：环境变量 COZE_API_TOKEN 或 COZE_BEARER_TOKEN 未设置！")
    
    headers = {
        "Authorization": authorization,
        "Content-Type": "application/json"
    }
    
    payload = {
        "workflow_id": COZE_WORKFLOW_ID,
        "parameters": {
            "title": title,
            "content": content
        }
    }
    
    try:
        logger.debug(f"发送请求到Coze API: {COZE_API_URL}")
        response = requests.post(COZE_API_URL, headers=headers, json=payload, timeout=120)
        
        logger.info(f"Coze API响应状态码: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Coze API请求失败: status_code={response.status_code}, response={response.text[:200]}")
            raise Exception(f"Coze API 请求失败 [Code: {response.status_code}]: {response.text}")
        
        # 尝试解析JSON响应
        try:
            result = response.json()
            logger.info(f"Coze API调用成功，返回数据: {result}")
            return result
        except ValueError:
            # 如果不是JSON，返回文本内容
            logger.warning(f"Coze API返回非JSON格式，返回文本内容")
            return {
                'success': True,
                'raw_response': response.text
            }
    except requests.exceptions.RequestException as e:
        logger.error(f"Coze API网络连接异常: {e}", exc_info=True)
        raise Exception(f"网络连接异常: {e}")
    except Exception as e:
        logger.error(f"Coze API调用失败: {e}", exc_info=True)
        raise

