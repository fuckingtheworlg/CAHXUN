#!/bin/bash
# ============================================================
# 校园墙查询 — 服务器一键部署脚本
# 在阿里云 ECS 上以 root 运行: bash deploy.sh
# ============================================================

set -e

APP_DIR="/opt/chaxun"
REPO_URL=""  # <-- 填入你的 GitHub 仓库地址

echo "========================================="
echo "  校园墙查询 — 服务器部署"
echo "========================================="

# ─── 1. 系统依赖 ───
echo "[1/7] 安装系统依赖..."
if command -v dnf &>/dev/null; then
    dnf install -y python3 python3-pip python3-devel gcc redis nginx git
elif command -v yum &>/dev/null; then
    yum install -y python3 python3-pip python3-devel gcc redis nginx git
elif command -v apt &>/dev/null; then
    apt update && apt install -y python3 python3-pip python3-venv python3-dev gcc redis-server nginx git
fi

# ─── 2. 启动 Redis ───
echo "[2/7] 启动 Redis..."
systemctl enable redis 2>/dev/null || systemctl enable redis-server 2>/dev/null || true
systemctl start redis 2>/dev/null || systemctl start redis-server 2>/dev/null || true

# ─── 3. 拉取代码 ───
echo "[3/7] 拉取代码..."
if [ -d "$APP_DIR/backend" ]; then
    echo "  目录已存在，执行 git pull..."
    cd "$APP_DIR"
    git pull
else
    echo "  首次部署，执行 git clone..."
    if [ -z "$REPO_URL" ]; then
        echo "  错误: 请先在脚本中填写 REPO_URL"
        echo "  编辑本文件，将 REPO_URL 设为你的 GitHub 仓库地址"
        exit 1
    fi
    git clone "$REPO_URL" "$APP_DIR"
fi

# ─── 4. Python 虚拟环境 & 依赖 ───
echo "[4/7] 安装 Python 依赖..."
cd "$APP_DIR/backend"
python3 -m venv venv 2>/dev/null || python3 -m venv --without-pip venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# ─── 5. 环境变量 ───
if [ ! -f "$APP_DIR/backend/.env" ]; then
    echo "[5/7] 创建 .env 配置文件..."
    cp .env.example .env
    echo ""
    echo "  ⚠️  请编辑 $APP_DIR/backend/.env 填入真实配置！"
    echo "  运行: vim $APP_DIR/backend/.env"
    echo ""
else
    echo "[5/7] .env 已存在，跳过"
fi

# ─── 6. Systemd 服务 ───
echo "[6/7] 配置 Systemd 服务..."
cat > /etc/systemd/system/chaxun.service << 'EOF'
[Unit]
Description=Campus Wall Query API
After=network.target redis.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/chaxun/backend
Environment=PATH=/opt/chaxun/backend/venv/bin
ExecStart=/opt/chaxun/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable chaxun

# ─── 7. Nginx ───
echo "[7/7] 配置 Nginx..."
cat > /etc/nginx/conf.d/chaxun.conf << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE streaming support
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 120s;
    }
}
EOF

nginx -t && systemctl enable nginx && systemctl reload nginx

echo ""
echo "========================================="
echo "  部署完成！"
echo "========================================="
echo ""
echo "  后续步骤:"
echo "  1. 编辑配置:  vim $APP_DIR/backend/.env"
echo "  2. 启动服务:  systemctl start chaxun"
echo "  3. 查看状态:  systemctl status chaxun"
echo "  4. 查看日志:  journalctl -u chaxun -f"
echo "  5. 管理后台:  http://47.99.217.72/api/admin"
echo ""
echo "  如需 HTTPS（微信小程序必须），还需要:"
echo "  - 绑定域名并备案"
echo "  - 申请 SSL 证书"
echo "  - 修改 Nginx 配置为 HTTPS"
echo ""
