"""
CLI交互式界面
"""
import sys
from database import init_db, get_db_session
from models import Topic, Title, Article, HTMLOutput
from services.title_service import generate_titles, save_titles_to_db
from services.article_service import generate_article, save_article_to_db
from services.html_service import generate_html, save_html_to_db


def print_separator():
    """打印分隔线"""
    print("=" * 60)


def print_menu():
    """打印主菜单"""
    print_separator()
    print("文章生成系统 - CLI界面")
    print_separator()
    print("1. 创建新主题并生成标题")
    print("2. 查看所有主题")
    print("3. 选择主题查看标题")
    print("4. 选择标题生成短文")
    print("5. 查看短文")
    print("6. 选择短文生成HTML")
    print("7. 查看HTML输出")
    print("8. 退出")
    print_separator()


def create_topic_and_generate_titles():
    """创建新主题并生成标题"""
    print_separator()
    topic_text = input("请输入文章主题: ").strip()
    
    if not topic_text:
        print("❌ 主题不能为空！")
        return
    
    print(f"\n正在为主题【{topic_text}】生成标题...")
    
    try:
        # 1. 创建主题
        db = get_db_session()
        topic = Topic(topic_text=topic_text, status="draft")
        db.add(topic)
        db.commit()
        topic_id = topic.id
        db.close()
        
        # 2. 生成标题
        titles, prompt_text = generate_titles(topic_text)
        
        if not titles:
            print("❌ 未能生成标题，请重试")
            return
        
        # 3. 保存标题到数据库
        title_ids = save_titles_to_db(topic_id, titles, prompt_text)
        
        # 4. 显示结果
        print(f"\n✅ 成功生成 {len(titles)} 个标题：")
        for i, title in enumerate(titles, 1):
            print(f"  {i}. {title}")
        
        print(f"\n✅ 主题和标题已保存到数据库（主题ID: {topic_id}）")
        
    except Exception as e:
        print(f"❌ 执行出错: {e}")


def list_topics():
    """查看所有主题"""
    print_separator()
    db = get_db_session()
    try:
        topics = db.query(Topic).order_by(Topic.created_at.desc()).all()
        
        if not topics:
            print("暂无主题")
            return
        
        print(f"共有 {len(topics)} 个主题：\n")
        for topic in topics:
            titles_count = len(topic.titles)
            print(f"  [{topic.id}] {topic.topic_text} (状态: {topic.status}, 标题数: {titles_count}, 创建时间: {topic.created_at.strftime('%Y-%m-%d %H:%M:%S')})")
        
    except Exception as e:
        print(f"❌ 执行出错: {e}")
    finally:
        db.close()


def view_titles_by_topic():
    """选择主题查看标题"""
    print_separator()
    topic_id = input("请输入主题ID: ").strip()
    
    if not topic_id.isdigit():
        print("❌ 无效的主题ID")
        return
    
    db = get_db_session()
    try:
        topic = db.query(Topic).filter(Topic.id == int(topic_id)).first()
        
        if not topic:
            print("❌ 未找到该主题")
            return
        
        print(f"\n主题: {topic.topic_text}")
        print(f"标题列表（共 {len(topic.titles)} 个）：\n")
        
        for i, title in enumerate(topic.titles, 1):
            selected_mark = "✓" if title.selected else " "
            print(f"  [{selected_mark}] {i}. {title.title_text} (ID: {title.id})")
        
    except Exception as e:
        print(f"❌ 执行出错: {e}")
    finally:
        db.close()


def generate_articles_from_titles():
    """选择标题生成短文"""
    print_separator()
    title_ids_input = input("请输入标题ID（多个用逗号分隔）: ").strip()
    
    if not title_ids_input:
        print("❌ 标题ID不能为空")
        return
    
    title_ids = [tid.strip() for tid in title_ids_input.split(",")]
    
    db = get_db_session()
    try:
        for title_id_str in title_ids:
            if not title_id_str.isdigit():
                print(f"❌ 跳过无效的标题ID: {title_id_str}")
                continue
            
            title_id = int(title_id_str)
            title = db.query(Title).filter(Title.id == title_id).first()
            
            if not title:
                print(f"❌ 未找到标题ID: {title_id}")
                continue
            
            print(f"\n正在为标题【{title.title_text}】生成短文...")
            
            try:
                # 生成短文
                article_text, prompt_text = generate_article(title.title_text)
                
                # 保存到数据库
                article_id = save_article_to_db(title_id, article_text, prompt_text)
                
                print(f"✅ 短文已生成并保存（短文ID: {article_id}）")
                print(f"预览（前100字符）: {article_text[:100]}...")
                
            except Exception as e:
                print(f"❌ 生成短文失败: {e}")
        
    except Exception as e:
        print(f"❌ 执行出错: {e}")
    finally:
        db.close()


def view_articles():
    """查看短文"""
    print_separator()
    db = get_db_session()
    try:
        articles = db.query(Article).order_by(Article.created_at.desc()).all()
        
        if not articles:
            print("暂无短文")
            return
        
        print(f"共有 {len(articles)} 篇短文：\n")
        for article in articles:
            selected_mark = "✓" if article.selected else " "
            print(f"  [{selected_mark}] ID: {article.id} | 标题: {article.title.title_text}")
            print(f"      预览: {article.article_text[:80]}...")
            print(f"      创建时间: {article.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
    except Exception as e:
        print(f"❌ 执行出错: {e}")
    finally:
        db.close()


def generate_html_from_articles():
    """选择短文生成HTML"""
    print_separator()
    article_id_input = input("请输入短文ID: ").strip()
    
    if not article_id_input.isdigit():
        print("❌ 无效的短文ID")
        return
    
    article_id = int(article_id_input)
    db = get_db_session()
    try:
        article = db.query(Article).filter(Article.id == article_id).first()
        
        if not article:
            print("❌ 未找到该短文")
            return
        
        print(f"\n正在为短文生成HTML...")
        print(f"短文预览: {article.article_text[:100]}...")
        
        try:
            # 生成HTML
            html_content, prompt_text = generate_html(article.article_text)
            
            # 保存到数据库
            html_id = save_html_to_db(article_id, html_content, prompt_text)
            
            print(f"✅ HTML已生成并保存（HTML ID: {html_id}）")
            print(f"HTML预览（前200字符）: {html_content[:200]}...")
            
        except Exception as e:
            print(f"❌ 生成HTML失败: {e}")
        
    except Exception as e:
        print(f"❌ 执行出错: {e}")
    finally:
        db.close()


def view_html_outputs():
    """查看HTML输出"""
    print_separator()
    db = get_db_session()
    try:
        html_outputs = db.query(HTMLOutput).order_by(HTMLOutput.created_at.desc()).all()
        
        if not html_outputs:
            print("暂无HTML输出")
            return
        
        print(f"共有 {len(html_outputs)} 个HTML输出：\n")
        for html_output in html_outputs:
            print(f"  ID: {html_output.id} | 短文ID: {html_output.article_id}")
            print(f"      短文标题: {html_output.article.title.title_text}")
            print(f"      HTML预览: {html_output.html_content[:100]}...")
            print(f"      创建时间: {html_output.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
        
    except Exception as e:
        print(f"❌ 执行出错: {e}")
    finally:
        db.close()


def main():
    """主函数"""
    # 初始化数据库
    init_db()
    
    while True:
        print_menu()
        choice = input("请选择操作 (1-8): ").strip()
        
        if choice == "1":
            create_topic_and_generate_titles()
        elif choice == "2":
            list_topics()
        elif choice == "3":
            view_titles_by_topic()
        elif choice == "4":
            generate_articles_from_titles()
        elif choice == "5":
            view_articles()
        elif choice == "6":
            generate_html_from_articles()
        elif choice == "7":
            view_html_outputs()
        elif choice == "8":
            print("再见！")
            sys.exit(0)
        else:
            print("❌ 无效的选择，请重新输入")
        
        input("\n按回车键继续...")


if __name__ == "__main__":
    main()

