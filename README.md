# AI Memos

基于 FastAPI 和 PocketFlow 构建的 AI 个人知识库服务。

## 技术栈

- **Python 3.12+**: 现代 Python 特性
- **uv**: 快速的 Python 包管理器
- **FastAPI**: 高性能 Web 框架
- **PocketFlow**: AI 工作流框架
- **Pydantic**: 数据验证和设置管理
- **JWT**: JSON Web Token 认证
- **SQLite**: 轻量级数据持久化存储

## 功能特性

- 用户注册和登录认证系统
- 基于 JWT 的安全认证
- 用户数据隔离（每个用户只能访问自己的数据）
- 可配置的用户注册功能
- 创建、读取、更新和删除备忘录
- 按标题、内容或标签搜索备忘录
- 带自动文档的 RESTful API
- SQLite 数据持久化存储（支持跨重启数据保留）
- 自动数据库初始化和索引优化
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
# 重要：修改 SECRET_KEY 为您自己的密钥
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

#### 用户认证

- `POST /api/v1/auth/register` - 用户注册（如果允许注册）
- `POST /api/v1/auth/login` - 用户登录

#### 备忘录（需要认证）

- `POST /api/v1/memos` - 创建新备忘录
- `GET /api/v1/memos` - 列出所有备忘录（支持分页）
- `GET /api/v1/memos/search?q=query` - 搜索备忘录
- `GET /api/v1/memos/{id}` - 获取指定备忘录
- `PUT /api/v1/memos/{id}` - 更新备忘录
- `DELETE /api/v1/memos/{id}` - 删除备忘录

### 使用示例

#### 1. 用户注册和登录

注册新用户：
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "myuser",
    "password": "mypassword"
  }'
```

用户登录：
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "myuser",
    "password": "mypassword"
  }'
```

返回的响应包含访问令牌（access_token），您需要在后续请求中使用它。

#### 2. 使用令牌访问备忘录 API

创建备忘录（需要认证）：
```bash
# 首先获取令牌
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"myuser","password":"mypassword"}' | \
  python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# 使用令牌创建备忘录
curl -X POST "http://localhost:8000/api/v1/memos" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "我的第一条备忘录",
    "content": "这是备忘录的内容",
    "tags": ["个人", "测试"]
  }'
```

列出备忘录（需要认证）：
```bash
curl "http://localhost:8000/api/v1/memos" \
  -H "Authorization: Bearer $TOKEN"
```

搜索备忘录（需要认证）：
```bash
curl "http://localhost:8000/api/v1/memos/search?q=第一条" \
  -H "Authorization: Bearer $TOKEN"
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
│   ├── auth.py        # 用户认证
│   ├── config.py      # 配置管理
│   ├── dependencies.py # FastAPI 依赖项
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
- `SECRET_KEY`: JWT 签名密钥（生产环境必须修改）
- `ALGORITHM`: JWT 签名算法（默认：HS256）
- `ACCESS_TOKEN_EXPIRE_MINUTES`: 访问令牌过期时间（默认：30 分钟）
- `ENABLE_REGISTRATION`: 是否允许注册新用户（默认：true）
- `DATABASE_URL`: 数据库文件路径（默认：sqlite:///./aimemos.db）

### 数据持久化

系统使用 SQLite 数据库进行数据持久化：

- **自动初始化**: 应用启动时自动创建数据库和表结构
- **索引优化**: 自动创建索引以提高查询性能
- **数据保留**: 服务器重启后数据不会丢失
- **文件位置**: 默认数据库文件为 `aimemos.db`，可通过 `DATABASE_URL` 配置修改

### 安全注意事项

1. **SECRET_KEY**: 生产环境中必须更改为强随机密钥
2. **HTTPS**: 生产环境中应使用 HTTPS 来保护令牌传输
3. **密码策略**: 建议设置最小密码长度为 6 个字符
4. **注册控制**: 生产环境中可以关闭 `ENABLE_REGISTRATION` 以控制用户访问
5. **数据库备份**: 定期备份 SQLite 数据库文件以防数据丢失

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。