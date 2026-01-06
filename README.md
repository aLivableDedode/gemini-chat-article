# 文章生成系统

一个完整的文章生成系统，支持从主题生成标题、从标题生成短文、从短文生成HTML的完整工作流程。

## 功能特性

- ✅ **标题生成**：根据主题自动生成多个爆款公众号标题
- ✅ **短文生成**：基于选中的标题生成情感类短文
- ✅ **HTML生成**：将短文转换为极简风格的HTML排版
- ✅ **数据库存储**：所有生成内容（包括提示词）都保存到SQLite数据库
- ✅ **双界面支持**：同时提供CLI命令行界面和Web界面
- ✅ **完整追溯**：每个生成步骤都保存了完整的提示词，便于调试和优化

## 项目结构

```
gemini-chat-article/
├── app.py                    # Web应用入口（Flask）
├── cli.py                    # CLI应用入口
├── config.py                 # 配置文件
├── database.py               # 数据库初始化和会话管理
├── models.py                 # 数据模型（Topic, Title, Article, HTML）
├── services/                 # 服务模块
│   ├── title_service.py      # 标题生成服务
│   ├── article_service.py    # 短文生成服务
│   └── html_service.py       # HTML生成服务
├── utils/                    # 工具模块
│   ├── api.py                # API调用工具
│   └── text_parser.py        # 文本解析工具
├── templates/                # Flask模板
│   └── index.html
├── static/                   # 静态文件
├── data/                     # 数据目录
│   └── articles.db           # SQLite数据库
└── requirements.txt          # 依赖包
```

## 安装

1. **克隆或下载项目**

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **设置环境变量**

创建 `.env` 文件（可以复制 `.env.example` 并修改）：
```bash
cp .env.example .env
```

然后编辑 `.env` 文件，填入你的API密钥：
```bash
# Gemini API密钥
GEMINI_API_KEY=your_gemini_api_key_here

# Coze API密钥（如果使用Coze API功能）
COZE_API_TOKEN=Bearer your_coze_bearer_token_here
```

或者在命令行中设置：
```bash
export GEMINI_API_KEY="your_api_key_here"
export COZE_API_TOKEN="Bearer your_coze_bearer_token_here"
```

**注意**：`.env` 文件已添加到 `.gitignore`，不会被提交到Git仓库。请确保不要将包含真实密钥的 `.env` 文件提交到版本控制系统。

## 使用方法

### CLI界面

运行命令行界面：
```bash
python cli.py
```

交互式菜单：
1. 创建新主题并生成标题
2. 查看所有主题
3. 选择主题查看标题
4. 选择标题生成短文
5. 查看短文
6. 选择短文生成HTML
7. 查看HTML输出
8. 导入提示词模板到数据库
9. 退出

### Web界面

启动Web服务器：
```bash
python app.py
```

然后在浏览器中访问：`http://localhost:5000`

Web界面提供完整的可视化操作流程。

## 数据库设计

系统使用SQLite数据库，包含以下表：

- **topics** - 主题表
- **titles** - 标题表（包含 prompt_text 和 prompt_template_id 字段）
- **articles** - 短文表（包含 prompt_text 和 prompt_template_id 字段）
- **html_outputs** - HTML输出表（包含 prompt_text 和 prompt_template_id 字段）
- **prompt_templates** - 提示词模板表（新增）

所有生成内容都会自动保存到数据库，包括：
- 生成的内容本身
- 使用的完整提示词（替换占位符后的最终提示词）
- 创建时间
- 关联关系

## 工作流程

```
用户输入主题
  ↓
生成标题（调用Gemini API，记录完整提示词）→ 保存标题和提示词到数据库
  ↓
用户选择标题（可多选）
  ↓
为每个选中标题生成短文（调用Gemini API，记录完整提示词）→ 保存短文和提示词到数据库
  ↓
用户选择短文
  ↓
生成HTML（调用Gemini API，记录完整提示词）→ 保存HTML和提示词到数据库
  ↓
完成
```

## 提示词模板管理

### 提示词模板目录结构

系统支持从文件系统导入提示词模板到数据库。提示词模板文件应放在 `prompts/` 目录下，按分类组织：

```
prompts/
├── title/          # 标题生成模板
│   └── 默认.txt
├── article/        # 短文生成模板
│   └── 默认.txt
└── html/           # HTML生成模板
    └── 默认.txt
```

### 导入提示词模板到数据库

系统提供了三种方式导入提示词模板：

#### 方式1：自动导入（推荐）

启动 Web 应用时，系统会自动导入 `prompts/` 目录下的所有模板文件：

```bash
python app.py
```

#### 方式2：使用独立导入脚本

运行专门的导入脚本：

```bash
python import_prompts.py
```

#### 方式3：使用 CLI 界面

在 CLI 界面中选择选项 8：

```bash
python cli.py
# 然后选择 8. 导入提示词模板到数据库
```

### 提示词模板规则

- **文件格式**：`.txt` 文件
- **命名规则**：文件名（不含扩展名）将作为模板名称
- **占位符支持**：
  - 标题模板：使用 `{{topic}}` 作为主题占位符
  - 短文模板：使用 `[在此输入你的主题]` 或 `{{title}}` 作为标题占位符
  - HTML模板：使用 `{{content}}` 作为内容占位符
- **默认模板**：每个分类的第一个模板会自动设置为默认模板

### 旧版提示词文件（已废弃）

以下旧版提示词文件已不再使用，建议迁移到新的模板系统：

- `标题生成提示词` - 标题生成模板（已迁移到 `prompts/title/`）
- `qx-短文提示词` - 短文生成模板（已迁移到 `prompts/article/`）
- `html生成提示词` - HTML生成模板（已迁移到 `prompts/html/`）

这些文件使用占位符：
- `{{topic}}` - 主题占位符（标题生成）
- `[在此输入你的主题]` - 主题占位符（短文生成）
- `{{content}}` - 内容占位符（HTML生成）

## 配置说明

在 `config.py` 中可以修改：
- API配置（BASE_URL, MODEL_NAME）
- 提示词文件路径
- 数据库路径
- Flask服务器配置
- 生成参数（temperature, max_tokens）

## 注意事项

1. **API密钥**：确保设置了 `GEMINI_API_KEY` 环境变量
2. **提示词文件**：确保提示词文件存在于项目根目录
3. **数据库**：首次运行会自动创建数据库和表结构
4. **网络连接**：需要能够访问 Gemini API 服务器

## 保留的独立脚本

以下文件保留作为独立脚本使用：
- `gen_title.py` - 独立标题生成脚本
- `gen_article.py` - 独立短文生成脚本
- `gen_html.py` - 独立HTML生成脚本

## 许可证

MIT License

# gemini-chat-article
