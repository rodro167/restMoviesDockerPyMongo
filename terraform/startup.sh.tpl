#!/bin/bash
# startup.sh.tpl — runs once on VM first boot via GCP metadata startup script
# Installs Docker, writes docker-compose + .env, sets up the DB, starts the app.

set -euo pipefail
exec > /var/log/startup.log 2>&1
echo "=== Startup script started at $(date) ==="

# ── 1. Install Docker ────────────────────────────────────────────────────────
apt-get update -y
apt-get install -y ca-certificates curl gnupg

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg \
  | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin python3-pip

systemctl enable docker
systemctl start docker

# ── 2. Install Python deps for setup_db.py ──────────────────────────────────
pip3 install pymongo python-dotenv --break-system-packages

# ── 3. Write .env ────────────────────────────────────────────────────────────
mkdir -p /app
cat > /app/.env <<EOF
MONGO_URI=${mongo_uri}
MONGO_DB=${mongo_db}
JWT_SECRET_KEY=${jwt_secret_key}
FLASK_PORT=${flask_port}
EOF

# ── 4. Write docker-compose.yaml ─────────────────────────────────────────────
cat > /app/docker-compose.yaml <<'EOF'
services:
  mongo:
    container_name: mongo
    image: mongo:7
    restart: unless-stopped
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db
    environment:
      MONGO_INITDB_DATABASE: restMovies
    networks:
      - app_net
    healthcheck:
      test: ["CMD", "mongosh", "--quiet", "--eval", "db.adminCommand('ping').ok"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 20s

  restmovies:
    container_name: restmovies
    image: ${docker_image}
    restart: unless-stopped
    ports:
      - "4000:4000"
    env_file:
      - .env
    depends_on:
      mongo:
        condition: service_healthy
    networks:
      - app_net

volumes:
  mongo_data:

networks:
  app_net:
EOF

# ── 5. Pull images and start services ────────────────────────────────────────
cd /app
docker compose pull
docker compose up -d

# ── 6. Wait for Mongo to be healthy, then run DB setup ───────────────────────
echo "Waiting for MongoDB to be ready..."
until docker exec mongo mongosh --quiet --eval "db.adminCommand('ping').ok" 2>/dev/null | grep -q "1"; do
  echo "  Mongo not ready yet, retrying in 5s..."
  sleep 5
done
echo "MongoDB is ready."

# Download and run setup_db.py from the container
docker exec restmovies python setup_db.py || echo "setup_db.py not found in image — skipping (run manually if needed)"

echo "=== Startup script finished at $(date) ==="
echo "API available at: http://$(curl -s ifconfig.me):4000"
