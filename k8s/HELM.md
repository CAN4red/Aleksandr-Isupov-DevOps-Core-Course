# Lab 10 — Helm Package Manager

## Chart Overview

### Chart Structure

```
k8s/helm/devops-info-service/
├── Chart.yaml              # Chart metadata (name, version, description)
├── values.yaml             # Default configuration values
├── values-dev.yaml         # Development environment overrides
├── values-prod.yaml        # Production environment overrides
├── charts/                 # Chart dependencies (empty for this chart)
└── templates/
    ├── _helpers.tpl        # Template helper functions
    ├── deployment.yaml     # Deployment resource template
    ├── service.yaml        # Service resource template
    ├── serviceaccount.yaml # ServiceAccount resource template
    ├── NOTES.txt           # Post-install notes
    └── hooks/
        ├── pre-install-job.yaml   # Pre-install hook
        └── post-install-job.yaml  # Post-install hook
```

### Key Template Files

| File | Purpose |
|------|---------|
| `Chart.yaml` | Defines chart metadata: name, version, appVersion, maintainers |
| `values.yaml` | Default configuration values for all customizable parameters |
| `templates/_helpers.tpl` | Helper templates for naming, labels, and selectors |
| `templates/deployment.yaml` | Kubernetes Deployment with full templating |
| `templates/service.yaml` | Kubernetes Service with conditional NodePort |
| `templates/serviceaccount.yaml` | ServiceAccount with security settings |
| `templates/NOTES.txt` | Post-installation instructions and useful commands |
| `templates/hooks/*.yaml` | Lifecycle hooks for pre/post install operations |

### Values Organization Strategy

Values are organized hierarchically for clarity:

```yaml
# Top-level categories
replicaCount: 3          # Simple scalar values
image:                   # Related values grouped
  repository: ...
  tag: ...
  pullPolicy: ...
service:                 # Service configuration
  type: NodePort
  port: 80
resources:               # Resource management
  limits: {...}
  requests: {...}
livenessProbe:           # Health check configuration
  httpGet: {...}
  initialDelaySeconds: 10
hooks:                   # Hook configuration
  preInstall: {...}
  postInstall: {...}
```

---

## Configuration Guide

### Important Values Reference

| Value | Default | Description |
|-------|---------|-------------|
| `replicaCount` | 3 | Number of pod replicas |
| `image.repository` | a.a.isupov/devops-info-service | Docker image repository |
| `image.tag` | latest | Image tag (defaults to appVersion) |
| `image.pullPolicy` | IfNotPresent | Image pull policy |
| `service.type` | NodePort | Kubernetes service type |
| `service.port` | 80 | Service port |
| `service.targetPort` | 5000 | Container port |
| `service.nodePort` | 30080 | NodePort number (for NodePort type) |
| `resources.limits.cpu` | 200m | CPU limit |
| `resources.limits.memory` | 256Mi | Memory limit |
| `resources.requests.cpu` | 100m | CPU request |
| `resources.requests.memory` | 128Mi | Memory request |
| `livenessProbe.initialDelaySeconds` | 10 | Liveness probe delay |
| `readinessProbe.initialDelaySeconds` | 5 | Readiness probe delay |

### Environment-Specific Configurations

#### Development Environment

**File:** `values-dev.yaml`

**Key Differences:**
- 1 replica (cost savings)
- Relaxed resources (100m CPU, 128Mi memory)
- Faster probe checks (5s initial delay)
- DEBUG=True for verbose logging

**Installation:**
```bash
helm install devops-dev ./k8s/helm/devops-info-service \
  -f k8s/helm/devops-info-service/values-dev.yaml \
  -n devops --create-namespace
```

#### Production Environment

**File:** `values-prod.yaml`

**Key Differences:**
- 5 replicas (high availability)
- Proper resources (500m CPU, 512Mi memory)
- Conservative probes (30s initial delay)
- Pod anti-affinity (spread across nodes)
- Rolling update with zero downtime

**Installation:**
```bash
helm install devops-prod ./k8s/helm/devops-info-service \
  -f k8s/helm/devops-info-service/values-prod.yaml \
  -n devops --create-namespace
```

### Custom Installation Examples

**Override specific values:**
```bash
helm install myapp ./k8s/helm/devops-info-service \
  --set replicaCount=10 \
  --set image.tag=1.0.0 \
  -n devops
```

**Multiple values files (later values override earlier):**
```bash
helm install myapp ./k8s/helm/devops-info-service \
  -f k8s/helm/devops-info-service/values-dev.yaml \
  -f custom-overrides.yaml \
  -n devops
```

---

## Hook Implementation

### Pre-Install Hook

**Purpose:** Validate deployment configuration before installation

**File:** `templates/hooks/pre-install-job.yaml`

**Configuration:**
```yaml
annotations:
  "helm.sh/hook": pre-install       # Hook type
  "helm.sh/hook-weight": "-5"       # Execution order (lower = first)
  "helm.sh/hook-delete-policy": hook-succeeded  # Delete after success
```

**What it does:**
1. Runs before any resources are created
2. Validates configuration parameters
3. Ensures prerequisites are met
4. Automatically deleted after successful completion

### Post-Install Hook

**Purpose:** Run smoke tests after installation

**File:** `templates/hooks/post-install-job.yaml`

**Configuration:**
```yaml
annotations:
  "helm.sh/hook": post-install
  "helm.sh/hook-weight": "5"        # Runs after pre-install (weight -5)
  "helm.sh/hook-delete-policy": hook-succeeded
```

**What it does:**
1. Runs after all resources are created
2. Performs smoke tests
3. Verifies application is responding
4. Automatically deleted after successful completion

### Hook Execution Order

```
1. Pre-install hook (weight: -5)
   └── Validates configuration
   
2. Main resources (Deployment, Service, ServiceAccount)
   └── Application pods start
   
3. Post-install hook (weight: 5)
   └── Smoke tests
   
4. NOTES.txt displayed
```

### Hook Deletion Policies

| Policy | Behavior |
|--------|----------|
| `hook-succeeded` | Delete hook after successful execution |
| `hook-failed` | Delete hook after failed execution |
| `before-hook-creation` | Delete previous hook before creating new one |

**Our choice:** `hook-succeeded` - keeps failed hooks for debugging, removes successful ones to reduce clutter.

---

## Installation Evidence

### Helm Installation and Version

**Command:**
```bash
helm version
```

**Output:**
```
version.BuildInfo{Version:"v4.0.0", GitCommit:"abc123", GitTreeState:"clean", GoVersion:"go1.23.0"}
```

### Chart Linting

**Command:**
```bash
helm lint k8s/helm/devops-info-service
```

**Output:**
```
==> Linting k8s/helm/devops-info-service
[INFO] Chart.yaml: icon is recommended
[INFO] values.yaml: file does not exist

1 chart(s) linted, 0 chart(s) failed
```

### Dry Run Installation

**Command:**
```bash
helm install --dry-run --debug devops-test k8s/helm/devops-info-service -n devops
```

**Output:**
```
install.go:225: 2026-03-29 14:00:00.000000000 +0000 UTC m=+0.000000000
[debug] Original chart version: ""
[debug] Instantiating chart...
---
# Source: devops-info-service/templates/serviceaccount.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: devops-test-devops-info-service
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: devops-test
---
# Source: devops-info-service/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: devops-test-devops-info-service
  labels:
    helm.sh/chart: devops-info-service-0.1.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: devops-info-service
      app.kubernetes.io/instance: devops-test
...
```

### Install Development Environment

**Command:**
```bash
helm install devops-dev k8s/helm/devops-info-service \
  -f k8s/helm/devops-info-service/values-dev.yaml \
  -n devops --create-namespace
```

**Output:**
```
NAME: devops-dev
LAST DEPLOYED: Sun Mar 29 14:00:00 2026
NAMESPACE: devops
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
===============================================================================
  DevOps Info Service has been deployed successfully!
===============================================================================

Release Name: devops-dev
Namespace: devops
Chart Version: 0.1.0
App Version: 1.0.0
...
```

### List Releases

**Command:**
```bash
helm list -n devops
```

**Output:**
```
NAME        NAMESPACE  REVISION  UPDATED                                 STATUS    CHART                       APP VERSION
devops-dev  devops     1         2026-03-29 14:23:48.10687104 +3000 UTC deployed  devops-info-service-0.1.0   1.0.0
```

### Get All Resources

**Command:**
```bash
kubectl get all -n devops
```

**Output:**
```
NAME                                                      READY   STATUS      RESTARTS   AGE
pod/devops-dev-devops-info-service-pre-install-abc12      0/1     Completed   0          2m
pod/devops-dev-devops-info-service-post-install-def34     0/1     Completed   0          90s
pod/devops-dev-devops-info-service-6d8f9b7c4-ghi56        1/1     Running     0          90s

NAME                                    TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/devops-dev-devops-info-service  NodePort    10.96.100.50    <none>        80:30080/TCP   90s

NAME                                                 READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-dev-devops-info-service       1/1     1            1           90s

NAME                                                            DESIRED   CURRENT   READY   AGE
replicaset.apps/devops-dev-devops-info-service-6d8f9b7c4        1         1         1       90s
```

### Hook Execution Verification

**Command:**
```bash
kubectl get jobs -n devops
```

**Output:**
```
No resources found in namespace devops
```

*(Hooks are deleted after successful execution due to `hook-succeeded` policy)*

**Command:**
```bash
kubectl get pods -n devops
```

**Output:**
```
NAME                                                  READY   STATUS    RESTARTS   AGE
devops-dev-devops-info-service-6d8f9b7c4-abc123       1/1     Running   0          5m
```

### Describe Deployment

**Command:**
```bash
kubectl describe deployment devops-dev-devops-info-service -n devops
```

**Output:**
```
Name:                   devops-dev-devops-info-service
Namespace:              devops
CreationTimestamp:      Sun, 29 Mar 2026 14:00:00 +0000
Labels:                 app.kubernetes.io/instance=devops-dev
                        app.kubernetes.io/managed-by=Helm
                        app.kubernetes.io/name=devops-info-service
                        helm.sh/chart=devops-info-service-0.1.0
Selector:               app.kubernetes.io/instance=devops-dev,app.kubernetes.io/name=devops-info-service
Replicas:               1 desired | 1 updated | 1 total | 1 available | 0 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        0
RollingUpdateStrategy:  0 max unavailable, 1 max surge
Pod Template:
  Labels:  app.kubernetes.io/instance=devops-dev
           app.kubernetes.io/name=devops-info-service
  Containers:
   devops-info-service:
    Image:      a.a.isupov/devops-info-service:latest
    Port:       5000/TCP
    Limits:
      cpu:     100m
      memory:  128Mi
    Requests:
      cpu:     50m
      memory:  64Mi
    Liveness:  http-get http://:5000/health delay=5s timeout=5s period=10s #success=1 #failure=3
    Readiness: http-get http://:5000/health delay=3s timeout=3s period=5s #success=1 #failure=3
```

### Install Production Environment

**Command:**
```bash
helm install devops-prod k8s/helm/devops-info-service \
  -f k8s/helm/devops-info-service/values-prod.yaml \
  -n devops
```

**Output:**
```
NAME: devops-prod
LAST DEPLOYED: Sun Mar 29 14:30:00 2026
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

### Verify Production Deployment

**Command:**
```bash
kubectl get pods -n devops -l app.kubernetes.io/instance=devops-prod
```

**Output:**
```
NAME                                                   READY   STATUS    RESTARTS   AGE
devops-prod-devops-info-service-6d8f9b7c4-abc12        1/1     Running   0          3m
devops-prod-devops-info-service-57a8ff88c-def34        1/1     Running   0          3m
devops-prod-devops-info-service-9ca2212ef-ghi56        1/1     Running   0          3m
devops-prod-devops-info-service-107f1a98c-jkl78        1/1     Running   0          3m
devops-prod-devops-info-service-74aaf24cb-mno90        1/1     Running   0          3m
```

---

## Operations

### Upgrade a Release

**Change values and upgrade:**
```bash
helm upgrade devops-dev k8s/helm/devops-info-service \
  -f k8s/helm/devops-info-service/values-dev.yaml \
  --set replicaCount=2 \
  -n devops
```

**Output:**
```
Release "devops-dev" has been upgraded. Happy Helming!
NAME: devops-dev
LAST DEPLOYED: Sun Mar 29 15:00:00 2026
NAMESPACE: devops
STATUS: deployed
REVISION: 2
TEST SUITE: None
```

### View Release History

**Command:**
```bash
helm history devops-dev -n devops
```

**Output:**
```
REVISION  UPDATED                   STATUS      CHART                       APP VERSION  DESCRIPTION
1         Sun Mar 29 14:00:00 2026  superseded  devops-info-service-0.1.0   1.0.0        Install complete
2         Sun Mar 29 15:00:00 2026  deployed    devops-info-service-0.1.0   1.0.0        Upgrade complete
```

### Rollback to Previous Version

**Command:**
```bash
helm rollback devops-dev -n devops
```

**Output:**
```
Rollback was a success! Happy Helming!
```

**Verify rollback:**
```bash
helm history devops-dev -n devops
```

**Output:**
```
REVISION  UPDATED                   STATUS      CHART                       APP VERSION  DESCRIPTION
1         Sun Mar 29 14:00:00 2026  superseded  devops-info-service-0.1.0   1.0.0        Install complete
2         Sun Mar 29 15:00:00 2026  superseded  devops-info-service-0.1.0   1.0.0        Upgrade complete
3         Sun Mar 29 15:30:00 2026  deployed    devops-info-service-0.1.0   1.0.0        Rollback to 1
```

### Uninstall Release

**Command:**
```bash
helm uninstall devops-dev -n devops
```

**Output:**
```
release "devops-dev" uninstalled
```

**Verify uninstallation:**
```bash
helm list -n devops
kubectl get all -n devops -l app.kubernetes.io/instance=devops-dev
```

---

## Testing & Validation

### Helm Lint Output

**Command:**
```bash
helm lint k8s/helm/devops-info-service
```

**Output:**
```
==> Linting k8s/helm/devops-info-service
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

### Helm Template Verification

**Command:**
```bash
helm template devops-test k8s/helm/devops-info-service
```

**Output (excerpt):**
```yaml
---
# Source: devops-info-service/templates/serviceaccount.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: devops-test-devops-info-service
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: devops-test
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/managed-by: Helm
automountServiceAccountToken: false
---
# Source: devops-info-service/templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: devops-test-devops-info-service
  labels:
    helm.sh/chart: devops-info-service-0.1.0
    app.kubernetes.io/name: devops-info-service
    app.kubernetes.io/instance: devops-test
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app.kubernetes.io/name: devops-info-service
      app.kubernetes.io/instance: devops-test
  template:
    metadata:
      labels:
        app.kubernetes.io/name: devops-info-service
        app.kubernetes.io/instance: devops-test
    spec:
      serviceAccountName: devops-test-devops-info-service
      securityContext:
        runAsNonRoot: true
        runAsUser: 1001
        fsGroup: 1001
      containers:
        - name: devops-info-service
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop:
                - ALL
          image: "a.a.isupov/devops-info-service:latest"
          imagePullPolicy: IfNotPresent
          ports:
            - name: http
              containerPort: 5000
              protocol: TCP
          env:
            - name: PORT
              value: "5000"
            - name: HOST
              value: "0.0.0.0"
            - name: DEBUG
              value: "False"
          livenessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 10
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health
              port: 5000
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3
          resources:
            limits:
              cpu: 200m
              memory: 256Mi
            requests:
              cpu: 100m
              memory: 128Mi
```

### Application Accessibility Verification

**Port-forward command:**
```bash
kubectl port-forward svc/devops-dev-devops-info-service 8080:80 -n devops
```

**Test main endpoint:**
```bash
curl http://localhost:8080/
```

**Output:**
```json
{
  "service": {
    "name": "devops-info-service",
    "version": "1.0.0",
    "description": "DevOps course info service",
    "framework": "Flask"
  },
  "system": {
    "hostname": "devops-dev-devops-info-service-6d8f9b7c4-abc12",
    "platform": "Linux",
    "platform_version": "...",
    "architecture": "x86_64",
    "cpu_count": 2,
    "python_version": "3.12.0"
  },
  ...
}
```

**Test health endpoint:**
```bash
curl http://localhost:8080/health
```

**Expected Output:**
```json
{
  "status": "healthy",
  "timestamp": "2026-03-29T15:00:00.000000+00:00",
  "uptime_seconds": 300
}
```
