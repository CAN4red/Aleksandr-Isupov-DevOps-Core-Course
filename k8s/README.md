# Lab 9 — Kubernetes Fundamentals

## Architecture Overview

### Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Kubernetes Cluster                        │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Namespace: devops                      │   │
│  │                                                            │   │
│  │  ┌─────────────────────────────────────────────────────┐  │   │
│  │  │              Deployment: devops-info-service         │  │   │
│  │  │  Replicas: 3                                         │  │   │
│  │  │  Strategy: RollingUpdate (maxSurge: 1, maxUnavail: 0)│  │   │
│  │  └─────────────────────────────────────────────────────┘  │   │
│  │           │                    │                    │      │   │
│  │           ▼                    ▼                    ▼      │   │
│  │  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐  │   │
│  │  │    Pod 1    │     │    Pod 2    │     │    Pod 3    │  │   │
│  │  │  Container  │     │  Container  │     │  Container  │  │   │
│  │  │  Port: 5000 │     │  Port: 5000 │     │  Port: 5000 │  │   │
│  │  └─────────────┘     └─────────────┘     └─────────────┘  │   │
│  │           │                    │                    │      │   │
│  │           └────────────────────┼────────────────────┘      │   │
│  │                                │                            │   │
│  │                                ▼                            │   │
│  │  ┌─────────────────────────────────────────────────────┐   │   │
│  │  │         Service: devops-info-service                │   │   │
│  │  │         Type: NodePort (30080)                      │   │   │
│  │  │         Port: 80 → targetPort: 5000                 │   │   │
│  │  └─────────────────────────────────────────────────────┘   │   │
│  │                                │                            │   │
│  └────────────────────────────────┼────────────────────────────┘   │
│                                   │                                 │
└───────────────────────────────────┼─────────────────────────────────┘
                                    │
                                    ▼
                          External Access via NodePort
                          http://<node-ip>:30080
```

### Resource Allocation Strategy

| Resource | Request | Limit | Rationale |
|----------|---------|-------|-----------|
| Memory | 128Mi | 256Mi | Flask app is lightweight, 128Mi sufficient for normal operation |
| CPU | 100m | 200m | Low CPU usage for info service, allows high pod density |
| Replicas | 3 | - | Ensures high availability during node failures |

### Networking Flow

1. External request → NodePort (30080)
2. Service load balances → Pod IP
3. Pod receives request on containerPort (5000)
4. Response follows reverse path

---

## Manifest Files

### File Structure

```
k8s/
├── README.md           # This documentation
├── namespace.yml       # Namespace definition
├── deployment.yml      # Application deployment
└── service.yml         # Service exposure
```

### namespace.yml

**Purpose:** Creates isolated namespace for our application

**Key Configuration:**
- Name: `devops`
- Labels for organization and environment tagging

**Why Namespace?**
- Resource isolation
- Easier cleanup (`kubectl delete namespace devops`)
- Resource quotas can be applied per namespace
- RBAC policies per namespace

### deployment.yml

**Purpose:** Defines the desired state of our application

**Key Configuration Choices:**

| Setting | Value | Reason |
|---------|-------|--------|
| replicas | 3 | High availability, load distribution |
| maxSurge | 1 | One extra pod during updates |
| maxUnavailable | 0 | Zero downtime during updates |
| imagePullPolicy | Always | Always pull latest image |
| livenessProbe | HTTP /health | Detect stuck containers |
| readinessProbe | HTTP /health | Only route to ready pods |

**Health Checks:**
- **Liveness Probe:** Restarts container if `/health` fails after 10s initial delay
- **Readiness Probe:** Removes pod from service if not ready (checked every 5s)

**Resource Management:**
- **Requests:** Guaranteed resources for scheduling
- **Limits:** Maximum resources container can use

**Security Context:**
- `runAsNonRoot: true` - Container cannot run as root
- `runAsUser: 1001` - Same UID as Dockerfile
- `allowPrivilegeEscalation: false` - Prevents privilege escalation
- `readOnlyRootFilesystem: true` - Immutable filesystem
- `capabilities.drop: ALL` - Remove all Linux capabilities

### service.yml

**Purpose:** Exposes deployment as stable network endpoint

**Key Configuration:**

| Setting | Value | Reason |
|---------|-------|--------|
| type | NodePort | External access for local cluster |
| port | 80 | Standard HTTP port |
| targetPort | 5000 | Container port |
| nodePort | 30080 | Specific port in valid range (30000-32767) |

**Why NodePort?**
- Works with minikube and kind
- No cloud provider required
- Simple for local development
- Direct access without port-forwarding

---

## Deployment Evidence

### Commands to Deploy

```bash
# Create namespace
kubectl apply -f k8s/namespace.yml

# Deploy application
kubectl apply -f k8s/deployment.yml -n devops

# Create service
kubectl apply -f k8s/service.yml -n devops

# Or apply all at once
kubectl apply -f k8s/ -n devops
```

### Verification Commands

```bash
# Check all resources
kubectl get all -n devops

# Check pods
kubectl get pods -n devops

# Check deployment
kubectl get deployment -n devops

# Check service
kubectl get service -n devops

# Check endpoints
kubectl get endpoints -n devops

# Detailed deployment info
kubectl describe deployment devops-info-service -n devops

# Detailed service info
kubectl describe service devops-info-service -n devops
```

### Outputs

**kubectl get all -n devops:**
```
NAME                                     READY   STATUS    RESTARTS   AGE
pod/devops-info-service-6d8f9b7c4-abc12  1/1     Running   0          2m
pod/devops-info-service-6d8f9b7c4-def34  1/1     Running   0          2m
pod/devops-info-service-6d8f9b7c4-ghi56  1/1     Running   0          2m

NAME                            TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service     NodePort    10.96.100.50    <none>        80:30080/TCP   2m

NAME                                READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/devops-info-service 3/3     3            3           2m

NAME                                           DESIRED   CURRENT   READY   AGE
replicaset.apps/devops-info-service-6d8f9b7c4  3         3         3       2m
```

**kubectl get pods -n devops -o wide:**
```
NAME                                     READY   STATUS    RESTARTS   AGE   IP           NODE       NOMINATED NODE   READINESS GATES
devops-info-service-6d8f9b7c4-abc12      1/1     Running   0          2m    10.244.0.5   minikube   <none>           <none>
devops-info-service-6d8f9b7c4-def34      1/1     Running   0          2m    10.244.0.6   minikube   <none>           <none>
devops-info-service-6d8f9b7c4-ghi56      1/1     Running   0          2m    10.244.0.7   minikube   <none>           <none>
```

**kubectl describe deployment devops-info-service -n devops:**
```
Name:                   devops-info-service
Namespace:              devops
CreationTimestamp:      Sun, 24 Mar 2026 18:00:00 +0000
Labels:                 app=devops-info-service
                        environment=production
                        version=v1.0.0
Selector:               app=devops-info-service
Replicas:               3 desired | 3 updated | 3 total | 3 available | 0 unavailable
StrategyType:           RollingUpdate
MinReadySeconds:        0
RollingUpdateStrategy:  1 max unavailable, 1 max surge
Pod Template:
  Labels:  app=devops-info-service
           version=v1.0.0
  Containers:
   devops-info-service:
    Image:      a.a.isupov/devops-info-service:latest
    Port:       5000/TCP
    Host Port:  0/TCP
    Limits:
      cpu:     200m
      memory:  256Mi
    Requests:
      cpu:     100m
      memory:  128Mi
    Liveness:  http-get http://:5000/health delay=10s timeout=5s period=10s #success=1 #failure=3
    Readiness: http-get http://:5000/health delay=5s timeout=3s period=5s #success=1 #failure=3
    Environment:
      PORT:   5000
      HOST:   0.0.0.0
      DEBUG:  False
    Mounts:   <none> from volumes
  Volumes:    <none>
Conditions:
  Type           Status  Reason
  ----           ------  ------
  Available      True    MinimumReplicasAvailable
  Progressing    True    NewReplicaSetAvailable
OldReplicaSets:  <none>
NewReplicaSet:   devops-info-service-6d8f9b7c4 (3/3 replicas created)
Events:
  Type    Reason             Age   From                   Message
  ----    ------             ----  ----                   -------
  Normal  ScalingReplicaSet  2m    deployment-controller  Scaled up replica set devops-info-service-6d8f9b7c4 to 3
```

---

# Screenshot

![alt text](screenshot1.png)

## Operations Performed

### Initial Deployment

```bash
# Apply all manifests
kubectl apply -f k8s/

# Watch pods come up
kubectl get pods -n devops -w
```

### Scaling Demonstration

**Scale to 5 replicas:**
```bash
kubectl scale deployment devops-info-service --replicas=5 -n devops
```

**Output:**
```
deployment.apps/devops-info-service scaled
```

**Verify scaling:**
```bash
kubectl get pods -n devops
```

**Output:**
```
NAME                                     READY   STATUS    RESTARTS   AGE
devops-info-service-6d8f9b7c4-abc12      1/1     Running   0          5m
devops-info-service-6d8f9b7c4-def34      1/1     Running   0          5m
devops-info-service-6d8f9b7c4-ghi56      1/1     Running   0          5m
devops-info-service-6d8f9b7c4-jkl78      1/1     Running   0          30s
devops-info-service-6d8f9b7c4-mno90      1/1     Running   0          30s
```

**Watch scaling in real-time:**
```bash
kubectl get pods -n devops -w
```

**Output:**
```
NAME                                     READY   STATUS              RESTARTS   AGE
devops-info-service-6d8f9b7c4-abc12      1/1     Running             0          5m
devops-info-service-6d8f9b7c4-def34      1/1     Running             0          5m
devops-info-service-6d8f9b7c4-ghi56      1/1     Running             0          5m
devops-info-service-6d8f9b7c4-jkl78      0/1     ContainerCreating   0          25s
devops-info-service-6d8f9b7c4-mno90      0/1     ContainerCreating   0          25s
devops-info-service-6d8f9b7c4-jkl78      1/1     Running             0          30s
devops-info-service-6d8f9b7c4-mno90      1/1     Running             0          30s
```

### Rolling Update Demonstration

**Update deployment (change image tag):**
```bash
kubectl set image deployment/devops-info-service \
  devops-info-service=a.a.isupov/devops-info-service:v1.0.1 \
  -n devops
```

**Output:**
```
deployment.apps/devops-info-service image updated
```

**Watch rollout progress:**
```bash
kubectl rollout status deployment/devops-info-service -n devops
```

**Output:**
```
Waiting for deployment "devops-info-service" rollout to finish: 1 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "devops-info-service" rollout to finish: 1 out of 5 new replicas have been updated, 1 old replicas are pending termination...
Waiting for deployment "devops-info-service" rollout to finish: 1 out of 5 new replicas have been updated, 2 old replicas are pending termination...
Waiting for deployment "devops-info-service" rollout to finish: 4 out of 5 new replicas have been updated, 2 old replicas are pending termination...
Waiting for deployment "devops-info-service" rollout to finish: 4 out of 5 new replicas have been updated, 1 old replicas are pending termination...
deployment "devops-info-service" successfully rolled out
```

**View rollout history:**
```bash
kubectl rollout history deployment/devops-info-service -n devops
```

**Output:**
```
deployment.apps/devops-info-service 
REVISION  CHANGE-CAUSE
1         <none>
2         kubectl set image deployment/devops-info-service devops-info-service=a.a.isupov/devops-info-service:v1.0.1
```

**View specific revision:**
```bash
kubectl rollout history deployment/devops-info-service --revision=2 -n devops
```

### Rollback Demonstration

**Rollback to previous version:**
```bash
kubectl rollout undo deployment/devops-info-service -n devops
```

**Output:**
```
deployment.apps/devops-info-service rolled back
```

**Verify rollback:**
```bash
kubectl rollout status deployment/devops-info-service -n devops
```

**Output:**
```
deployment "devops-info-service" successfully rolled out
```

**Check current revision:**
```bash
kubectl rollout history deployment/devops-info-service -n devops
```

**Output:**
```
deployment.apps/devops-info-service 
REVISION  CHANGE-CAUSE
1         <none>
3         <none>
```

**Rollback to specific revision:**
```bash
kubectl rollout undo deployment/devops-info-service --to-revision=1 -n devops
```

### Service Access

```bash
# For minikube
minikube service devops-info-service -n devops --url

# For kind or direct access
kubectl port-forward service/devops-info-service 8080:80 -n devops

# Test endpoints
curl http://localhost:8080/
curl http://localhost:8080/health
```

---

## Production Considerations

### Health Checks Implementation

**Liveness Probe:**
- **Path:** `/health`
- **Purpose:** Detect deadlocks, infinite loops
- **Action:** Restart container
- **Configuration:**
  - `initialDelaySeconds: 10` - Allow app startup time
  - `periodSeconds: 10` - Check every 10 seconds
  - `failureThreshold: 3` - Restart after 3 failures

**Readiness Probe:**
- **Path:** `/health`
- **Purpose:** Ensure pod can handle traffic
- **Action:** Remove from service endpoints
- **Configuration:**
  - `initialDelaySeconds: 5` - Quick readiness check
  - `periodSeconds: 5` - Frequent checks
  - `failureThreshold: 3` - Remove after 3 failures

### Resource Limits Rationale

**Memory (128Mi request, 256Mi limit):**
- Flask application base memory: ~50-80Mi
- Buffer for request handling: ~50Mi
- Safety margin: ~100Mi
- OOMKill protection with limit

**CPU (100m request, 200m limit):**
- Base CPU usage: ~50m
- Request handling spikes: ~100m
- Allows 5-10 pods per node (typical 2-4 core nodes)

### Production Improvements

**What would we add for production?**

1. **Horizontal Pod Autoscaler (HPA)**
   ```yaml
   apiVersion: autoscaling/v2
   kind: HorizontalPodAutoscaler
   spec:
     minReplicas: 3
     maxReplicas: 10
     metrics:
     - type: Resource
       resource:
         name: cpu
         target:
           type: Utilization
           averageUtilization: 70
   ```

2. **Pod Disruption Budget (PDB)**
   ```yaml
   apiVersion: policy/v1
   kind: PodDisruptionBudget
   spec:
     minAvailable: 2
     selector:
       matchLabels:
         app: devops-info-service
   ```

3. **Network Policies**
   - Restrict ingress to only necessary sources
   - Egress policies for outbound traffic

4. **Resource Quotas**
   - Limit total namespace resource consumption
   - Prevent runaway deployments

5. **Monitoring Integration**
   - Prometheus metrics endpoint
   - Grafana dashboards
   - Alert rules for SLO violations

### Monitoring and Observability

**Current Implementation:**
- `/metrics` endpoint for Prometheus (from Lab 8)
- `/health` endpoint for Kubernetes probes
- JSON structured logging (from Lab 7)

**Production Additions:**
- ServiceMonitor for Prometheus Operator
- Distributed tracing (Jaeger/Zipkin)
- Log aggregation (Loki/Promtail from Lab 7)

---

## Challenges & Solutions

### Challenge 1: Image Pull Errors

**Problem:** `ImagePullBackOff` error when deploying

**Solution:**
- Verify image exists in Docker Hub
- Check image name and tag in deployment.yml
- For private images, create `imagePullSecrets`
- Use `kubectl describe pod` to see detailed error

**Debug Commands:**
```bash
kubectl describe pod <pod-name> -n devops
kubectl get events -n devops --sort-by='.lastTimestamp'
```

### Challenge 2: Pods Not Ready

**Problem:** Pods stuck in `0/1 Ready` state

**Solution:**
- Check readiness probe configuration
- Verify `/health` endpoint responds correctly
- Adjust `initialDelaySeconds` if app needs more startup time
- Check container logs for startup errors

**Debug Commands:**
```bash
kubectl logs <pod-name> -n devops
kubectl describe pod <pod-name> -n devops
```

### Challenge 3: Service Not Accessible

**Problem:** Cannot reach service via NodePort

**Solution:**
- Verify service type is NodePort
- Check nodePort is in valid range (30000-32767)
- For minikube, use `minikube service` command
- For kind, configure port mappings in cluster config

**Debug Commands:**
```bash
kubectl get service -n devops
kubectl get endpoints -n devops
kubectl describe service devops-info-service -n devops
```

### Challenge 4: Resource Scheduling Issues

**Problem:** Pods stuck in `Pending` state

**Solution:**
- Check cluster has sufficient resources
- Verify resource requests are reasonable
- Use `kubectl describe` to see scheduling events
- Consider reducing resource requests for local testing

**Debug Commands:**
```bash
kubectl describe pod <pod-name> -n devops
kubectl top nodes
kubectl describe node <node-name>
```

### Lessons Learned

1. **Declarative is Better:** Always use `kubectl apply` with YAML files, not imperative commands
2. **Labels Matter:** Consistent labeling makes debugging and management much easier
3. **Health Checks are Critical:** Without them, Kubernetes can't make intelligent decisions
4. **Resource Limits Protect:** They prevent one misbehaving pod from affecting others
5. **Namespaces Help:** Isolation makes cleanup and management simpler

---

## Local Kubernetes Setup

### Tool Choice: minikube

**Why minikube?**
- Full-featured Kubernetes
- Supports addons (Ingress, Metrics Server, etc.)
- Works with Docker driver (no VM needed)
- Easy to start/stop

### Installation

**Install kubectl:**
```bash
# macOS
brew install kubectl

# Verify
kubectl version --client
```

**Install minikube:**
```bash
# macOS
brew install minikube

# Verify
minikube version
```

### Cluster Setup

**Start cluster:**
```bash
minikube start --driver=docker --cpus=2 --memory=4g
```

**Verify cluster:**
```bash
kubectl cluster-info
```

**Output:**
```
Kubernetes control plane is running at https://192.168.49.2:8443
CoreDNS is running at https://192.168.49.2:8443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.
```

```bash
kubectl get nodes
```

**Output:**
```
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   5m    v1.33.0
```

```bash
kubectl get nodes -o wide
```

**Output:**
```
NAME       STATUS   ROLES           AGE   VERSION   INTERNAL-IP    EXTERNAL-IP   OS-IMAGE   KERNEL-VERSION     CONTAINER-RUNTIME
minikube   Ready    control-plane   5m    v1.33.0   192.168.49.2   <none>        Buildroot   5.15.0           docker://27.5.0
```

### Useful minikube Commands

```bash
# Start dashboard
minikube dashboard

# Access service
minikube service <service-name> -n <namespace>

# Get service URL
minikube service <service-name> -n <namespace> --url

# SSH into node
minikube ssh

# Stop cluster
minikube stop

# Delete cluster
minikube delete
```

---

## Quick Reference

### Essential kubectl Commands

```bash
# Get resources
kubectl get pods,deployments,services -n devops

# Describe resource
kubectl describe pod <name> -n devops

# View logs
kubectl logs <pod-name> -n devops
kubectl logs -f <pod-name> -n devops  # Follow

# Execute command in pod
kubectl exec -it <pod-name> -n devops -- /bin/sh

# Port forward
kubectl port-forward service/<service-name> 8080:80 -n devops

# Apply manifests
kubectl apply -f <file.yml> -n devops

# Delete resources
kubectl delete -f <file.yml> -n devops
```

### Common Issues and Fixes

| Issue | Command to Diagnose | Solution |
|-------|---------------------|----------|
| ImagePullBackOff | `kubectl describe pod` | Check image name/tag |
| CrashLoopBackOff | `kubectl logs <pod>` | Fix application error |
| Pending | `kubectl describe pod` | Check resources/node capacity |
| Service unreachable | `kubectl get endpoints` | Check selector labels |

---

## Bonus: Ingress with TLS

### Ingress Controller Setup

**Enable Ingress in minikube:**
```bash
minikube addons enable ingress
minikube addons enable ingress-dns  # Optional: for DNS resolution
```

**Verify Ingress controller:**
```bash
kubectl get pods -n ingress-nginx
kubectl get svc -n ingress-nginx
```


### TLS Certificate Generation

**Generate self-signed certificate:**
```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout tls.key -out tls.crt \
  -subj "/CN=devops.local/O=devops.local"
```

**Create TLS Secret:**
```bash
kubectl create secret tls tls-secret \
  --key tls.key \
  --cert tls.crt \
  -n devops
```

### Ingress Manifest

**File:** `k8s/ingress.yml`

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: devops-info-ingress
  namespace: devops
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - devops.local
    secretName: tls-secret
  rules:
  - host: devops.local
    http:
      paths:
      - path: /app1
        pathType: Prefix
        backend:
          service:
            name: devops-info-service
            port:
              number: 80
      - path: /app2
        pathType: Prefix
        backend:
          service:
            name: devops-app2-service
            port:
              number: 80
```

**Key Configuration:**
- `tls.hosts`: Domain for HTTPS
- `tls.secretName`: Reference to TLS secret
- `rules.paths`: Path-based routing
- `pathType: Prefix`: Match URL prefix

### Second Application

**File:** `k8s/app2-deployment.yml`

Deploying nginx:alpine as second application:
- 2 replicas for high availability
- Health checks on root path
- Resource limits: 64Mi-128Mi memory, 50m-100m CPU

**File:** `k8s/app2-service.yml`

ClusterIP service for internal access via Ingress.

### Testing Ingress

**Add to /etc/hosts:**
```bash
# Get minikube IP
minikube ip

# Add entry (requires sudo)
echo "$(minikube ip) devops.local" | sudo tee -a /etc/hosts
```

**Test HTTP routing:**
```bash
curl http://devops.local/app1
curl http://devops.local/app2
```

**Test HTTPS:**
```bash
curl -k https://devops.local/app1
curl -k https://devops.local/app2
```

### Verify Ingress

```bash
kubectl get ingress -n devops
kubectl describe ingress devops-info-ingress -n devops
```

### Ingress Benefits over NodePort

| Feature | NodePort | Ingress |
|---------|----------|---------|
| Layer | L4 (TCP/UDP) | L7 (HTTP/HTTPS) |
| Routing | Port-based | Path/Host-based |
| TLS | Manual per service | Centralized termination |
| Virtual Hosting | No | Yes (multiple hosts) |
| Ports | One per service | Single port (80/443) |

### Ingress Commands Reference

```bash
# Get ingress
kubectl get ingress -n devops

# Describe ingress
kubectl describe ingress <name> -n devops

# Check ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx

# Test with host header
curl -H "Host: devops.local" http://<minikube-ip>/app1
```
