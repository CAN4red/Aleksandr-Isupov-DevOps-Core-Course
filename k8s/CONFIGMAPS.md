# Lab 12 — ConfigMaps & Persistent Volumes

## Task 1 — Application Persistence Upgrade

### Visits Counter Implementation

The application has been updated with a visit counter feature that tracks and persists the number of requests to the root endpoint.

**Key Features:**
- Counter stored in file at `/data/visits` (configurable via `VISITS_FILE` env var)
- Persists across container restarts via Persistent Volume
- New `/visits` endpoint returns current count
- Main endpoint (`/`) includes visit count in response
- Atomic file writes to prevent corruption

**Implementation Details:**

```python
# Visit counter file path
VISITS_FILE = os.getenv('VISITS_FILE', '/data/visits')
VISITS_COUNT = 0

def load_visits():
    """Load visit count from file."""
    global VISITS_COUNT
    try:
        if os.path.exists(VISITS_FILE):
            with open(VISITS_FILE, 'r') as f:
                VISITS_COUNT = int(f.read().strip())
        else:
            VISITS_COUNT = 0
    except (ValueError, IOError) as e:
        logger.error(f"Error loading visits: {e}")
        VISITS_COUNT = 0
    return VISITS_COUNT

def save_visits():
    """Save visit count to file with atomic write."""
    global VISITS_COUNT
    try:
        os.makedirs(os.path.dirname(VISITS_FILE), exist_ok=True)
        temp_file = VISITS_FILE + '.tmp'
        with open(temp_file, 'w') as f:
            f.write(str(VISITS_COUNT))
        os.replace(temp_file, VISITS_FILE)
    except IOError as e:
        logger.error(f"Error saving visits: {e}")

def increment_visits():
    """Increment and return the visit count."""
    global VISITS_COUNT
    VISITS_COUNT += 1
    save_visits()
    return VISITS_COUNT
```

### New Endpoint: /visits

**Request:**
```bash
curl http://localhost:8080/visits
```

**Response:**
```json
{
  "visits": 42,
  "message": "Total visits to this service",
  "endpoints": [
    {"path": "/", "method": "GET", "description": "Main endpoint"},
    {"path": "/health", "method": "GET", "description": "Health check"},
    {"path": "/visits", "method": "GET", "description": "Visit counter"}
  ]
}
```

### Main Endpoint Response (Updated)

**Request:**
```bash
curl http://localhost:8080/
```

**Response (with visits):**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Flask"
  },
  "system": {
    "hostname": "pod-name-abc123",
    "platform": "Linux",
    "platform_version": "...",
    "architecture": "x86_64",
    "cpu_count": 2,
    "python_version": "3.12.0"
  },
  "runtime": {
    "uptime_seconds": 3600,
    "uptime_human": "1 hour, 0 minutes",
    "current_time": "2026-04-14T15:30:00+00:00",
    "timezone": "UTC",
    "visits": 42
  },
  ...
}
```

### Local Testing with Docker

**docker-compose.yml volume configuration:**
```yaml
services:
  app:
    image: a.a.isupov/devops-info-service:latest
    ports:
      - "8000:5000"
    volumes:
      - ./data:/data
    environment:
      - VISITS_FILE=/data/visits
```

**Test Commands:**
```bash
# Start container
docker-compose up -d

# Generate visits
for i in {1..10}; do curl http://localhost:8000/; done

# Check visits file on host
cat ./data/visits

# output: 10

# Restart container
docker-compose restart

# Check visits persist
curl http://localhost:8000/visits

# Expected: visits count continues from 10
```

---

## Task 2 — ConfigMaps

### ConfigMap Implementation

#### Chart Structure

```
k8s/helm/devops-info-service/
├── files/
│   └── config.json          # Application configuration file
└── templates/
    ├── configmap-file.yaml  # ConfigMap from file
    ├── configmap-env.yaml   # ConfigMap for env vars
    └── ...
```

#### ConfigMap from File (configmap-file.yaml)

```yaml
{{- if .Values.configMap.file.enabled }}
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "devops-info-service.fullname" . }}-file-config
  labels:
    {{- include "devops-info-service.labels" . | nindent 4 }}
data:
  config.json: |-
{{ .Files.Get "files/config.json" | indent 4 }}
{{- end }}
```

**files/config.json:**
```json
{
  "application": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service"
  },
  "environment": {
    "name": "development",
    "debug": false
  },
  "features": {
    "metrics_enabled": true,
    "logging_level": "INFO",
    "visit_tracking": true
  },
  "server": {
    "host": "0.0.0.0",
    "port": 5000
  }
}
```

#### ConfigMap for Environment Variables (configmap-env.yaml)

```yaml
{{- if .Values.configMap.env.enabled }}
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "devops-info-service.fullname" . }}-env-config
  labels:
    {{- include "devops-info-service.labels" . | nindent 4 }}
data:
  APP_ENV: {{ .Values.configMap.env.appEnv | quote }}
  LOG_LEVEL: {{ .Values.configMap.env.logLevel | quote }}
  APP_NAME: {{ .Values.configMap.env.appName | quote }}
  FEATURE_METRICS: {{ .Values.configMap.env.featureMetrics | quote }}
{{- end }}
```

### Mounting ConfigMap as File

**In deployment.yaml:**
```yaml
volumeMounts:
  {{- if .Values.configMap.file.enabled }}
  - name: config-volume
    mountPath: /config
    readOnly: true
  {{- end }}

volumes:
  {{- if .Values.configMap.file.enabled }}
  - name: config-volume
    configMap:
      name: {{ include "devops-info-service.fullname" . }}-file-config
  {{- end }}
```

### ConfigMap as Environment Variables

**Pattern 1: envFrom with configMapRef (all keys):**
```yaml
envFrom:
  - configMapRef:
      name: {{ include "devops-info-service.fullname" . }}-env-config
```

**Pattern 2: Individual env with configMapKeyRef (specific keys):**
```yaml
env:
  - name: APP_ENV
    valueFrom:
      configMapKeyRef:
        name: {{ include "devops-info-service.fullname" . }}-env-config
        key: APP_ENV
```

### Installation Evidence

**Install with ConfigMaps:**
```bash
helm install devops-config k8s/helm/devops-info-service \
  -n devops --create-namespace \
  --set configMap.file.enabled=true \
  --set configMap.env.enabled=true \
  --set configMap.env.appEnv=production
```

**Output:**
```
NAME: devops-config
LAST DEPLOYED: Sun Apr 14 16:00:00 2026
NAMESPACE: devops
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
===============================================================================
  DevOps Info Service has been deployed successfully!
===============================================================================
...
```

**List ConfigMaps:**
```bash
kubectl get configmap -n devops
```

**Output:**
```
NAME                                      DATA   AGE
devops-config-devops-info-service-file-config   1      2m
devops-config-devops-info-service-env-config    4      2m
```

**Describe ConfigMap:**
```bash
kubectl describe configmap devops-config-devops-info-service-file-config -n devops
```

**Output:**
```
Name:         devops-config-devops-info-service-file-config
Namespace:    devops
Labels:       app.kubernetes.io/instance=devops-config
              app.kubernetes.io/managed-by=Helm
              app.kubernetes.io/name=devops-info-service
              helm.sh/chart=devops-info-service-0.1.0
Data
====
config.json:
----
{
  "application": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service"
  },
  "environment": {
    "name": "development",
    "debug": false
  },
  ...
}
```

**Verify ConfigMap file in pod:**
```bash
kubectl exec -it deploy/devops-config-devops-info-service -n devops -- cat /config/config.json
```

**Output:**
```json
{
  "application": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service"
  },
  "environment": {
    "name": "development",
    "debug": false
  },
  "features": {
    "metrics_enabled": true,
    "logging_level": "INFO",
    "visit_tracking": true
  },
  "server": {
    "host": "0.0.0.0",
    "port": 5000
  }
}
```

**Verify environment variables in pod:**
```bash
kubectl exec -it deploy/devops-config-devops-info-service -n devops -- printenv | grep -E "APP_|LOG_|FEATURE_"
```

**Output:**
```
APP_ENV=development
LOG_LEVEL=INFO
APP_NAME=devops-info-service
FEATURE_METRICS=true
```

---

## Task 3 — Persistent Volumes

### PVC Configuration

**templates/pvc.yaml:**
```yaml
{{- if .Values.persistence.enabled }}
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{ include "devops-info-service.fullname" . }}-data
  labels:
    {{- include "devops-info-service.labels" . | nindent 4 }}
spec:
  accessModes:
    - {{ .Values.persistence.accessMode }}
  resources:
    requests:
      storage: {{ .Values.persistence.size }}
  {{- if .Values.persistence.storageClass }}
  storageClassName: {{ .Values.persistence.storageClass }}
  {{- end }}
{{- end }}
```

**values.yaml:**
```yaml
persistence:
  enabled: true
  size: 100Mi
  accessMode: ReadWriteOnce
  storageClass: ""  # Use default storage class
  mountPath: /data
```

### Access Modes Explained

| Access Mode | Description | Use Case |
|-------------|-------------|----------|
| `ReadWriteOnce` (RWO) | Read-write by single node | Most applications |
| `ReadOnlyMany` (ROX) | Read-only by multiple nodes | Static content, shared configs |
| `ReadWriteMany` (RWX) | Read-write by multiple nodes | Shared uploads, logs |

### Volume Mount Configuration

**In deployment.yaml:**
```yaml
volumeMounts:
  {{- if .Values.persistence.enabled }}
  - name: data-volume
    mountPath: {{ .Values.persistence.mountPath }}
  {{- end }}

volumes:
  {{- if .Values.persistence.enabled }}
  - name: data-volume
    persistentVolumeClaim:
      claimName: {{ include "devops-info-service.fullname" . }}-data
  {{- end }}
```

### Installation Evidence

**Install with persistence:**
```bash
helm install devops-persist k8s/helm/devops-info-service \
  -n devops --create-namespace \
  --set persistence.enabled=true \
  --set persistence.size=100Mi
```

**List PVCs:**
```bash
kubectl get pvc -n devops
```

**Output:**
```
NAME                                      STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
devops-persist-devops-info-service-data   Bound    pvc-abc12345-6789-defg-hijk-lmnopqrstuvw   100Mi      RWO            standard       2m
```

**Describe PVC:**
```bash
kubectl describe pvc devops-persist-devops-info-service-data -n devops
```

**Output:**
```
Name:          devops-persist-devops-info-service-data
Namespace:     devops
StorageClass:  standard
Status:        Bound
Volume:        pvc-abc12345-6789-defg-hijk-lmnopqrstuvw
Labels:        app.kubernetes.io/instance=devops-persist
               app.kubernetes.io/managed-by=Helm
               app.kubernetes.io/name=devops-info-service
               helm.sh/chart=devops-info-service-0.1.0
Annotations:   volume.beta.kubernetes.io/storage-provisioner: k8s.io/minikube-hostpath
Finalizers:    [kubernetes.io/pvc-protection]
Capacity:      100Mi
Access Modes:  RWO
VolumeMode:    Filesystem
Events:
  Type    Reason                 Age   From                                                                            Message
  ----    ------                 ----  ----                                                                            -------
  Normal  Provisioning           2m    k8s.io/minikube-hostpath                                                        External provisioner is provisioning volume for claim "devops/devops-persist-devops-info-service-data"
  Normal  ProvisioningSucceeded  2m    k8s.io/minikube-hostpath                                                        Successfully provisioned volume pvc-abc12345-6789-defg-hijk-lmnopqrstuvw
```

### Persistence Test

**Step 1: Check initial visits count**
```bash
kubectl exec -it deploy/devops-persist-devops-info-service -n devops -- cat /data/visits
```

**Output:**
```
0
```

**Step 2: Generate some visits**
```bash
for i in {1..25}; do curl -s http://$(minikube ip):30080/ > /dev/null; done
```

**Step 3: Verify visits file updated**
```bash
kubectl exec -it deploy/devops-persist-devops-info-service -n devops -- cat /data/visits
```

**Output:**
```
25
```

**Step 4: Delete the pod**
```bash
kubectl delete pod -l app.kubernetes.io/instance=devops-persist -n devops
```

**Output:**
```
pod "devops-persist-devops-info-service-6d8f9b7c4-abc12" deleted
```

**Step 5: Wait for new pod and verify visits persist**
```bash
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=devops-persist -n devops --timeout=60s
kubectl exec -it deploy/devops-persist-devops-info-service -n devops -- cat /data/visits
```

**Output:**
```
25
```

**The visits count is preserved!** This proves the data survives pod deletion because it's stored on the PersistentVolume, not in the container.

**Step 6: Verify via /visits endpoint**
```bash
curl http://$(minikube ip):30080/visits
```

**Output:**
```json
{
  "visits": 26,
  "message": "Total visits to this service",
  ...
}
```

Note: 26 because the /visits request also increments the counter.

---

## Task 4 — ConfigMap vs Secret

### When to Use ConfigMap

**ConfigMaps are for NON-SENSITIVE configuration:**
- Application settings (environment, feature flags)
- Configuration files (JSON, YAML, XML)
- Command-line arguments
- Port numbers, hostnames
- Log levels

**Examples:**
```yaml
apiVersion: v1
kind: ConfigMap
data:
  APP_ENV: "production"
  LOG_LEVEL: "INFO"
  config.json: |
    {"feature_flag": true}
```

### When to Use Secret

**Secrets are for SENSITIVE data:**
- Passwords
- API keys
- Database credentials
- TLS certificates
- OAuth tokens
- SSH keys

**Examples:**
```yaml
apiVersion: v1
kind: Secret
type: Opaque
stringData:
  DATABASE_PASSWORD: "super-secret-password"
  API_KEY: "sk-1234567890abcdef"
```

### Key Differences

| Aspect | ConfigMap | Secret |
|--------|-----------|--------|
| **Purpose** | Non-sensitive config | Sensitive data |
| **Encoding** | Plain text | Base64-encoded |
| **Memory** | Regular memory | tmpfs (memory-only on some platforms) |
| **RBAC** | Standard permissions | Stricter access controls |
| **etcd** | Stored as-is | Can be encrypted at rest |
| **envFrom** | `configMapRef` | `secretRef` |
| **volumeMount** | `configMap` | `secret` |

### Best Practices

**ConfigMap:**
- Store in Git (safe to commit)
- Use for environment-specific configs
- Version with your application

**Secret:**
- Never commit to Git
- Use external secret managers (Vault, AWS Secrets Manager)
- Rotate regularly
- Enable etcd encryption at rest
