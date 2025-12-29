# Deployment Guide

This guide covers deploying sitq in production environments, including configuration, scaling, and monitoring.

## Production Deployment Architecture

### Single-Node Deployment

```
┌─────────────────────────────────────────────────────────┐
│                Production Server                        │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Web App   │  │ sitq Queue  │  │ sitq Worker │    │
│  │             │  │             │  │             │    │
│  │ - Flask     │  │ - TaskQueue │  │ - Worker    │    │
│  │ - Django    │  │ - Backend   │  │ - Process   │    │
│  │ - FastAPI   │  │ - Storage   │  │ - Monitor   │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│         │                │                │              │
│         └────────────────┼────────────────┘              │
│                          │                               │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              SQLite Database                        │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │ │
│  │  │ tasks.db    │  │ results.db  │  │ queue.db│ │ │
│  │  └─────────────┘  └─────────────┘  └─────────┘ │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Multi-Node Deployment

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Server 1  │    │   Web Server 2  │    │   Web Server N  │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │   App      │ │    │ │   App      │ │    │ │   App      │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Load Balancer  │
                    │                 │
                    │ - Nginx        │
                    │ - HAProxy      │
                    └─────────┬───────┘
                              │
                    ┌─────────────────┐
                    │ sitq Cluster   │
                    │                 │
                    │ ┌─────────────┐ │
                    │ │   Queue     │ │
                    │ │   Backend   │ │
                    │ └─────────────┘ │
                    │                 │
                    │ ┌─────────────┐ │
                    │ │  Workers    │ │
                    │ │ - Worker 1  │ │
                    │ │ - Worker 2  │ │
                    │ │ - Worker N  │ │
                    │ └─────────────┘ │
                    └─────────┬───────┘
                              │
                    ┌─────────────────┐
                    │  Shared Storage │
                    │                 │
                    │ - NFS         │
                    │ - Database    │
                    │ - Redis       │
                    └─────────────────┘
```

## Docker Deployment

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY sitq/ ./sitq/

# Install sitq
RUN pip install -e .

# Create non-root user
RUN useradd --create-home --shell /bin/bash sitq
USER sitq

# Create directories
RUN mkdir -p /app/data /app/logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sitq; print('OK')" || exit 1

# Default command
CMD ["python", "-m", "sitq.worker", "--config", "/app/config/production.yaml"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Web Application
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SITQ_BACKEND_URL=sqlite:///data/tasks.db
      - SITQ_LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config:/app/config
    depends_on:
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Worker Service
  worker:
    build: .
    command: ["python", "-m", "sitq.worker", "--config", "/app/config/worker.yaml"]
    environment:
      - SITQ_BACKEND_URL=sqlite:///data/tasks.db
      - SITQ_WORKER_ID=worker-${HOSTNAME}
      - SITQ_LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config:/app/config
    depends_on:
      - redis
    restart: unless-stopped
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  # Redis for caching and session storage
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
    command: redis-server --appendonly yes

  # Monitoring
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning
    restart: unless-stopped

volumes:
  redis_data:
  prometheus_data:
  grafana_data:

networks:
  default:
    driver: bridge
```

## Kubernetes Deployment

### Namespace and ConfigMap

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: sitq
  labels:
    name: sitq

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: sitq-config
  namespace: sitq
data:
  config.yaml: |
    backend:
      type: sqlite
      database: /data/tasks.db
      connection_pool_size: 20
      enable_wal: true
    
    worker:
      max_workers: 4
      poll_interval: 0.5
      timeout: 300
      max_retries: 3
      retry_delay: 1.0
    
    logging:
      level: INFO
      format: json
      file: /logs/sitq.log
```

### Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sitq-worker
  namespace: sitq
  labels:
    app: sitq-worker
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sitq-worker
  template:
    metadata:
      labels:
        app: sitq-worker
    spec:
      containers:
      - name: sitq-worker
        image: sitq:latest
        command: ["python", "-m", "sitq.worker"]
        args: ["--config", "/etc/sitq/config.yaml"]
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: SITQ_WORKER_ID
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: SITQ_LOG_LEVEL
          value: "INFO"
        volumeMounts:
        - name: config
          mountPath: /etc/sitq
        - name: data
          mountPath: /data
        - name: logs
          mountPath: /logs
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: config
        configMap:
          name: sitq-config
      - name: data
        persistentVolumeClaim:
          claimName: sitq-data-pvc
      - name: logs
        emptyDir: {}
      restartPolicy: Always

---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: sitq-worker-service
  namespace: sitq
  labels:
    app: sitq-worker
spec:
  selector:
    app: sitq-worker
  ports:
  - name: http
    port: 8000
    targetPort: 8000
    protocol: TCP
  type: ClusterIP

---
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: sitq-worker-hpa
  namespace: sitq
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sitq-worker
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Persistent Volume

```yaml
# k8s/pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: sitq-data-pvc
  namespace: sitq
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: fast-ssd
```

## Configuration Management

### Environment Variables

```bash
# .env.production
# Database Configuration
SITQ_BACKEND_TYPE=sqlite
SITQ_BACKEND_DATABASE=/data/sitq/tasks.db
SITQ_BACKEND_CONNECTION_POOL_SIZE=20
SITQ_BACKEND_ENABLE_WAL=true

# Worker Configuration
SITQ_WORKER_MAX_WORKERS=4
SITQ_WORKER_POLL_INTERVAL=0.5
SITQ_WORKER_TIMEOUT=300
SITQ_WORKER_MAX_RETRIES=3
SITQ_WORKER_RETRY_DELAY=1.0

# Logging Configuration
SITQ_LOG_LEVEL=INFO
SITQ_LOG_FORMAT=json
SITQ_LOG_FILE=/logs/sitq.log
SITQ_LOG_MAX_SIZE=100MB
SITQ_LOG_BACKUP_COUNT=5

# Monitoring Configuration
SITQ_METRICS_ENABLED=true
SITQ_METRICS_PORT=9090
SITQ_HEALTH_CHECK_ENABLED=true
SITQ_HEALTH_CHECK_PORT=8000

# Security Configuration
SITQ_AUTH_ENABLED=true
SITQ_AUTH_SECRET_KEY=${SITQ_SECRET_KEY}
SITQ_AUTH_TOKEN_EXPIRY=3600
```

### YAML Configuration

```yaml
# config/production.yaml
backend:
  type: sqlite
  database: /data/sitq/tasks.db
  connection_pool_size: 20
  max_overflow: 10
  connection_timeout: 30
  enable_wal: true
  synchronous: NORMAL
  cache_size: 50000
  temp_store: MEMORY

worker:
  max_workers: 4
  poll_interval: 0.5
  timeout: 300
  max_retries: 3
  retry_delay: 1.0
  backoff_factor: 2.0
  max_memory_mb: 1024
  max_cpu_percent: 80

logging:
  level: INFO
  format: json
  file: /logs/sitq.log
  max_size: 100MB
  backup_count: 5
  console: true

monitoring:
  metrics_enabled: true
  metrics_port: 9090
  health_check_enabled: true
  health_check_port: 8000
  prometheus_enabled: true

security:
  auth_enabled: true
  secret_key: ${SITQ_SECRET_KEY}
  token_expiry: 3600
  allowed_origins:
    - https://app.example.com
    - https://admin.example.com
```

## Monitoring and Observability

### Prometheus Configuration

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "sitq_rules.yml"

scrape_configs:
  - job_name: 'sitq-workers'
    static_configs:
      - targets: 
        - 'worker-1:9090'
        - 'worker-2:9090'
        - 'worker-3:9090'
    metrics_path: /metrics
    scrape_interval: 10s

  - job_name: 'sitq-queue'
    static_configs:
      - targets: ['queue:9090']
    metrics_path: /metrics
    scrape_interval: 10s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### Alert Rules

```yaml
# monitoring/sitq_rules.yml
groups:
  - name: sitq_alerts
    rules:
      - alert: HighErrorRate
        expr: sitq_error_rate > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} for {{ $labels.instance }}"

      - alert: HighQueueDepth
        expr: sitq_queue_depth > 1000
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Queue depth too high"
          description: "Queue depth is {{ $value }} for {{ $labels.instance }}"

      - alert: WorkerDown
        expr: up{job="sitq-workers"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Worker is down"
          description: "Worker {{ $labels.instance }} has been down for more than 1 minute"

      - alert: HighMemoryUsage
        expr: sitq_memory_usage_bytes / sitq_memory_limit_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value | humanizePercentage }} for {{ $labels.instance }}"
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "sitq Monitoring",
    "panels": [
      {
        "title": "Task Throughput",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(sitq_tasks_processed_total[5m])",
            "legendFormat": "{{instance}}"
          }
        ]
      },
      {
        "title": "Queue Depth",
        "type": "singlestat",
        "targets": [
          {
            "expr": "sitq_queue_depth",
            "legendFormat": "Queue Depth"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(sitq_tasks_failed_total[5m]) / rate(sitq_tasks_processed_total[5m])",
            "legendFormat": "Error Rate"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "sitq_memory_usage_bytes",
            "legendFormat": "{{instance}}"
          }
        ]
      }
    ]
  }
}
```

## Security

### Authentication and Authorization

```python
# security/auth.py
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class AuthManager:
    """Authentication and authorization manager."""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.token_expiry = timedelta(hours=1)
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def generate_token(self, user_id: str, permissions: list) -> str:
        """Generate JWT token."""
        payload = {
            'user_id': user_id,
            'permissions': permissions,
            'exp': datetime.utcnow() + self.token_expiry,
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def has_permission(self, token: str, permission: str) -> bool:
        """Check if token has specific permission."""
        payload = self.verify_token(token)
        if not payload:
            return False
        return permission in payload.get('permissions', [])
```

### Network Security

```yaml
# k8s/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: sitq-network-policy
  namespace: sitq
spec:
  podSelector:
    matchLabels:
      app: sitq-worker
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    - podSelector:
        matchLabels:
          app: sitq-web
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: sitq-queue
    ports:
    - protocol: TCP
      port: 5432
  - to: []
    ports:
    - protocol: TCP
      port: 53
    - protocol: UDP
      port: 53
    - protocol: TCP
      port: 443
```

## Backup and Recovery

### Backup Script

```bash
#!/bin/bash
# scripts/backup.sh

set -e

# Configuration
BACKUP_DIR="/backups/sitq"
DATA_DIR="/data/sitq"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup SQLite database
echo "Backing up SQLite database..."
sqlite3 "$DATA_DIR/tasks.db" ".backup $BACKUP_DIR/tasks_$TIMESTAMP.db"

# Backup configuration
echo "Backing up configuration..."
tar -czf "$BACKUP_DIR/config_$TIMESTAMP.tar.gz" /etc/sitq/

# Backup logs (last 7 days)
echo "Backing up logs..."
find /var/log/sitq -name "*.log" -mtime -7 -exec tar -czf "$BACKUP_DIR/logs_$TIMESTAMP.tar.gz" {} +

# Create backup manifest
cat > "$BACKUP_DIR/manifest_$TIMESTAMP.txt" << EOF
Backup created: $(date)
Database: tasks_$TIMESTAMP.db
Config: config_$TIMESTAMP.tar.gz
Logs: logs_$TIMESTAMP.tar.gz
EOF

# Clean old backups
echo "Cleaning old backups..."
find "$BACKUP_DIR" -name "*.db" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "manifest_*.txt" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: $TIMESTAMP"
```

### Recovery Script

```bash
#!/bin/bash
# scripts/recover.sh

set -e

if [ $# -ne 1 ]; then
    echo "Usage: $0 <backup_timestamp>"
    echo "Example: $0 20231201_120000"
    exit 1
fi

TIMESTAMP=$1
BACKUP_DIR="/backups/sitq"
DATA_DIR="/data/sitq"

# Stop services
echo "Stopping sitq services..."
systemctl stop sitq-worker
systemctl stop sitq-web

# Backup current data
echo "Backing up current data..."
mv "$DATA_DIR/tasks.db" "$DATA_DIR/tasks.db.backup.$(date +%Y%m%d_%H%M%S)"

# Restore database
echo "Restoring database..."
cp "$BACKUP_DIR/tasks_$TIMESTAMP.db" "$DATA_DIR/tasks.db"

# Restore configuration
echo "Restoring configuration..."
tar -xzf "$BACKUP_DIR/config_$TIMESTAMP.tar.gz" -C /

# Restore logs
echo "Restoring logs..."
tar -xzf "$BACKUP_DIR/logs_$TIMESTAMP.tar.gz" -C /var/log/

# Set permissions
chown -R sitq:sitq "$DATA_DIR"
chmod 644 "$DATA_DIR/tasks.db"

# Start services
echo "Starting sitq services..."
systemctl start sitq-worker
systemctl start sitq-web

echo "Recovery completed from backup: $TIMESTAMP"
```

## Performance Tuning

### System Optimization

```bash
#!/bin/bash
# scripts/optimize_system.sh

# Increase file descriptor limit
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# Optimize TCP settings
cat >> /etc/sysctl.conf << EOF
# Network optimization for sitq
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 1200
net.ipv4.tcp_max_tw_buckets = 5000
EOF

# Apply sysctl settings
sysctl -p

# Optimize I/O scheduler
echo deadline > /sys/block/sda/queue/scheduler

# Configure swappiness
echo 10 > /proc/sys/vm/swappiness
```

### Database Optimization

```sql
-- scripts/optimize_sqlite.sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 50000;
PRAGMA temp_store = MEMORY;
PRAGMA mmap_size = 1073741824;  -- 1GB
PRAGMA page_size = 4096;
PRAGMA wal_autocheckpoint = 1000;
PRAGMA optimize;
```

## Troubleshooting

### Common Issues

1. **High Memory Usage**
   ```bash
   # Check memory usage
   ps aux | grep sitq
   top -p $(pgrep -f sitq.worker)
   
   # Check for memory leaks
   valgrind --tool=memcheck python -m sitq.worker
   ```

2. **Database Locking**
   ```bash
   # Check for locked processes
   lsof /data/sitq/tasks.db
   
   # Check SQLite status
   sqlite3 /data/sitq/tasks.db "PRAGMA lock_status;"
   ```

3. **Performance Issues**
   ```bash
   # Profile worker
   python -m cProfile -o profile.stats -m sitq.worker
   
   # Analyze profile
   python -c "
   import pstats
   p = pstats.Stats('profile.stats')
   p.sort_stats('cumulative')
   p.print_stats(20)
   "
   ```

### Health Checks

```python
# health_check.py
import requests
import sys
import time

def check_health(endpoint: str) -> bool:
    """Check health of sitq component."""
    try:
        response = requests.get(f"{endpoint}/health", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

def main():
    """Main health check."""
    endpoints = [
        "http://localhost:8000",
        "http://localhost:8001",
        "http://localhost:8002"
    ]
    
    all_healthy = True
    
    for endpoint in endpoints:
        if check_health(endpoint):
            print(f"✅ {endpoint} is healthy")
        else:
            print(f"❌ {endpoint} is unhealthy")
            all_healthy = False
    
    if not all_healthy:
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## Best Practices

### Production Checklist

- [ ] **Configuration Management**
  - [ ] Use environment variables for secrets
  - [ ] Version control configuration files
  - [ ] Separate config per environment

- [ ] **Security**
  - [ ] Enable authentication
  - [ ] Use HTTPS in production
  - [ ] Implement rate limiting
  - [ ] Regular security updates

- [ ] **Monitoring**
  - [ ] Set up metrics collection
  - [ ] Configure alerting
  - [ ] Monitor resource usage
  - [ ] Log aggregation

- [ ] **Backup**
  - [ ] Automated daily backups
  - [ ] Off-site backup storage
  - [ ] Regular recovery testing
  - [ ] Backup retention policy

- [ ] **Performance**
  - [ ] Load testing
  - [ ] Performance monitoring
  - [ ] Resource optimization
  - [ ] Capacity planning

- [ ] **Reliability**
  - [ ] Health checks
  - [ ] Graceful shutdown
  - [ ] Error handling
  - [ ] Circuit breakers

## Next Steps

- [Contributing Guide](contributing.md) - Learn how to contribute
- [Performance Guide](performance.md) - Performance optimization
- [API Reference](../reference/api/sitq.md) - Detailed API documentation