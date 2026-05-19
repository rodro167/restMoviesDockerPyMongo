#!/bin/bash
# startup.sh.tpl — runs once on VM first boot via GCP metadata startup script
# Installs Docker, writes the full monitoring stack config, starts services.

set -euo pipefail
exec > /var/log/startup.log 2>&1
echo "=== Startup script started at $(date) ==="

# ── 1. Install Docker ─────────────────────────────────────────────────────────
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

# ── 2. Install Python deps for setup_db.py ───────────────────────────────────
pip3 install pymongo python-dotenv --break-system-packages

# ── 3. Write .env ─────────────────────────────────────────────────────────────
mkdir -p /app
cat > /app/.env <<EOF
MONGO_URI=${mongo_uri}
MONGO_DB=${mongo_db}
JWT_SECRET_KEY=${jwt_secret_key}
FLASK_PORT=${flask_port}
GRAFANA_ADMIN_PASSWORD=${grafana_admin_password}
EOF

# ── 4. Write prometheus/prometheus.yml ────────────────────────────────────────
mkdir -p /app/prometheus
cat > /app/prometheus/prometheus.yml <<'PROMEOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'restmovies'
    static_configs:
      - targets: ['restmovies:4000']

  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']

  - job_name: 'node'
    static_configs:
      - targets: ['host.docker.internal:9100']

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
PROMEOF

# ── 5. Write grafana datasource provisioning ─────────────────────────────────
mkdir -p /app/grafana/provisioning/datasources
cat > /app/grafana/provisioning/datasources/prometheus.yml <<'GRAFEOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
GRAFEOF

# ── 6. Write docker-compose.yaml (base stack) ────────────────────────────────
cat > /app/docker-compose.yaml <<'COMPOSEEOF'
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

  prometheus:
    container_name: prometheus
    image: prom/prometheus:v2.52.0
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=15d'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    extra_hosts:
      - "host.docker.internal:host-gateway"
    networks:
      - app_net

  grafana:
    container_name: grafana
    image: grafana/grafana:11.0.0
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=$${GRAFANA_ADMIN_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning/datasources:/etc/grafana/provisioning/datasources:ro
    depends_on:
      - prometheus
    networks:
      - app_net

  cadvisor:
    container_name: cadvisor
    image: gcr.io/cadvisor/cadvisor:v0.49.1
    restart: unless-stopped
    privileged: true
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker:/var/lib/docker:ro
      - /dev/disk:/dev/disk:ro
    networks:
      - app_net

volumes:
  mongo_data:
  prometheus_data:
  grafana_data:

networks:
  app_net:
COMPOSEEOF

# ── 7. Write docker-compose.gcp.yaml (GCP overlay: node-exporter) ────────────
cat > /app/docker-compose.gcp.yaml <<'GCPEOF'
services:
  node-exporter:
    container_name: node-exporter
    image: prom/node-exporter:v1.8.0
    restart: unless-stopped
    pid: host
    network_mode: host
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/host/root:ro,rslave
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--path.rootfs=/host/root'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($|/)'
GCPEOF

# ── 8. Pull images and start full monitoring stack ────────────────────────────
cd /app
docker compose -f docker-compose.yaml -f docker-compose.gcp.yaml pull
docker compose -f docker-compose.yaml -f docker-compose.gcp.yaml up -d

# ── 9. Wait for Mongo to be healthy, then run DB setup ───────────────────────
echo "Waiting for MongoDB to be ready..."
until docker exec mongo mongosh --quiet --eval "db.adminCommand('ping').ok" 2>/dev/null | grep -q "1"; do
  echo "  Mongo not ready yet, retrying in 5s..."
  sleep 5
done
echo "MongoDB is ready."

docker exec restmovies python setup_db.py || echo "setup_db.py not found in image — skipping (run manually if needed)"

echo "=== Startup script finished at $(date) ==="
PUBLIC_IP=$(curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip)
echo "API:        http://$PUBLIC_IP:4000"
echo "Grafana:    http://$PUBLIC_IP:3000"
echo "Prometheus: http://$PUBLIC_IP:9090"
