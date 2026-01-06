"""
配置文件
"""
import os

# API配置
API_KEY = os.getenv("GEMINI_API_KEY")
BASE_URL = os.getenv("GEMINI_BASE_URL", "http://1003.2.gptuu.cc:1003")
MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-3-pro-preview")

# 提示词文件路径
TITLE_PROMPT_FILE = "标题生成提示词"
ARTICLE_PROMPT_FILE = "qx-短文提示词"
HTML_PROMPT_FILE = "html生成提示词"

# 数据库配置
DB_DIR = "data"
DB_PATH = os.path.join(DB_DIR, "articles.db")

# Flask配置
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5001  # 改为5001避免端口冲突
FLASK_DEBUG = True

# 生成参数
TITLE_TEMPERATURE = 0.8
TITLE_MAX_TOKENS = 2048
ARTICLE_TEMPERATURE = 0.7
ARTICLE_MAX_TOKENS = 8192
HTML_TEMPERATURE = 0.7
HTML_MAX_TOKENS = 4096

