"""
数据库初始化和会话管理
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
import os

# 数据库路径
DB_DIR = "data"
DB_PATH = os.path.join(DB_DIR, "articles.db")

# 确保 data 目录存在
os.makedirs(DB_DIR, exist_ok=True)

# 创建数据库引擎
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

# 创建会话工厂
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

# 创建基类
Base = declarative_base()


def init_db():
    """初始化数据库，创建所有表"""
    from models import Topic, Title, Article, HTMLOutput
    Base.metadata.create_all(bind=engine)


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    """获取数据库会话（用于非上下文管理器场景）"""
    return SessionLocal()

