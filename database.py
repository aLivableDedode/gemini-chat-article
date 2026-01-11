"""
数据库初始化和会话管理
"""
from sqlalchemy import create_engine, inspect, text
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


def migrate_configs_table():
    """迁移 configs 表，添加 name 列（如果不存在）"""
    try:
        inspector = inspect(engine)
        if 'configs' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('configs')]
            if 'name' not in columns:
                # 添加 name 列
                with engine.begin() as conn:
                    conn.execute(text("ALTER TABLE configs ADD COLUMN name VARCHAR(100)"))
                print("✅ configs 表已添加 name 列")
    except Exception as e:
        # 如果表不存在或其他错误，忽略（init_db 会创建表）
        print(f"⚠️ 迁移 configs 表时出错（可忽略，如果表不存在）: {e}")


def init_db():
    """初始化数据库，创建所有表"""
    from models import Topic, Title, Article, HTMLOutput, Config
    # 迁移 configs 表（如果已存在且缺少 name 列）
    migrate_configs_table()
    # 创建所有表（包括新表和已有表的更新）
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

