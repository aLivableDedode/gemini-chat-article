#!/usr/bin/env python3
"""
手动导入提示词模板到数据库
用法: python import_prompts.py
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db
from services.prompt_service import init_prompt_templates
from utils.logger import logger


def main():
    """主函数"""
    print("=" * 60)
    print("提示词模板导入工具")
    print("=" * 60)
    
    try:
        # 1. 初始化数据库（确保表存在）
        print("\n[1/2] 正在初始化数据库...")
        init_db()
        print("✅ 数据库初始化完成")
        
        # 2. 导入提示词模板
        print("\n[2/2] 正在导入提示词模板...")
        init_prompt_templates()
        print("✅ 提示词模板导入完成")
        
        print("\n" + "=" * 60)
        print("✅ 所有操作完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 导入失败: {e}")
        logger.error(f"导入提示词模板失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

