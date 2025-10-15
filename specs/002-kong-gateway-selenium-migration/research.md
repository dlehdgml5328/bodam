# Research: Kong Gateway 마이그레이션 및 Selenium 크롤러 전환

**Date**: 2025-10-15
**Feature**: Kong Gateway 마이그레이션 및 Selenium 크롤러 전환

## Research Areas

### 1. Kong Gateway Architecture

#### Decision: DB-less vs PostgreSQL Mode
**Chosen**: **DB-less mode (declarative configuration)**

**Rationale**:
- Kubernetes-native: Configuration stored in ConfigMaps/Secrets
- GitOps friendly: Version-controlled YAML configurations
- Faster startup times: No database dependency
- Easier rollback: `kubectl apply -f` previous config
- Better for <100 routes: Optimal for current 50+ route requirement

**Alternatives Considered**:
- **PostgreSQL mode**: Rejected because it adds operational complexity (DB backups, migrations, HA setup) for a use case that doesn't require runtime configuration changes
- **Hybrid mode**: Rejected as unnecessary complexity for initial implementation

**Implementation Details**:
- Configuration file: `kong.yaml` in ConfigMap
- Dynamic updates: `kubectl apply -f kong.yaml` + pod restart
- Backup strategy: Git repository as source of truth

#### Decision: Kong Plugins for API Gateway
**Chosen**:
1. **Rate Limiting Plugin**: `rate-limiting-advanced` (OSS alternative: `rate-limiting`)
2. **Authentication**: `jwt` + `key-auth` plugins
3. **CORS Plugin**: `cors`
4. **Request/Response Logging**: `file-log` or `http-log`
5. **Request Transformer**: `request-transformer`

**Rationale**:
- Rate Limiting: Protects backend from abuse, configurable per-route
- JWT Auth: Matches existing authentication system (FR-012 from spec 001)
- CORS: Centralized cross-origin policy management
- Logging: Structured JSON logs for observability
- Transformer: Header injection for tracing (X-Request-ID)

**Best Practices**:
- Start with minimal plugins, add incrementally
- Use plugin scoping: global < service < route
- Monitor plugin overhead (<10ms p95 per plugin)

---

### 2. Selenium WebDriver Setup

#### Decision: Browser Choice
**Chosen**: **Chrome headless (via ChromeDriver)**

**Rationale**:
- Most common browser for web testing: Better community support
- Headless mode: 40% less memory vs GUI mode (~300MB vs ~500MB per instance)
- WebDriver Manager: Auto-downloads matching ChromeDriver version
- Best JavaScript engine compatibility: V8 matches Node.js ecosystem

**Alternatives Considered**:
- **Firefox (GeckoDriver)**: Rejected due to slower JavaScript execution and larger memory footprint in headless mode
- **Playwright**: Rejected to minimize scope (Selenium is widely adopted, team familiarity assumed)

**Implementation Details**:
```python
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')  # Required for Docker
options.add_argument('--disable-dev-shm-usage')  # Overcome limited resource problems
options.add_argument('--disable-gpu')  # Applicable to Windows

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)
```

#### Decision: WebDriver Connection Pooling
**Chosen**: **Custom connection pool with max 10 instances per worker**

**Rationale**:
- Browser startup cost: 2-3 seconds per instance
- Memory constraint: 2GB / 300MB = ~6 instances per pod
- Pool management: Reuse instances for multiple jobs, reset state between jobs

**Pattern**:
```python
from queue import Queue
import atexit

class WebDriverPool:
    def __init__(self, max_size=10):
        self.pool = Queue(maxsize=max_size)
        self._initialize_pool(max_size)

    def _initialize_pool(self, size):
        for _ in range(size):
            driver = self._create_driver()
            self.pool.put(driver)

    def acquire(self):
        return self.pool.get()

    def release(self, driver):
        # Clear cookies, reset state
        driver.delete_all_cookies()
        self.pool.put(driver)

    def cleanup(self):
        while not self.pool.empty():
            driver = self.pool.get()
            driver.quit()

# Global pool
driver_pool = WebDriverPool(max_size=10)
atexit.register(driver_pool.cleanup)
```

**Best Practices**:
- Timeout configuration: Page load timeout 30s, script timeout 10s
- Explicit waits: `WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "content")))`
- Error handling: Catch `TimeoutException`, `NoSuchElementException`, retry once

#### Decision: Selenium Deployment Model
**Chosen**: **Standalone instances in Celery workers (not Selenium Grid)**

**Rationale**:
- Simpler architecture: No separate Grid hub/nodes
- Kubernetes-native scaling: `kubectl scale deployment celery-worker`
- Celery already handles job distribution
- Lower operational overhead: One less service to maintain

**Alternatives Considered**:
- **Selenium Grid**: Rejected because Celery already provides distributed task execution; Grid adds unnecessary complexity

---

### 3. NGINX Static File Optimization

#### Decision: NGINX Caching Strategy
**Chosen**: **Aggressive caching with versioned asset URLs**

**Rationale**:
- Static assets (CSS, JS, images) rarely change
- Cache-Control headers: `public, max-age=31536000` (1 year) for versioned assets
- Versioning: Asset URLs include hash (e.g., `app.a1b2c3d4.js`) for cache busting
- ETag support: For non-versioned files

**Configuration**:
```nginx
location ~* \.(css|js|jpg|jpeg|png|gif|ico|svg|woff|woff2|ttf)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    access_log off;  # Reduce I/O for static files
}

location /static/ {
    alias /usr/share/nginx/html/static/;
    try_files $uri =404;
}
```

#### Decision: TLS Termination with cert-manager
**Chosen**: **cert-manager with Let's Encrypt (ACME)**

**Rationale**:
- Automatic certificate renewal: No manual intervention
- Kubernetes-native: CRDs for Certificate resources
- Free certificates: Let's Encrypt for public domains
- HTTP-01 challenge: Works with standard LoadBalancer

**Implementation**:
```yaml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: bodam-tls
spec:
  secretName: bodam-tls-secret
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
    - api.bodam.example
    - app.bodam.example
```

**NGINX Configuration**:
```nginx
server {
    listen 443 ssl http2;
    server_name api.bodam.example app.bodam.example;

    ssl_certificate /etc/nginx/tls/tls.crt;
    ssl_certificate_key /etc/nginx/tls/tls.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
}
```

#### Decision: NGINX Upstream for Kong Gateway
**Chosen**: **Kubernetes Service name resolution**

**Configuration**:
```nginx
upstream kong_upstream {
    server kong-gateway.default.svc.cluster.local:8000;
    keepalive 32;  # Connection pooling
}

location /api/ {
    proxy_pass http://kong_upstream;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

---

### 4. Migration Strategy

#### Decision: Blue-Green vs Canary Deployment
**Chosen**: **Canary deployment with traffic splitting**

**Rationale**:
- Gradual rollout: 10% → 50% → 100% traffic to Kong Gateway
- Early validation: Detect issues with 10% of traffic before full rollout
- Easy rollback: Revert traffic split if errors increase
- Kubernetes-native: Use Service weights or Ingress annotations

**Migration Sequence**:
1. **Phase 1 (Week 1)**: Deploy Kong Gateway alongside NGINX Ingress
   - Kong Gateway handles 0% traffic (shadow mode)
   - Monitor Kong Gateway health, resource usage
2. **Phase 2 (Week 2)**: Route low-traffic endpoints to Kong (10% of total traffic)
   - Example: Admin API endpoints
   - Monitor error rates, latency
3. **Phase 3 (Week 3)**: Increase to 50% of traffic
   - Include medium-traffic endpoints (user profile, settings)
4. **Phase 4 (Week 4)**: Full migration (100% of traffic)
   - High-traffic endpoints (donations, fire station search)
5. **Phase 5 (Week 5)**: Decommission NGINX Ingress API routing
   - Keep NGINX for static files + TLS termination

**Traffic Split Implementation (NGINX)**:
```nginx
split_clients "${remote_addr}" $backend_upstream {
    10% kong_upstream;   # Phase 2
    * nginx_ingress;     # Fallback to old Ingress
}

location /api/ {
    proxy_pass http://$backend_upstream;
}
```

#### Decision: Route Migration Sequence
**Chosen**: Low-traffic → Medium-traffic → High-traffic

**Order**:
1. Admin endpoints (`/api/admin/*`) - <100 req/day
2. User management (`/api/users/profile`) - ~1k req/day
3. Fire station lookup (`/api/fire-stations/search`) - ~5k req/day
4. Donation endpoints (`/api/donations/*`) - ~3k req/day (financial, critical)

**Rationale**:
- Low-risk first: Admin endpoints have minimal user impact
- Critical last: Donation endpoints are revenue-generating
- Monitoring window: 48 hours per phase before proceeding

#### Decision: Rollback Mechanism
**Chosen**: **Immediate traffic revert + NGINX Ingress standby**

**Trigger Conditions**:
- Error rate >5% for 5 minutes
- Latency p95 >500ms (vs baseline <300ms)
- Kong Gateway pod crashes

**Rollback Procedure**:
1. Set traffic split to 0% Kong Gateway (immediate)
2. Investigate Kong Gateway logs and metrics
3. Fix issue in staging environment
4. Retry migration phase

**Best Practices**:
- Keep NGINX Ingress running for 2 weeks post-migration
- Automated rollback: Prometheus AlertManager + Kubernetes Job
- Runbook: Document rollback steps in `infra/runbooks/kong-rollback.md`

---

## Dependencies Added

### Backend (requirements.txt)
```
selenium>=4.15.0
webdriver-manager>=4.0.0
```

### Infrastructure (Kubernetes)
- **Kong Gateway Image**: `kong:3.5-alpine`
- **cert-manager**: v1.13+ (for TLS certificates)

---

## Summary of Decisions

| Area | Decision | Key Rationale |
|------|----------|---------------|
| Kong Mode | DB-less (declarative) | Kubernetes-native, GitOps friendly |
| Browser | Chrome headless | Best compatibility, lower memory |
| WebDriver Pool | Custom pool (max 10) | Reuse instances, reduce startup cost |
| Deployment | Standalone in Celery workers | Simpler than Selenium Grid |
| NGINX Caching | 1-year cache + versioned assets | Maximize static file performance |
| TLS | cert-manager + Let's Encrypt | Automatic renewal, free certs |
| Migration | Canary (10% → 50% → 100%) | Gradual validation, easy rollback |
| Route Order | Low-traffic → High-traffic | Minimize risk, critical endpoints last |

---

## Open Questions Resolved
All NEEDS CLARIFICATION items from Technical Context have been resolved through this research.

**Status**: ✅ Research complete, ready for Phase 1 (Design & Contracts)
