sudo bash -c 'cat > /home/administrator/redeploy_dashboard.sh' << "EOF"
#!/bin/bash
set -euo pipefail

# ====== Cấu hình cơ bản ======
APP_NAME="my_streamlit"                    # tên container
APP_PORT=8501                              # port app streamlit trong container
REPO_URL="https://github.com/truongquangphuc/dashboard-766"  # đổi link nếu dùng repo khác
APP_DIR="/home/administrator/dashboard-766" # thư mục source trên server

echo "=== $(date) Bắt đầu redeploy ==="

# ====== Lấy code mới ======
if [ -d "$APP_DIR/.git" ]; then
  cd "$APP_DIR"
  # đảm bảo remote đúng URL (nếu bạn đổi link repo, chỉ cần sửa REPO_URL ở trên)
  CURRENT_URL=$(git remote get-url origin || echo "")
  if [ "$CURRENT_URL" != "$REPO_URL" ]; then
    git remote set-url origin "$REPO_URL"
  fi
  git fetch origin
  # tự nhận biết nhánh mặc định, fallback về main nếu không đọc được
  BRANCH=$(git remote show origin | sed -n "/HEAD branch/s/.*: //p")
  BRANCH=${BRANCH:-main}
  git reset --hard
  git checkout "$BRANCH" || true
  git pull origin "$BRANCH"
else
  # nếu chưa có thì clone mới
  mkdir -p "$(dirname "$APP_DIR")"
  git clone "$REPO_URL" "$APP_DIR"
  cd "$APP_DIR"
fi

# ====== Triển khai Docker ======
# Nếu có docker-compose/compose, dùng compose; không thì build/run Dockerfile
if [ -f "docker-compose.yml" ] || [ -f "docker-compose.yaml" ] || [ -f "compose.yaml" ]; then
  if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE="docker-compose"
  else
    COMPOSE="docker compose"
  fi
  $COMPOSE down || true
  $COMPOSE build --no-cache
  $COMPOSE up -d
else
  docker stop "$APP_NAME" || true
  docker rm "$APP_NAME" || true
  docker build --no-cache -t "$APP_NAME" .
  docker run -d \
    --name "$APP_NAME" \
    -p $APP_PORT:8501 \
    --restart=always \
    "$APP_NAME"
fi

# ====== Reload/restart nginx ======
systemctl reload nginx || systemctl restart nginx

echo "=== $(date) Redeploy hoàn tất ==="
EOF

# cấp quyền chạy
sudo chmod +x /home/administrator/redeploy_dashboard.sh
