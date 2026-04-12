# 部署说明

## 一、服务器环境要求

- Linux 服务器（推荐 Ubuntu 22.04+）
- Python 3.10+
- MySQL 5.7+ / 8.0（已有校园墙数据库）
- Redis 6+
- Nginx（用于反向代理 + HTTPS）

## 二、后端部署

### 2.1 上传代码

```bash
scp -r backend/ user@server:/opt/chaxun/backend/
```

### 2.2 安装依赖

```bash
cd /opt/chaxun/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2.3 配置环境变量

```bash
cp .env.example .env
vim .env
```

关键配置项说明：

| 变量 | 说明 | 示例 |
|------|------|------|
| `DB_HOST` | MySQL 地址 | `127.0.0.1` |
| `DB_PORT` | MySQL 端口 | `3306` |
| `DB_USER` | 只读数据库用户 | `readonly_user` |
| `DB_PASSWORD` | 数据库密码 | `your_password` |
| `DB_NAME` | 数据库名 | `campus_wall` |
| `DB_TABLE_NAME` | 贴文表名 | `posts` |
| `REDIS_URL` | Redis 连接地址 | `redis://127.0.0.1:6379/0` |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | `sk-xxxx` |
| `DEEPSEEK_BASE_URL` | DeepSeek API 地址 | `https://api.deepseek.com` |
| `DEEPSEEK_MODEL` | 模型名称 | `deepseek-chat` |
| `WECHAT_APPID` | 微信小程序 AppID | `wxXXX` |
| `WECHAT_SECRET` | 微信小程序 Secret | `xxx` |
| `RATE_LIMIT_PER_MINUTE` | 每用户每分钟问答限制 | `5` |

### 2.4 适配数据库表结构

编辑 `app/models.py`，将 ORM 模型的 `__tablename__` 和字段名映射到你的实际表结构。

例如，如果你的表名为 `wall_posts`，内容字段为 `text`：

```python
class Post(Base):
    __tablename__ = "wall_posts"
    id = Column(Integer, primary_key=True)
    content = Column("text", Text)  # 映射 text 字段到 content
    ...
```

### 2.5 创建数据库只读用户（推荐）

```sql
CREATE USER 'readonly_user'@'%' IDENTIFIED BY 'your_password';
GRANT SELECT ON campus_wall.* TO 'readonly_user'@'%';
FLUSH PRIVILEGES;
```

### 2.6 使用 Systemd 管理服务

创建 `/etc/systemd/system/chaxun.service`：

```ini
[Unit]
Description=Campus Wall Query API
After=network.target mysql.service redis.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/chaxun/backend
Environment=PATH=/opt/chaxun/backend/venv/bin
ExecStart=/opt/chaxun/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable chaxun
sudo systemctl start chaxun
```

## 三、Nginx 配置

微信小程序要求后端接口必须通过 HTTPS 访问。

```nginx
server {
    listen 443 ssl http2;
    server_name api.your-domain.com;

    ssl_certificate /etc/ssl/certs/your-domain.pem;
    ssl_certificate_key /etc/ssl/private/your-domain.key;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE 流式输出支持
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 120s;
    }
}

server {
    listen 80;
    server_name api.your-domain.com;
    return 301 https://$host$request_uri;
}
```

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## 四、小程序发布

### 4.1 配置 API 地址

编辑 `miniprogram/utils/config.js`，修改 `baseUrl` 为你的 HTTPS 域名：

```javascript
const config = {
  baseUrl: 'https://api.your-domain.com/api',
};
```

### 4.2 配置微信后台

1. 登录[微信公众平台](https://mp.weixin.qq.com/)
2. 开发管理 → 开发设置 → 服务器域名
3. 添加 `https://api.your-domain.com` 到 `request 合法域名`

### 4.3 替换 TabBar 图标

将 `miniprogram/assets/` 目录下的占位图标替换为正式设计的图标（PNG 格式，建议 81x81px）。

### 4.4 修改 AppID

编辑 `miniprogram/project.config.json`，将 `appid` 改为你的真实小程序 AppID。

### 4.5 上传发布

1. 使用微信开发者工具打开 `miniprogram/` 目录
2. 点击"上传"，填写版本号和描述
3. 在微信公众平台提交审核

## 五、管理后台

### 5.1 访问地址

后端启动后，浏览器访问 `https://api.your-domain.com/api/admin` 即可打开管理后台。

### 5.2 管理员账号

在 `.env` 中配置管理员凭据：

```
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password
ADMIN_JWT_SECRET=your_random_jwt_secret_key
```

**重要**：务必修改默认密码和 JWT Secret，生产环境禁止使用默认值。

### 5.3 功能说明

| 模块 | 功能 |
|------|------|
| 仪表盘 | 贴文统计、今日问答量、活跃会话数 |
| 贴文管理 | 分页浏览贴文、关键词搜索、查看详情 |
| 问答日志 | 查看用户 AI 问答记录（存储最近 500 条） |
| 系统设置 | 查看当前配置状态（限流、模型、数据库等） |

### 5.4 Nginx 配置补充

管理后台页面通过 `/api/admin` 路径访问，无需额外 Nginx 配置，已随后端 API 一起代理。如需限制管理后台仅内网访问：

```nginx
location /api/admin {
    allow 10.0.0.0/8;
    allow 172.16.0.0/12;
    allow 192.168.0.0/16;
    deny all;
    proxy_pass http://127.0.0.1:8000;
}
```

## 六、可选优化

### 6.1 MySQL 全文索引

如果贴文量较大（>10万条），建议对 content 字段建立全文索引以提升搜索性能：

```sql
ALTER TABLE posts ADD FULLTEXT INDEX ft_content (content) WITH PARSER ngram;
```

建索引后，在 `app/services/search.py` 中将 `use_fulltext` 参数设为 `True`。

### 6.2 Redis 安全

生产环境建议为 Redis 设置密码，并在 `REDIS_URL` 中包含密码：

```
REDIS_URL=redis://:your_redis_password@127.0.0.1:6379/0
```
