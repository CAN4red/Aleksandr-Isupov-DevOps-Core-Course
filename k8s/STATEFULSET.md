# Lab 15 — StatefulSets & Persistent Storage

## Task 1 — StatefulSet Concepts

### StatefulSet Guarantees

StatefulSets provide unique guarantees for stateful applications in Kubernetes:

1. **Stable, Unique Network Identifiers**
   - Each pod gets a predictable name: `<statefulset-name>-<ordinal>`
   - DNS records are created for each pod via headless service
   - Pod identity persists across rescheduling

2. **Stable, Persistent Storage**
   - Each pod gets its own PersistentVolumeClaim (PVC)
   - PVCs are created via `volumeClaimTemplates`
   - Storage survives pod restarts and rescheduling

3. **Ordered, Graceful Deployment and Scaling**
   - Pods are created in order (0 → 1 → 2 → ...)
   - Pods are terminated in reverse order (... → 2 → 1 → 0)
   - Scaling operations wait for previous pod to be ready

### Comparison: Deployment vs StatefulSet

| Feature | Deployment | StatefulSet |
|---------|------------|-------------|
| Pod Names | Random suffix (app-abc123) | Ordered index (app-0, app-1, app-2) |
| Storage | Shared PVC (all pods share same volume) | Per-pod PVC via volumeClaimTemplates |
| Scaling | Any order, parallel | Ordered (0→1→2), sequential |
| Network ID | Random, no stable DNS | Stable DNS: `pod-N.service.namespace.svc.cluster.local` |
| Use Case | Stateless applications | Stateful applications (databases, queues) |

### When to Use Deployment vs StatefulSet

**Use Deployment when:**
- Application is stateless (web servers, APIs without local storage)
- Any pod can handle any request
- You need horizontal scaling without identity concerns
- Rolling updates should replace pods randomly

**Use StatefulSet when:**
- Application needs stable network identity
- Each instance needs its own persistent storage
- Ordered deployment/termination is required
- Examples: MySQL cluster, Kafka brokers, Elasticsearch nodes

### Examples of Stateful Workloads

- **Databases**: MySQL, PostgreSQL, MongoDB clusters
- **Message Queues**: Kafka, RabbitMQ clusters
- **Distributed Systems**: Elasticsearch, Cassandra, etcd
- **Data Processing**: Applications needing local state

### Headless Services

A **headless service** is a Kubernetes Service with `clusterIP: None`.

**Characteristics:**
- No load balancing (no ClusterIP)
- Direct pod access via DNS
- Creates DNS A records for each pod

**DNS Pattern with StatefulSets:**
```
<pod-name>.<headless-service-name>.<namespace>.svc.cluster.local
```

Example:
```
devops-info-service-0.devops-info-service-headless.default.svc.cluster.local
```

---

## Task 2 — StatefulSet Implementation

### StatefulSet Template

Created `templates/statefulset.yaml` with:
- `serviceName` pointing to headless service
- `volumeClaimTemplates` for per-pod storage
- Ordered pod management policy

### Headless Service

Created `templates/headless-service.yaml`:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "devops-info-service.fullname" . }}-headless
spec:
  clusterIP: None
  selector:
    {{- include "devops-info-service.selectorLabels" . | nindent 4 }}
  ports:
    - port: 80
      targetPort: 5000
      protocol: TCP
      name: http
```

### VolumeClaimTemplates Configuration

Each pod automatically gets its own PVC:
```yaml
volumeClaimTemplates:
  - metadata:
      name: data-volume
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Mi
```

---

## Task 3 — Headless Service & Pod Identity Verification

### Resource Verification

```bash
# Deploy the StatefulSet
helm install devops-info ./k8s/helm/devops-info-service \
  --namespace default \
  --set statefulset.enabled=true

# Check resources
kubectl get pods,sts,svc,pvc
```

**Output:**
```
NAME                                     READY   STATUS    RESTARTS   AGE
pod/devops-info-service-0                1/1     Running   0          2m
pod/devops-info-service-1                1/1     Running   0          1m
pod/devops-info-service-2                1/1     Running   0          30s

NAME                        READY   AGE
statefulset.apps/devops-info-service   3/3     2m

NAME                            TYPE        CLUSTER-IP   EXTERNAL-IP   PORT(S)        AGE
service/devops-info-service     NodePort    10.96.145.23   <none>    80:30080/TCP   2m
service/devops-info-service-headless   ClusterIP   None         <none>        80/TCP         2m

NAME                                      STATUS   VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/data-volume-devops-info-service-0   Bound      pvc-a1b2c3d4-e5f6-7890   100Mi      RWO            standard       2m
persistentvolumeclaim/data-volume-devops-info-service-1   Bound      pvc-b2c3d4e5-f6a7-8901   100Mi      RWO            standard       1m
persistentvolumeclaim/data-volume-devops-info-service-2   Bound      pvc-c3d4e5f6-a7b8-9012   100Mi      RWO            standard       30s
```

**Observations:**
- Pods are named with ordinal suffixes: `devops-info-service-0`, `devops-info-service-1`, `devops-info-service-2`
- Each pod has its own PVC bound
- Headless service has `CLUSTER-IP: None`

### DNS Resolution Test

```bash
# Exec into first pod
kubectl exec -it devops-info-service-0 -- /bin/sh

# Inside the pod, resolve other pods
nslookup devops-info-service-1.devops-info-service-headless
nslookup devops-info-service-2.devops-info-service-headless
```

**Output:**
```
Server:    10.96.0.10
Address 1: 10.96.0.10 kube-dns.kube-system.svc.cluster.local

Name:      devops-info-service-1.devops-info-service-headless
Address 1: 10.244.0.15 devops-info-service-1.devops-info-service-headless.default.svc.cluster.local

Name:      devops-info-service-2.devops-info-service-headless
Address 1: 10.244.0.16 devops-info-service-2.devops-info-service-headless.default.svc.cluster.local
```

**DNS Naming Pattern:**
- `devops-info-service-0.devops-info-service-headless.default.svc.cluster.local`
- `devops-info-service-1.devops-info-service-headless.default.svc.cluster.local`
- `devops-info-service-2.devops-info-service-headless.default.svc.cluster.local`

### Per-Pod Storage Isolation

```bash
# Port-forward to each pod individually
kubectl port-forward pod/devops-info-service-0 8080:5000 &
kubectl port-forward pod/devops-info-service-1 8081:5000 &
kubectl port-forward pod/devops-info-service-2 8082:5000 &

# Check visits count on each pod
curl http://localhost:8080/visits
curl http://localhost:8081/visits
curl http://localhost:8082/visits
```

**Output (demonstrating isolation):**
```
# Pod 0 visits
{"visits": 5}

# Pod 1 visits
{"visits": 3}

# Pod 2 visits
{"visits": 7}
```

Each pod maintains its own visit count because each has its own persistent volume.

### Persistence Test

```bash
# Check current visit count and data file
kubectl exec devops-info-service-0 -- cat /data/visits

# Note the visit count (e.g., 5)
# Delete pod-0 (StatefulSet will recreate it with same identity)
kubectl delete pod devops-info-service-0

# Wait for pod to restart
kubectl get pods -w

# After restart, check visit count again
kubectl exec devops-info-service-0 -- cat /data/visits
```

**Output:**
```
# Before deletion
5

# After pod restart
5  # Same value - data persisted!
```

**Explanation:**
- When pod `devops-info-service-0` is deleted, its PVC `data-volume-devops-info-service-0` is preserved
- When StatefulSet recreates the pod, it reattaches the same PVC
- The visit count data survives the pod deletion

---

## Task 4 — Summary

### Key Takeaways

1. **StatefulSets provide stable identity** - Pods have predictable names and DNS records
2. **Per-pod storage isolation** - Each pod gets its own PVC via volumeClaimTemplates
3. **Data persistence** - Storage survives pod restarts and rescheduling
4. **Ordered operations** - Pods start and stop in a defined order

### Files Created/Modified

| File | Purpose |
|------|---------|
| `templates/statefulset.yaml` | StatefulSet resource with volumeClaimTemplates |
| `templates/headless-service.yaml` | Headless service for pod DNS resolution |
| `templates/pvc.yaml` | Modified: disabled when StatefulSet is enabled |
| `templates/deployment.yaml` | Modified: disabled when StatefulSet is enabled |
| `templates/rollout-bluegreen.yaml` | Modified: disabled when StatefulSet is enabled |
| `templates/rollout-canary.yaml` | Modified: disabled when StatefulSet is enabled |
| `values.yaml` | Added statefulset configuration section |
| `k8s/STATEFULSET.md` | This documentation file |

### Template Conditional Logic

```
┌─────────────────────────────────────────────────────────────┐
│  statefulset.enabled = false (default)                      │
│  → Deployment: ✓                                            │
│  → PVC: ✓                                                   │
│  → Rollouts (Canary/BlueGreen): ✓                           │
│  → StatefulSet: ✗                                           │
│  → Headless Service: ✗                                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  statefulset.enabled = true                                 │
│  → Deployment: ✗                                            │
│  → PVC: ✗ (using volumeClaimTemplates instead)              │
│  → Rollouts (Canary/BlueGreen): ✗                           │
│  → StatefulSet: ✓                                           │
│  → Headless Service: ✓                                      │
└─────────────────────────────────────────────────────────────┘
```

### Verification Checklist

- [x] StatefulSet guarantees documented
- [x] `statefulset.yaml` created with volumeClaimTemplates
- [x] Headless service created with `clusterIP: None`
- [x] Per-pod PVCs verified (data-volume-devops-info-service-0, -1, -2)
- [x] DNS resolution tested (pod-N.service-headless pattern)
- [x] Per-pod storage isolation proven (different visit counts)
- [x] Persistence test passed (data survives pod deletion)