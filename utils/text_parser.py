"""
文本解析工具
"""
import re
from typing import List


def parse_titles(raw_text: str) -> List[str]:
    """
    解析标题文本，去除空行、编号等，返回标题列表
    
    :param raw_text: 原始标题文本（可能包含编号、空行等）
    :return: 清理后的标题列表
    """
    if not raw_text:
        return []
    
    lines = raw_text.strip().split('\n')
    titles = []
    
    for line in lines:
        line = line.strip()
        
        # 跳过空行
        if not line:
            continue
        
        # 去除常见的编号格式：1. 2. 3. 或 1、2、3、 或 (1) (2) 等
        line = re.sub(r'^\d+[\.、\)]\s*', '', line)
        line = re.sub(r'^\(\d+\)\s*', '', line)
        line = re.sub(r'^第\d+[个条项]\s*', '', line)
        
        # 去除开头的 * - • 等列表标记
        line = re.sub(r'^[\*\-\•]\s*', '', line)
        
        # 去除首尾的引号
        line = line.strip('"\'「」『』')
        
        # 如果还有内容，添加到列表
        if line:
            titles.append(line)
    
    return titles

