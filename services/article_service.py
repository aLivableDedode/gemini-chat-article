"""
短文生成服务
"""
from typing import Tuple, Optional
import os
from utils.api import get_gemini_response
from database import get_db_session
from models import Article
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
            PromptTemplate.category == "article",
            PromptTemplate.is_default == True
        ).first()
        
        if not template:
            # 如果没有默认模板，返回第一个
            template = db.query(PromptTemplate).filter(
                PromptTemplate.category == "article"
            ).first()
        
        if template:
            return template.content
    finally:
        db.close()
    
    # 向后兼容：如果数据库中没有，尝试从文件加载
    PROMPT_FILE_PATH = "qx-短文提示词"
    if os.path.exists(PROMPT_FILE_PATH):
        with open(PROMPT_FILE_PATH, "r", encoding="utf-8") as f:
            return f.read()
    
    raise FileNotFoundError("找不到提示词模板")


def generate_article(title: str, template_id: Optional[int] = None) -> Tuple[str, str, Optional[int]]:
    """
    生成短文
    
    :param title: 文章标题（主题）
    :param template_id: 提示词模板ID（可选）
    :return: (短文内容, 完整提示词, 模板ID)
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
                PromptTemplate.category == "article",
                PromptTemplate.is_default == True
            ).first()
            if not default_template:
                default_template = db.query(PromptTemplate).filter(
                    PromptTemplate.category == "article"
                ).first()
            used_template_id = default_template.id if default_template else None
    finally:
        db.close()
    
    # 3. 替换主题占位符
    prompt = template_content.replace("[在此输入你的主题]", title)
    
    # 4. 添加明确指令：只返回最终的中文短文，不要包含思考过程
    prompt += "\n\n**重要提示**：请直接输出最终的中文短文，不要包含任何思考过程、英文内容或中间步骤。只返回按照上述框架创作的中文短文正文。"
    
    # 5. 调用API生成短文
    article_text = get_gemini_response(prompt, temperature=0.7, max_tokens=8192)
    
    return article_text, prompt, used_template_id


def save_article_to_db(title_id: int, article_text: str, prompt_text: str, template_id: Optional[int] = None) -> int:
    """
    保存短文和提示词到数据库
    
    :param title_id: 标题ID
    :param article_text: 短文内容
    :param prompt_text: 完整提示词
    :return: 保存的短文ID
    """
    logger.info(f"开始保存短文到数据库: title_id={title_id}, article_length={len(article_text)}")
    db = get_db_session()
    try:
        article = Article(
            title_id=title_id,
            article_text=article_text,
            prompt_text=prompt_text,
            prompt_template_id=template_id,
            selected=False
        )
        db.add(article)
        db.commit()
        logger.info(f"短文保存成功，ID: {article.id}")
        return article.id
    except Exception as e:
        db.rollback()
        logger.error(f"保存短文失败: {e}", exc_info=True)
        raise e
    finally:
        db.close()

