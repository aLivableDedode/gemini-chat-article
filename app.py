"""
Flask Web应用
"""
from flask import Flask, render_template, request, jsonify, redirect
from database import init_db, get_db_session
from models import Topic, Title, Article, HTMLOutput, PromptTemplate
from services.title_service import generate_titles, save_titles_to_db
from services.article_service import generate_article, save_article_to_db
from services.html_service import generate_html, save_html_to_db
from services.prompt_service import init_prompt_templates, get_prompt_templates, delete_prompt_template
from services.coze_service import call_coze_api
from utils.logger import logger

app = Flask(__name__)

# 初始化数据库
logger.info("正在初始化数据库...")
init_db()
logger.info("数据库初始化完成")

# 初始化提示词模板
try:
    logger.info("正在初始化提示词模板...")
    init_prompt_templates()
    logger.info("提示词模板初始化完成")
except Exception as e:
    logger.error(f"提示词模板初始化失败: {e}", exc_info=True)


@app.route('/')
def index():
    """主页 - 重定向到步骤1"""
    return redirect('/step1')


@app.route('/step1')
def step1():
    """步骤1: 创建主题并生成标题"""
    return render_template('step1.html')


@app.route('/step2')
def step2():
    """步骤2: 选择标题生成短文"""
    return render_template('step2.html')


@app.route('/step3')
def step3():
    """步骤3: 选择短文生成HTML"""
    return render_template('step3.html')


@app.route('/step4')
def step4():
    """步骤4: 查看HTML输出"""
    return render_template('step4.html')


@app.route('/step5')
def step5():
    """步骤5: 选择标题生成HTML并调用Coze API"""
    return render_template('step5.html')


@app.route('/prompts')
def prompts():
    """提示词管理"""
    return render_template('prompts.html')


@app.route('/api/topics', methods=['GET'])
def get_topics():
    """获取所有主题"""
    logger.info("收到获取主题列表请求")
    db = get_db_session()
    try:
        topics = db.query(Topic).order_by(Topic.created_at.desc()).all()
        logger.info(f"查询到 {len(topics)} 个主题")
        result = []
        for t in topics:
            # 使用查询计数，避免关系加载问题
            titles_count = db.query(Title).filter(Title.topic_id == t.id).count()
            # 只返回有标题的主题（titles_count > 0）
            if titles_count > 0:
                result.append({
                    'id': t.id,
                    'topic_text': t.topic_text,
                    'status': t.status,
                    'created_at': t.created_at.isoformat(),
                    'titles_count': titles_count
                })
        logger.info(f"过滤后返回 {len(result)} 个有标题的主题（已过滤 {len(topics) - len(result)} 个无标题主题）")
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        logger.error(f"获取主题列表失败: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/prompts', methods=['POST'])
def create_prompt():
    """创建新的提示词模板"""
    data = request.json
    category = data.get('category', '').strip()
    name = data.get('name', '').strip()
    description = data.get('description', '').strip() or None
    content = data.get('content', '').strip()
    is_default = data.get('is_default', False)
    
    logger.info(f"收到创建提示词请求: category='{category}', name='{name}'")
    
    if category not in ['title', 'article', 'html']:
        logger.warning(f"无效的分类: {category}")
        return jsonify({'success': False, 'error': '无效的分类，必须是 title/article/html 之一'}), 400
    
    if not name:
        logger.warning("模板名称为空")
        return jsonify({'success': False, 'error': '模板名称不能为空'}), 400
    
    if not content:
        logger.warning("模板内容为空")
        return jsonify({'success': False, 'error': '模板内容不能为空'}), 400
    
    db = get_db_session()
    try:
        # 如果设置为默认模板，需要先取消同分类下其他模板的默认状态
        if is_default:
            logger.info(f"设置为默认模板，取消同分类下其他模板的默认状态")
            existing_defaults = db.query(PromptTemplate).filter(
                PromptTemplate.category == category,
                PromptTemplate.is_default == True
            ).all()
            for template in existing_defaults:
                template.is_default = False
        
        # 创建新模板
        logger.info(f"正在创建提示词模板: {name}")
        template = PromptTemplate(
            category=category,
            name=name,
            description=description,
            content=content,
            is_default=is_default
        )
        db.add(template)
        db.commit()
        template_id = template.id
        logger.info(f"提示词模板创建成功，ID: {template_id}")
        
        return jsonify({
            'success': True,
            'data': {
                'id': template_id,
                'category': category,
                'name': name,
                'description': description,
                'is_default': is_default
            }
        })
    except Exception as e:
        db.rollback()
        logger.error(f"创建提示词模板失败: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/prompts/<category>', methods=['GET'])
def get_prompts(category):
    """获取指定分类的提示词模板列表"""
    if category not in ['title', 'article', 'html']:
        return jsonify({'success': False, 'error': '无效的分类'}), 400
    
    try:
        templates = get_prompt_templates(category)
        return jsonify({
            'success': True,
            'data': templates
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/prompts/<int:template_id>', methods=['GET'])
def get_prompt_detail(template_id):
    """获取提示词模板详情"""
    db = get_db_session()
    try:
        template = db.query(PromptTemplate).filter(PromptTemplate.id == template_id).first()
        if not template:
            return jsonify({'success': False, 'error': '模板不存在'}), 404
        
        return jsonify({
            'success': True,
            'data': {
                'id': template.id,
                'category': template.category,
                'name': template.name,
                'description': template.description,
                'content': template.content,
                'is_default': template.is_default
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/prompts/<int:template_id>', methods=['DELETE'])
def delete_prompt(template_id):
    """删除提示词模板"""
    logger.info(f"收到删除提示词模板请求: template_id={template_id}")
    
    try:
        # 删除模板（函数内部会检查模板是否存在）
        success = delete_prompt_template(template_id)
        if success:
            logger.info(f"提示词模板删除成功: template_id={template_id}")
            return jsonify({
                'success': True,
                'data': {'id': template_id}
            })
        else:
            # 模板不存在
            return jsonify({'success': False, 'error': '模板不存在'}), 404
    except Exception as e:
        logger.error(f"删除提示词模板失败: template_id={template_id}, error={e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/topics', methods=['POST'])
def create_topic():
    """创建主题并生成标题"""
    data = request.json
    topic_text = data.get('topic_text', '').strip()
    template_id = data.get('template_id', None)  # 可选的提示词模板ID
    
    logger.info(f"收到创建主题请求: topic='{topic_text}', template_id={template_id}")
    
    if not topic_text:
        logger.warning("主题为空，拒绝请求")
        return jsonify({'success': False, 'error': '主题不能为空'}), 400
    
    try:
        # 1. 创建主题
        logger.info(f"正在创建主题: {topic_text}")
        db = get_db_session()
        topic = Topic(topic_text=topic_text, status="draft")
        db.add(topic)
        db.commit()
        topic_id = topic.id
        db.close()
        logger.info(f"主题创建成功，ID: {topic_id}")
        
        # 2. 生成标题（使用指定的模板）
        logger.info(f"开始生成标题，使用模板ID: {template_id}")
        titles, prompt_text, used_template_id = generate_titles(topic_text, template_id)
        logger.info(f"标题生成完成，共生成 {len(titles)} 个标题")
        
        if not titles:
            logger.warning("未能生成任何标题")
            return jsonify({'success': False, 'error': '未能生成标题'}), 500
        
        # 3. 保存标题到数据库
        logger.info(f"正在保存 {len(titles)} 个标题到数据库")
        title_ids = save_titles_to_db(topic_id, titles, prompt_text, used_template_id)
        logger.info(f"标题保存成功，ID列表: {title_ids}")
        
        return jsonify({
            'success': True,
            'data': {
                'topic_id': topic_id,
                'topic_text': topic_text,
                'titles': titles,
                'title_ids': title_ids,
                'template_id': used_template_id
            }
        })
    except Exception as e:
        logger.error(f"创建主题失败: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/topics/custom', methods=['POST'])
def create_topic_with_custom_titles():
    """创建主题并保存自定义标题"""
    data = request.json
    topic_text = data.get('topic_text', '').strip()
    titles = data.get('titles', [])
    
    logger.info(f"收到创建主题并保存自定义标题请求: topic='{topic_text}', titles_count={len(titles)}")
    
    if not topic_text:
        logger.warning("主题为空，拒绝请求")
        return jsonify({'success': False, 'error': '主题不能为空'}), 400
    
    if not titles or len(titles) == 0:
        logger.warning("标题列表为空，拒绝请求")
        return jsonify({'success': False, 'error': '至少需要输入一个标题'}), 400
    
    try:
        # 1. 创建主题
        logger.info(f"正在创建主题: {topic_text}")
        db = get_db_session()
        topic = Topic(topic_text=topic_text, status="draft")
        db.add(topic)
        db.commit()
        topic_id = topic.id
        db.close()
        logger.info(f"主题创建成功，ID: {topic_id}")
        
        # 2. 保存自定义标题到数据库（不需要prompt_text，因为是手动输入的）
        logger.info(f"正在保存 {len(titles)} 个自定义标题")
        title_ids = []
        db = get_db_session()
        try:
            for idx, title_text in enumerate(titles, 1):
                logger.debug(f"保存标题 {idx}/{len(titles)}: '{title_text[:30]}...'")
                title = Title(
                    topic_id=topic_id,
                    title_text=title_text,
                    prompt_text="自定义标题（手动输入）",  # 标记为自定义标题
                    prompt_template_id=None,
                    selected=False
                )
                db.add(title)
                db.flush()
                title_ids.append(title.id)
            
            db.commit()
            logger.info(f"自定义标题保存成功，共 {len(title_ids)} 个，ID列表: {title_ids}")
        except Exception as e:
            db.rollback()
            logger.error(f"保存自定义标题失败: {e}", exc_info=True)
            raise
        finally:
            db.close()
        
        # 3. 返回结果
        return jsonify({
            'success': True,
            'data': {
                'topic_id': topic_id,
                'topic_text': topic_text,
                'titles': [{'id': tid, 'title_text': titles[idx]} for idx, tid in enumerate(title_ids)]
            }
        })
    except Exception as e:
        logger.error(f"创建主题并保存自定义标题失败: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/topics/<int:topic_id>/titles', methods=['GET'])
def get_titles(topic_id):
    """获取主题下的所有标题"""
    logger.info(f"收到获取标题请求: topic_id={topic_id}")
    db = get_db_session()
    try:
        topic = db.query(Topic).filter(Topic.id == topic_id).first()
        if not topic:
            logger.warning(f"主题不存在: topic_id={topic_id}")
            return jsonify({'success': False, 'error': '主题不存在'}), 404
        
        # 直接查询标题，避免关系加载问题
        titles = db.query(Title).filter(Title.topic_id == topic_id).order_by(Title.created_at.desc()).all()
        logger.info(f"查询到 {len(titles)} 个标题")
        
        return jsonify({
            'success': True,
            'data': {
                'topic': {
                    'id': topic.id,
                    'topic_text': topic.topic_text
                },
                'titles': [{
                    'id': t.id,
                    'title_text': t.title_text,
                    'prompt_text': t.prompt_text,
                    'selected': t.selected,
                    'created_at': t.created_at.isoformat()
                } for t in titles]
            }
        })
    except Exception as e:
        logger.error(f"获取标题失败: topic_id={topic_id}, error={e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/titles/<int:title_id>/prompt', methods=['GET'])
def get_title_prompt(title_id):
    """获取标题的提示词"""
    db = get_db_session()
    try:
        title = db.query(Title).filter(Title.id == title_id).first()
        if not title:
            return jsonify({'success': False, 'error': '标题不存在'}), 404
        
        return jsonify({
            'success': True,
            'data': {
                'id': title.id,
                'title_text': title.title_text,
                'prompt_text': title.prompt_text,
                'created_at': title.created_at.isoformat()
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/articles/<int:article_id>/prompt', methods=['GET'])
def get_article_prompt(article_id):
    """获取短文的提示词"""
    db = get_db_session()
    try:
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            return jsonify({'success': False, 'error': '短文不存在'}), 404
        
        return jsonify({
            'success': True,
            'data': {
                'id': article.id,
                'title_text': article.title.title_text,
                'article_text': article.article_text[:100] + '...',
                'prompt_text': article.prompt_text,
                'created_at': article.created_at.isoformat()
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/html/<int:html_id>/prompt', methods=['GET'])
def get_html_prompt(html_id):
    """获取HTML的提示词"""
    logger.info(f"收到获取HTML提示词请求: html_id={html_id}")
    db = get_db_session()
    try:
        html_output = db.query(HTMLOutput).filter(HTMLOutput.id == html_id).first()
        if not html_output:
            logger.warning(f"HTML不存在: html_id={html_id}")
            return jsonify({'success': False, 'error': 'HTML不存在'}), 404
        
        return jsonify({
            'success': True,
            'data': {
                'id': html_output.id,
                'article_title': html_output.article.title.title_text,
                'prompt_text': html_output.prompt_text,
                'created_at': html_output.created_at.isoformat()
            }
        })
    except Exception as e:
        logger.error(f"获取HTML提示词失败: html_id={html_id}, error={e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/articles/custom', methods=['POST'])
def create_custom_article():
    """创建自定义短文（包含标题和短文内容）"""
    data = request.json
    topic_text = data.get('topic_text', '').strip() or None
    title_text = data.get('title_text', '').strip()
    article_text = data.get('article_text', '').strip()
    
    logger.info(f"收到创建自定义短文请求: topic_text='{topic_text}', title_text='{title_text[:30]}...', article_length={len(article_text)}")
    
    if not title_text:
        logger.warning("标题为空")
        return jsonify({'success': False, 'error': '标题不能为空'}), 400
    
    if not article_text:
        logger.warning("短文内容为空")
        return jsonify({'success': False, 'error': '短文内容不能为空'}), 400
    
    db = get_db_session()
    try:
        # 1. 创建或获取主题
        if topic_text:
            # 使用指定的主题
            topic = db.query(Topic).filter(Topic.topic_text == topic_text).first()
            if not topic:
                logger.info(f"创建新主题: {topic_text}")
                topic = Topic(topic_text=topic_text, status="draft")
                db.add(topic)
                db.flush()
            topic_id = topic.id
        else:
            # 自动创建主题（使用标题作为主题）
            logger.info(f"自动创建主题，使用标题: {title_text[:30]}...")
            topic = Topic(topic_text=title_text[:100], status="draft")  # 使用标题前100字符作为主题
            db.add(topic)
            db.flush()
            topic_id = topic.id
        
        logger.info(f"主题ID: {topic_id}")
        
        # 2. 创建标题
        logger.info(f"创建标题: {title_text}")
        title = Title(
            topic_id=topic_id,
            title_text=title_text,
            prompt_text="自定义标题和短文（手动输入）",
            prompt_template_id=None,
            selected=False
        )
        db.add(title)
        db.flush()
        title_id = title.id
        logger.info(f"标题创建成功，ID: {title_id}")
        
        # 3. 创建短文
        logger.info(f"创建短文，长度: {len(article_text)} 字符")
        article = Article(
            title_id=title_id,
            article_text=article_text,
            prompt_text="自定义短文（手动输入）",
            prompt_template_id=None,
            selected=False
        )
        db.add(article)
        db.flush()
        article_id = article.id
        logger.info(f"短文创建成功，ID: {article_id}")
        
        db.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'topic_id': topic_id,
                'topic_text': topic.topic_text,
                'title_id': title_id,
                'title_text': title_text,
                'article_id': article_id
            }
        })
    except Exception as e:
        db.rollback()
        logger.error(f"创建自定义短文失败: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/titles/<int:title_id>/articles', methods=['POST'])
def create_article(title_id):
    """为标题生成短文"""
    data = request.json or {}
    template_id = data.get('template_id', None)  # 可选的提示词模板ID
    
    logger.info(f"收到生成短文请求: title_id={title_id}, template_id={template_id}")
    
    db = get_db_session()
    try:
        title = db.query(Title).filter(Title.id == title_id).first()
        if not title:
            logger.warning(f"标题不存在: title_id={title_id}")
            return jsonify({'success': False, 'error': '标题不存在'}), 404
        
        logger.info(f"开始为标题生成短文: '{title.title_text}'")
        # 生成短文（使用指定的模板）
        article_text, prompt_text, used_template_id = generate_article(title.title_text, template_id)
        logger.info(f"短文生成完成，长度: {len(article_text)} 字符")
        
        # 保存到数据库
        logger.info(f"正在保存短文到数据库")
        article_id = save_article_to_db(title_id, article_text, prompt_text, used_template_id)
        logger.info(f"短文保存成功，ID: {article_id}")
        
        return jsonify({
            'success': True,
            'data': {
                'article_id': article_id,
                'article_text': article_text,
                'template_id': used_template_id
            }
        })
    except Exception as e:
        logger.error(f"生成短文失败: title_id={title_id}, error={e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/articles', methods=['GET'])
def get_articles():
    """获取所有短文"""
    db = get_db_session()
    try:
        articles = db.query(Article).order_by(Article.created_at.desc()).all()
        return jsonify({
            'success': True,
            'data': [{
                'id': a.id,
                'title_id': a.title_id,
                'title_text': a.title.title_text,
                'article_text': a.article_text,
                'prompt_text': a.prompt_text,
                'selected': a.selected,
                'created_at': a.created_at.isoformat()
            } for a in articles]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/articles/<int:article_id>/html', methods=['POST'])
def create_html(article_id):
    """为短文生成HTML"""
    data = request.json or {}
    template_id = data.get('template_id', None)  # 可选的提示词模板ID
    
    db = get_db_session()
    try:
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            return jsonify({'success': False, 'error': '短文不存在'}), 404
        
        # 生成HTML（使用指定的模板）
        html_content, prompt_text, used_template_id = generate_html(article.article_text, template_id)
        
        # 保存到数据库
        html_id = save_html_to_db(article_id, html_content, prompt_text, used_template_id)
        
        return jsonify({
            'success': True,
            'data': {
                'html_id': html_id,
                'html_content': html_content,
                'template_id': used_template_id
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/html/<int:html_id>', methods=['GET'])
def get_html(html_id):
    """获取HTML输出"""
    db = get_db_session()
    try:
        html_output = db.query(HTMLOutput).filter(HTMLOutput.id == html_id).first()
        if not html_output:
            return jsonify({'success': False, 'error': 'HTML不存在'}), 404
        
        return jsonify({
            'success': True,
            'data': {
                'id': html_output.id,
                'article_id': html_output.article_id,
                'html_content': html_output.html_content,
                'created_at': html_output.created_at.isoformat()
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/html', methods=['GET'])
def list_html_outputs():
    """获取所有HTML输出列表（不包含HTML内容）"""
    db = get_db_session()
    try:
        html_outputs = db.query(HTMLOutput).order_by(HTMLOutput.created_at.desc()).all()
        logger.info(f"获取HTML输出列表，共 {len(html_outputs)} 条")
        return jsonify({
            'success': True,
            'data': [{
                'id': h.id,
                'article_id': h.article_id,
                'article_title': h.article.title.title_text,
                'created_at': h.created_at.isoformat()
            } for h in html_outputs]
        })
    except Exception as e:
        logger.error(f"获取HTML输出列表失败: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/html/<int:html_id>', methods=['GET'])
def get_html_output(html_id):
    """获取单个HTML输出的详细内容"""
    db = get_db_session()
    try:
        html_output = db.query(HTMLOutput).filter(HTMLOutput.id == html_id).first()
        if not html_output:
            logger.warning(f"HTML输出不存在: html_id={html_id}")
            return jsonify({'success': False, 'error': 'HTML输出不存在'}), 404
        
        logger.info(f"获取HTML输出详情: html_id={html_id}")
        return jsonify({
            'success': True,
            'data': {
                'id': html_output.id,
                'article_id': html_output.article_id,
                'article_title': html_output.article.title.title_text,
                'html_content': html_output.html_content,
                'prompt_text': html_output.prompt_text,
                'created_at': html_output.created_at.isoformat()
            }
        })
    except Exception as e:
        logger.error(f"获取HTML输出详情失败: html_id={html_id}, error={e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/titles/<int:title_id>/coze', methods=['POST'])
def call_coze_for_title(title_id):
    """为标题生成HTML并调用Coze API"""
    data = request.json or {}
    html_template_id = data.get('html_template_id', None)  # 可选的HTML提示词模板ID
    
    logger.info(f"收到调用Coze API请求: title_id={title_id}, html_template_id={html_template_id}")
    
    db = get_db_session()
    try:
        title = db.query(Title).filter(Title.id == title_id).first()
        if not title:
            logger.warning(f"标题不存在: title_id={title_id}")
            return jsonify({'success': False, 'error': '标题不存在'}), 404
        
        # 1. 检查是否已有短文，如果没有则生成
        article = db.query(Article).filter(Article.title_id == title_id).first()
        if not article:
            logger.info(f"标题没有对应的短文，开始生成短文")
            article_text, prompt_text, used_template_id = generate_article(title.title_text)
            article_id = save_article_to_db(title_id, article_text, prompt_text, used_template_id)
            article = db.query(Article).filter(Article.id == article_id).first()
        else:
            logger.info(f"使用已有短文: article_id={article.id}")
        
        # 2. 检查是否已有HTML，如果没有则生成
        html_output = db.query(HTMLOutput).filter(HTMLOutput.article_id == article.id).first()
        if not html_output:
            logger.info(f"短文没有对应的HTML，开始生成HTML")
            html_content, html_prompt_text, used_html_template_id = generate_html(article.article_text, html_template_id)
            html_id = save_html_to_db(article.id, html_content, html_prompt_text, used_html_template_id)
            html_output = db.query(HTMLOutput).filter(HTMLOutput.id == html_id).first()
        else:
            logger.info(f"使用已有HTML: html_id={html_output.id}")
        
        # 3. 调用Coze API
        logger.info(f"开始调用Coze API: title='{title.title_text}'")
        coze_result = call_coze_api(title.title_text, html_output.html_content)
        
        logger.info(f"Coze API调用成功: title_id={title_id}")
        return jsonify({
            'success': True,
            'data': {
                'title_id': title_id,
                'title_text': title.title_text,
                'html_id': html_output.id,
                'coze_result': coze_result
            }
        })
    except Exception as e:
        logger.error(f"调用Coze API失败: title_id={title_id}, error={e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


if __name__ == '__main__':
    from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG
    app.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT)

