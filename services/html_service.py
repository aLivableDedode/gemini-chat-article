"""
HTML生成服务
"""
from typing import Tuple, Optional
import os
from utils.api import get_gemini_response
from database import get_db_session
from models import HTMLOutput
from utils.logger import logger


def load_prompt_template(template_id: Optional[int] = None) -> str:
    """读取提示词模板"""
    from database import get_db_session
    from models import PromptTemplate
    
    db = get_db_session()
    try:
        if template_id:
            template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
            if template:
                return template.content
        
        # 使用默认模板
        template = db.query(PromptTemplate).filter(
            PromptTemplate.category == "html",
            PromptTemplate.is_default == True
        ).first()
        
        if not template:
            # 如果没有默认模板，返回第一个
            template = db.query(PromptTemplate).filter(
                PromptTemplate.category == "html"
            ).first()
        
        if template:
            return template.content
    finally:
        db.close()
    
    # 向后兼容：如果数据库中没有，尝试从文件加载
    PROMPT_FILE_PATH = "html生成提示词"
    if os.path.exists(PROMPT_FILE_PATH):
        with open(PROMPT_FILE_PATH, "r", encoding="utf-8") as f:
            return f.read()
    
    raise FileNotFoundError("找不到提示词模板")


def generate_html(article_text: str, template_id: Optional[int] = None) -> Tuple[str, str, Optional[int]]:
    """
    生成HTML
    
    :param article_text: 短文内容
    :param template_id: 提示词模板ID（可选）
    :return: (HTML内容, 完整提示词, 模板ID)
    """
    # 1. 读取模板
    template_content = load_prompt_template(template_id)
    
    # 2. 获取模板ID
    from database import get_db_session
    from models import PromptTemplate
    
    db = get_db_session()
    try:
        if template_id:
            used_template_id = template_id
        else:
            # 获取默认模板ID
            default_template = db.query(PromptTemplate).filter(
                PromptTemplate.category == "html",
                PromptTemplate.is_default == True
            ).first()
            if not default_template:
                default_template = db.query(PromptTemplate).filter(
                    PromptTemplate.category == "html"
                ).first()
            used_template_id = default_template.id if default_template else None
    finally:
        db.close()
    
    # 3. 替换占位符
    final_prompt = template_content.replace("{{content}}", article_text)
    
    # 4. 调用 API
    html_content = get_gemini_response(final_prompt, temperature=0.7, max_tokens=4096)
    
    return html_content, final_prompt, used_template_id


def save_html_to_db(article_id: int, html_content: str, prompt_text: str, template_id: Optional[int] = None) -> int:
    """
    保存HTML和提示词到数据库
    
    :param article_id: 短文ID
    :param html_content: HTML内容
    :param prompt_text: 完整提示词
    :return: 保存的HTML输出ID
    """
    logger.info(f"开始保存HTML到数据库: article_id={article_id}, html_length={len(html_content)}")
    db = get_db_session()
    try:
        html_output = HTMLOutput(
            article_id=article_id,
            html_content=html_content,
            prompt_text=prompt_text,
            prompt_template_id=template_id
        )
        db.add(html_output)
        db.commit()
        logger.info(f"HTML保存成功，ID: {html_output.id}")
        return html_output.id
    except Exception as e:
        db.rollback()
        logger.error(f"保存HTML失败: {e}", exc_info=True)
        raise e
    finally:
        db.close()

