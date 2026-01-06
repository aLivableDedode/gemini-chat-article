"""
Coze API调用服务
"""
import requests
import os
import json
from typing import Dict, Optional
from utils.logger import logger

# Coze API配置
COZE_API_URL = "https://api.coze.cn/v1/workflow/stream_run"
# workflow_id 可以从环境变量获取，如果没有则使用默认值
COZE_WORKFLOW_ID = os.getenv("COZE_WORKFLOW_ID", "7590055614313087003")

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
    
    # 尝试将 workflow_id 转换为整数（如果可能）
    # 某些 API 可能需要整数类型而不是字符串
    try:
        workflow_id = int(COZE_WORKFLOW_ID)
        logger.debug(f"使用整数格式的 workflow_id: {workflow_id}")
    except (ValueError, TypeError):
        workflow_id = COZE_WORKFLOW_ID
        logger.debug(f"使用字符串格式的 workflow_id: {workflow_id}")
    
    payload = {
        "workflow_id": workflow_id,
        "parameters": {
            "title": str(title).strip(),
            "content": str(content).strip()
        }
    }
    
    # 验证参数不为空
    if not payload["parameters"]["title"]:
        raise ValueError("标题不能为空")
    if not payload["parameters"]["content"]:
        raise ValueError("内容不能为空")
    
    try:
        logger.debug(f"发送请求到Coze API: {COZE_API_URL}")
        logger.debug(f"请求负载: workflow_id={COZE_WORKFLOW_ID}, title_length={len(title)}, content_length={len(content)}")
        response = requests.post(COZE_API_URL, headers=headers, json=payload, timeout=120)
        
        logger.info(f"Coze API响应状态码: {response.status_code}")
        
        # 尝试解析响应（无论状态码如何）
        result = None
        response_text = response.text
        
        # 首先尝试解析为 JSON
        try:
            result = response.json()
            logger.debug(f"Coze API响应内容 (JSON): {result}")
        except ValueError:
            # 如果不是 JSON，可能是流式响应（SSE格式）或纯文本
            logger.debug(f"Coze API响应不是JSON格式，响应长度: {len(response_text)}")
            
            # 检查是否是 SSE 格式（Server-Sent Events）
            if response_text.startswith('data:') or '\ndata:' in response_text:
                logger.info("检测到SSE格式响应，尝试解析流式数据")
                # 解析 SSE 格式
                lines = response_text.strip().split('\n')
                sse_data = []
                for line in lines:
                    if line.startswith('data:'):
                        data_str = line[5:].strip()  # 移除 'data:' 前缀
                        if data_str:
                            try:
                                sse_data.append(json.loads(data_str))
                            except (ValueError, json.JSONDecodeError):
                                sse_data.append(data_str)
                
                if sse_data:
                    # 合并所有 SSE 数据
                    if len(sse_data) == 1:
                        result = sse_data[0]
                    else:
                        result = {'stream_data': sse_data, 'raw_response': response_text[:1000]}
                    logger.debug(f"解析SSE数据成功，共 {len(sse_data)} 条")
            else:
                # 纯文本响应，尝试提取有用信息
                logger.info("响应为纯文本格式")
                result = None
        
        if response.status_code != 200:
            error_msg = "未知错误"
            error_code = None
            
            if result:
                # 尝试从JSON响应中提取错误信息
                if isinstance(result, dict):
                    # 优先检查 Coze API 的错误格式
                    if 'error_code' in result or 'error_message' in result:
                        error_code = result.get('error_code', '未知')
                        error_message = result.get('error_message', result.get('message', '未知错误'))
                        logger.error(f"Coze API请求失败: status_code={response.status_code}, error_code={error_code}, error_message={error_message}")
                        
                        # 针对特定错误码提供更友好的提示
                        if error_code == 4200:
                            raise Exception(f"Workflow 不存在 (HTTP {response.status_code}, 错误码: {error_code})。请检查 COZE_WORKFLOW_ID 是否正确，当前值: {COZE_WORKFLOW_ID}。错误详情: {error_message}")
                        else:
                            raise Exception(f"Coze API 请求失败 [HTTP {response.status_code}, 错误码: {error_code}]: {error_message}")
                    
                    # 其他错误格式
                    error_msg = result.get('message', result.get('error', result.get('detail', str(result))))
                    # 如果是嵌套的错误信息
                    if 'error' in result and isinstance(result['error'], dict):
                        error_msg = result['error'].get('message', error_msg)
                else:
                    error_msg = str(result)
            else:
                error_msg = response.text[:500]  # 限制错误信息长度
            
            logger.error(f"Coze API请求失败: status_code={response.status_code}, error={error_msg}")
            raise Exception(f"Coze API 请求失败 [HTTP {response.status_code}]: {error_msg}")
        
        # 检查响应中是否包含错误信息（无论状态码如何）
        if result and isinstance(result, dict):
            # 检查 Coze API 的错误格式：error_code 和 error_message
            if 'error_code' in result or 'error_message' in result:
                error_code = result.get('error_code', '未知')
                error_message = result.get('error_message', result.get('message', '未知错误'))
                logger.error(f"Coze API返回错误: error_code={error_code}, error_message={error_message}")
                
                # 针对特定错误码提供更友好的提示
                if error_code == 4200:
                    raise Exception(f"Workflow 不存在 (错误码: {error_code})。请检查 COZE_WORKFLOW_ID 是否正确，当前值: {COZE_WORKFLOW_ID}。错误详情: {error_message}")
                else:
                    raise Exception(f"Coze API 错误 (错误码: {error_code}): {error_message}")
            
            # 检查是否有错误字段
            if 'error' in result:
                error_msg = result.get('error')
                if isinstance(error_msg, dict):
                    error_msg = error_msg.get('message', str(error_msg))
                logger.error(f"Coze API返回错误信息: {error_msg}")
                raise Exception(f"Coze API 错误: {error_msg}")
            
            # 检查 message 字段是否包含错误信息
            if 'message' in result:
                message = str(result.get('message', ''))
                if 'error' in message.lower() or 'fail' in message.lower():
                    logger.error(f"Coze API返回错误信息: {message}")
                    raise Exception(f"Coze API 错误: {message}")
        
        # 格式化返回结果
        if result:
            logger.info(f"Coze API调用成功，返回数据: {type(result).__name__}")
            return result
        else:
            # 返回文本响应，限制长度并格式化
            text_response = response_text[:5000]  # 限制长度
            logger.info(f"Coze API返回文本响应，长度: {len(text_response)}")
            return {
                'success': True,
                'response_type': 'text',
                'content': text_response,
                'full_length': len(response_text)
            }
    except requests.exceptions.RequestException as e:
        logger.error(f"Coze API网络连接异常: {e}", exc_info=True)
        raise Exception(f"网络连接异常: {e}")
    except Exception as e:
        logger.error(f"Coze API调用失败: {e}", exc_info=True)
        raise

