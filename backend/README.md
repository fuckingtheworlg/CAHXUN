# 校园墙查询 — 后端

基于 FastAPI 的轻量级后端，只读接入校园墙 MySQL 数据库，提供贴文检索和 AI 问答服务。

## 快速开始

### 1. 安装依赖

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入真实的数据库、Redis、DeepSeek、微信配置
```

### 3. 适配数据库表

编辑 `app/models.py`，将 `__tablename__` 和字段映射为你的实际数据库表结构。

### 4. 启动服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

访问 `http://localhost:8000/docs` 查看 API 文档。

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/posts` | 贴文列表（分页） |
| GET | `/api/posts/search?q=xxx` | 关键词搜索 |
| POST | `/api/chat` | AI 问答（SSE 流式） |
| POST | `/api/auth/login` | 微信登录 |
| GET | `/health` | 健康检查 |
