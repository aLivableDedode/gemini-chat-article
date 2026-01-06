"""
标题生成服务
"""
from typing import List, Tuple, Optional
import os
from utils.api import get_gemini_response
from utils.text_parser import parse_titles
from database import get_db_session
from models import Title
from services.prompt_service import get_prompt_template_by_id, get_default_prompt_template
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
            PromptTemplate.category == "title",
            PromptTemplate.is_default == True
        ).first()
        
        if not template:
            # 如果没有默认模板，返回第一个
            template = db.query(PromptTemplate).filter(
                PromptTemplate.category == "title"
            ).first()
        
        if template:
            return template.content
    finally:
        db.close()
    
    # 向后兼容：如果数据库中没有，尝试从文件加载
    PROMPT_FILE_PATH = "标题生成提示词"
    if os.path.exists(PROMPT_FILE_PATH):
        with open(PROMPT_FILE_PATH, "r", encoding="utf-8") as f:
            return f.read()
    
    raise FileNotFoundError("找不到提示词模板")


def generate_titles(topic: str, template_id: Optional[int] = None) -> Tuple[List[str], str, Optional[int]]:
    """
    生成标题列表并自动解析
    
    :param topic: 文章主题
    :param template_id: 提示词模板ID（可选）
    :return: (标题列表, 完整提示词, 模板ID)
    """
    logger.info(f"开始生成标题: topic='{topic}', template_id={template_id}")
    
    # 1. 读取模板
    template_content = load_prompt_template(template_id)
    logger.debug(f"提示词模板加载成功，长度: {len(template_content)} 字符")
    
    # 2. 获取模板ID
    from database import get_db_session
    from models import PromptTemplate
    
    db = get_db_session()
    try:
        if template_id:
            used_template_id = template_id
            logger.info(f"使用指定模板: template_id={template_id}")
        else:
            # 获取默认模板ID
            default_template = db.query(PromptTemplate).filter(
                PromptTemplate.category == "title",
                PromptTemplate.is_default == True
            ).first()
            if not default_template:
                default_template = db.query(PromptTemplate).filter(
                    PromptTemplate.category == "title"
                ).first()
            used_template_id = default_template.id if default_template else None
            logger.info(f"使用默认模板: template_id={used_template_id}")
    finally:
        db.close()
    
    # 3. 替换占位符
    final_prompt = template_content.replace("{{topic}}", topic)
    logger.debug(f"提示词准备完成，最终长度: {len(final_prompt)} 字符")
    
    # 4. 调用 API 生成标题
    logger.info("正在调用API生成标题...")
    raw_output = get_gemini_response(final_prompt, temperature=0.8, max_tokens=2048)
    logger.info(f"API返回原始内容长度: {len(raw_output)} 字符")
    
    # 5. 解析标题列表
    logger.info("正在解析标题列表...")
    titles = parse_titles(raw_output)
    logger.info(f"标题解析完成，共 {len(titles)} 个标题: {titles}")
    
    return titles, final_prompt, used_template_id


def save_titles_to_db(topic_id: int, titles: List[str], prompt_text: str, template_id: Optional[int] = None) -> List[int]:
    """
    保存标题和提示词到数据库
    
    :param topic_id: 主题ID
    :param titles: 标题列表
    :param prompt_text: 完整提示词
    :return: 保存的标题ID列表
    """
    logger.info(f"开始保存标题到数据库: topic_id={topic_id}, titles_count={len(titles)}")
    db = get_db_session()
    try:
        title_ids = []
        for idx, title_text in enumerate(titles, 1):
            logger.debug(f"保存标题 {idx}/{len(titles)}: '{title_text[:30]}...'")
            title = Title(
                topic_id=topic_id,
                title_text=title_text,
                prompt_text=prompt_text,
                prompt_template_id=template_id,
                selected=False
            )
            db.add(title)
            db.flush()  # 获取ID
            title_ids.append(title.id)
        
        db.commit()
        logger.info(f"标题保存成功，共 {len(title_ids)} 个，ID列表: {title_ids}")
        return title_ids
    except Exception as e:
        db.rollback()
        logger.error(f"保存标题失败: {e}", exc_info=True)
        raise e
    finally:
        db.close()

