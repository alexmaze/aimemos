# AI Memos

基于 FastAPI 和 PocketFlow 构建的 AI 个人知识库服务。

## 技术栈

- **Python 3.12+**: 现代 Python 特性
- **uv**: 快速的 Python 包管理器
- **FastAPI**: 高性能 Web 框架
- **PocketFlow**: AI 工作流框架
- **Pydantic**: 数据验证和设置管理

## 功能特性

- 创建、读取、更新和删除备忘录
- 按标题、内容或标签搜索备忘录
- 带自动文档的 RESTful API
- 内存存储（可轻松扩展为持久化存储）
- 健康检查端点

## 安装

### 前置要求

- Python 3.12 或更高版本
- uv 包管理器

### 设置步骤

1. 克隆仓库：
```bash
git clone https://github.com/alexmaze/aimemos.git
cd aimemos
```

2. 使用 uv 安装依赖：
```bash
uv sync
```

3. （可选）复制并配置环境文件：
```bash
cp .env.example .env
# 根据您的需要编辑 .env
```

## 使用方法

### 运行服务器

使用 uv 启动服务器：

```bash
uv run aimemos
```

或者直接使用 Python 运行：

```bash
uv run python -m aimemos.main
```

服务器默认将在 `http://0.0.0.0:8000` 上启动。

### API 文档

服务器运行后，您可以访问：

- **交互式 API 文档 (Swagger UI)**: http://localhost:8000/docs
- **备用 API 文档 (ReDoc)**: http://localhost:8000/redoc
- **OpenAPI 模式**: http://localhost:8000/openapi.json

### API 端点

#### 根路径和健康检查

- `GET /` - 根端点，返回服务信息
- `GET /health` - 健康检查端点

#### 备忘录

- `POST /api/v1/memos` - 创建新备忘录
- `GET /api/v1/memos` - 列出所有备忘录（支持分页）
- `GET /api/v1/memos/search?q=query` - 搜索备忘录
- `GET /api/v1/memos/{id}` - 获取指定备忘录
- `PUT /api/v1/memos/{id}` - 更新备忘录
- `DELETE /api/v1/memos/{id}` - 删除备忘录

### 使用示例

创建备忘录：
```bash
curl -X POST "http://localhost:8000/api/v1/memos" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "我的第一条备忘录",
    "content": "这是备忘录的内容",
    "tags": ["个人", "测试"]
  }'
```

列出备忘录：
```bash
curl "http://localhost:8000/api/v1/memos"
```

搜索备忘录：
```bash
curl "http://localhost:8000/api/v1/memos/search?q=第一条"
```

### 演示脚本

提供了一个演示脚本来展示 API 功能：

```bash
# 安装演示依赖
uv sync --extra demo

# 运行演示（请确保服务器已运行）
uv run python demo.py
```

## 开发

### 项目结构

```
aimemos/
├── aimemos/           # 主包
│   ├── __init__.py    # 包初始化
│   ├── app.py         # FastAPI 应用
│   ├── config.py      # 配置管理
│   ├── main.py        # 入口点
│   ├── models.py      # Pydantic 模型
│   ├── routes.py      # API 路由
│   └── storage.py     # 数据存储层
├── demo.py            # 演示脚本
├── .env.example       # 环境变量示例文件
├── pyproject.toml     # 项目依赖
└── uv.lock            # 依赖锁定文件
```

### 配置

通过环境变量或 `.env` 文件管理配置：

- `HOST`: 服务器主机地址（默认：0.0.0.0）
- `PORT`: 服务器端口（默认：8000）
- `DEBUG`: 调试模式（默认：false）
- `APP_NAME`: 应用名称
- `APP_VERSION`: 应用版本

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。