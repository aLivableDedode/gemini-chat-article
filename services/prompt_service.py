"""
提示词模板管理服务
"""
import os
from typing import List, Optional, Dict
from database import get_db_session
from models import PromptTemplate
from utils.logger import logger


PROMPTS_DIR = "prompts"
CATEGORIES = {
    "title": "标题生成",
    "article": "短文生成",
    "html": "HTML生成"
}


def load_prompt_from_file(category: str, name: str) -> Optional[str]:
    """从文件加载提示词模板"""
    file_path = os.path.join(PROMPTS_DIR, category, f"{name}.txt")
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None
    return None


def init_prompt_templates():
    """初始化提示词模板到数据库"""
    logger.info("开始初始化提示词模板")
    db = get_db_session()
    try:
        total_loaded = 0
        for category in CATEGORIES.keys():
            category_dir = os.path.join(PROMPTS_DIR, category)
            if not os.path.exists(category_dir):
                logger.warning(f"提示词目录不存在: {category_dir}")
                continue
            
            logger.info(f"处理分类: {category} ({CATEGORIES[category]})")
            # 读取该分类下的所有txt文件
            for filename in os.listdir(category_dir):
                if filename.endswith('.txt'):
                    name = filename[:-4]  # 去除.txt后缀
                    file_path = os.path.join(category_dir, filename)
                    
                    # 检查是否已存在
                    existing = db.query(PromptTemplate).filter(
                        PromptTemplate.category == category,
                        PromptTemplate.name == name
                    ).first()
                    
                    if existing:
                        logger.debug(f"模板已存在，跳过: {category}/{name}")
                        continue  # 已存在，跳过
                    
                    # 读取文件内容
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        
                        # 创建模板（第一个作为默认模板）
                        is_default = not db.query(PromptTemplate).filter(
                            PromptTemplate.category == category,
                            PromptTemplate.is_default == True
                        ).first()
                        
                        template = PromptTemplate(
                            category=category,
                            name=name,
                            description=f"{CATEGORIES[category]}模板 - {name}",
                            content=content,
                            is_default=is_default,
                            file_path=file_path
                        )
                        db.add(template)
                        total_loaded += 1
                        logger.info(f"加载提示词模板: {category}/{name} (默认: {is_default})")
                    except Exception as e:
                        logger.error(f"加载提示词文件失败 {file_path}: {e}", exc_info=True)
                        continue
        
        db.commit()
        logger.info(f"提示词模板初始化完成，共加载 {total_loaded} 个模板")
    except Exception as e:
        db.rollback()
        logger.error(f"初始化提示词模板失败: {e}", exc_info=True)
        raise e
    finally:
        db.close()


def get_prompt_templates(category: str) -> List[Dict]:
    """获取指定分类的提示词模板列表"""
    db = get_db_session()
    try:
        templates = db.query(PromptTemplate).filter(
            PromptTemplate.category == category
        ).order_by(PromptTemplate.is_default.desc(), PromptTemplate.created_at.asc()).all()
        
        return [{
            'id': t.id,
            'name': t.name,
            'description': t.description,
            'is_default': t.is_default,
            'content': t.content[:200] + '...' if len(t.content) > 200 else t.content  # 预览
        } for t in templates]
    finally:
        db.close()


def get_prompt_template_by_id(template_id: int) -> Optional[Dict]:
    """根据ID获取提示词模板（返回字典，避免数据库会话问题）"""
    db = get_db_session()
    try:
        template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
        if template:
            return {
                'id': template.id,
                'category': template.category,
                'name': template.name,
                'description': template.description,
                'content': template.content,
                'is_default': template.is_default
            }
        return None
    finally:
        db.close()


def get_default_prompt_template(category: str) -> Optional[Dict]:
    """获取指定分类的默认提示词模板（返回字典）"""
    db = get_db_session()
    try:
        template = db.query(PromptTemplate).filter(
            PromptTemplate.category == category,
            PromptTemplate.is_default == True
        ).first()
        
        # 如果没有默认模板，返回第一个
        if not template:
            template = db.query(PromptTemplate).filter(
                PromptTemplate.category == category
            ).first()
        
        if template:
            return {
                'id': template.id,
                'category': template.category,
                'name': template.name,
                'description': template.description,
                'content': template.content,
                'is_default': template.is_default
            }
        return None
    finally:
        db.close()

