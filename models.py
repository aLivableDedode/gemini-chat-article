"""
数据模型定义
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class Topic(Base):
    """主题表"""
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    topic_text = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    status = Column(String(20), default="draft")  # draft/completed

    # 关系
    titles = relationship("Title", back_populates="topic", cascade="all, delete-orphan")


class Title(Base):
    """标题表"""
    __tablename__ = "titles"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    title_text = Column(String(200), nullable=False)
    prompt_text = Column(Text, nullable=False)  # 生成标题时使用的完整提示词
    prompt_template_id = Column(Integer, ForeignKey("prompt_templates.id"), nullable=True)  # 使用的提示词模板ID
    created_at = Column(DateTime, default=datetime.now)
    selected = Column(Boolean, default=False)

    # 关系
    topic = relationship("Topic", back_populates="titles")
    articles = relationship("Article", back_populates="title", cascade="all, delete-orphan")
    prompt_template = relationship("PromptTemplate", foreign_keys=[prompt_template_id])


class Article(Base):
    """短文表"""
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title_id = Column(Integer, ForeignKey("titles.id"), nullable=False)
    article_text = Column(Text, nullable=False)
    prompt_text = Column(Text, nullable=False)  # 生成短文时使用的完整提示词
    prompt_template_id = Column(Integer, ForeignKey("prompt_templates.id"), nullable=True)  # 使用的提示词模板ID
    created_at = Column(DateTime, default=datetime.now)
    selected = Column(Boolean, default=False)

    # 关系
    title = relationship("Title", back_populates="articles")
    html_outputs = relationship("HTMLOutput", back_populates="article", cascade="all, delete-orphan")
    prompt_template = relationship("PromptTemplate", foreign_keys=[prompt_template_id])


class HTMLOutput(Base):
    """HTML输出表"""
    __tablename__ = "html_outputs"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    html_content = Column(Text, nullable=False)
    prompt_text = Column(Text, nullable=False)  # 生成HTML时使用的完整提示词
    prompt_template_id = Column(Integer, ForeignKey("prompt_templates.id"), nullable=True)  # 使用的提示词模板ID
    created_at = Column(DateTime, default=datetime.now)

    # 关系
    article = relationship("Article", back_populates="html_outputs")
    prompt_template = relationship("PromptTemplate", foreign_keys=[prompt_template_id])


class PromptTemplate(Base):
    """提示词模板表"""
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), nullable=False, index=True)  # title/article/html
    name = Column(String(200), nullable=False)  # 模板名称
    description = Column(Text, nullable=True)  # 模板描述
    content = Column(Text, nullable=False)  # 模板内容
    is_default = Column(Boolean, default=False)  # 是否为默认模板
    file_path = Column(String(500), nullable=True)  # 文件路径（如果从文件加载）
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

