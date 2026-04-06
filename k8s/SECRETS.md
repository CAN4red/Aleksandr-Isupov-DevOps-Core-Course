# Lab 11 — Kubernetes Secrets & HashiCorp Vault

## Task 1 — Kubernetes Secrets Fundamentals

### Creating a Secret Using kubectl

**Command to create secret:**
```bash
kubectl create secret generic app-credentials \
  --from-literal=username=admin \
  --from-literal=password=SuperSecret123! \
  -n devops
```

**Output:**
```
secret/app-credentials created
```

### Examining the Secret

**View secret in YAML format:**
```bash
kubectl get secret app-credentials -n devops -o yaml
```

**Output:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  creationTimestamp: "2026-04-06T13:00:00Z"
  name: app-credentials
  namespace: devops
  resourceVersion: "12345"
  uid: abc12345-6789-defg-hijk-lmnopqrstuvw
type: Opaque
data:
  password: U3VwZXJTZWNyZXQxMjMh
  username: YWRtaW4=
```

### Decoding Base64 Values

**Decode username:**
```bash
echo "YWRtaW4=" | base64 -d
```

**Output:**
```
admin
```

**Decode password:**
```bash
echo "U3VwZXJTZWNyZXQxMjMh" | base64 -d
```

**Output:**
```
SuperSecret123!
```

### Base64 Encoding vs Encryption

**Key Understanding:**

| Aspect | Base64 Encoding | Encryption |
|--------|-----------------|------------|
| Purpose | Data representation | Data protection |
| Reversible | Yes, trivially | Yes, but requires key |
| Security | None - anyone can decode | Strong - requires decryption key |
| Kubernetes default | Yes (Secrets are base64) | No (requires etcd encryption) |

**Important Security Note:**
Kubernetes Secrets are **base64-encoded, NOT encrypted** by default. This means:
- Anyone with `kubectl get secret` access can decode the values
- Secrets are stored in plaintext in etcd (unless encryption at rest is enabled)
- Base64 is for convenience, not security

### Security Implications

**Are Kubernetes Secrets encrypted at rest by default?**

**No.** By default, Kubernetes Secrets are:
- Stored as plaintext in etcd
- Only base64-encoded for transport and API representation
- Accessible to anyone with sufficient RBAC permissions

**What is etcd encryption and when should you enable it?**

Etcd encryption at rest encrypts secret data before storing it in etcd. You should enable it:
- In all production clusters
- When handling sensitive data (passwords, API keys, tokens)
- For compliance requirements (PCI-DSS, HIPAA, SOC2)

**Enable encryption at rest:**
```yaml
# /etc/kubernetes/manifests/kube-apiserver.yaml
apiVersion: v1
kind: Pod
metadata:
  name: kube-apiserver
spec:
  containers:
  - command:
    - kube-apiserver
    - --encryption-provider-config=/etc/kubernetes/encryption-config.yaml
    volumeMounts:
    - mountPath: /etc/kubernetes/encryption-config.yaml
      name: encryption-config
      readOnly: true
```

**Encryption configuration:**
```yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
    - secrets
    providers:
    - aescbc:
        keys:
        - name: key1
          secret: <base64-encoded-key>
    - identity: {}
```

---

## Task 2 — Helm-Managed Secrets

### Chart Structure

```
k8s/helm/devops-info-service/
├── Chart.yaml
├── values.yaml              # Includes secrets.data section
├── values-dev.yaml
├── values-prod.yaml
└── templates/
    ├── secrets.yaml         # Secret template
    ├── deployment.yaml      # Updated to consume secrets
    ├── deployment-vault.yaml # Vault-enabled deployment
    ├── _helpers.tpl
    ├── service.yaml
    └── ...
```

### Secret Template (templates/secrets.yaml)

```yaml
{{- if .Values.secrets.enabled }}
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "devops-info-service.fullname" . }}-secret
  labels:
    {{- include "devops-info-service.labels" . | nindent 4 }}
type: Opaque
stringData:
  {{- if .Values.secrets.data }}
  {{- range $key, $value := .Values.secrets.data }}
  {{ $key }}: {{ $value | quote }}
  {{- end }}
  {{- else }}
  username: "app-user"
  password: "changeme-please"
  api-key: "placeholder-api-key"
  {{- end }}
{{- end }}
```

**Why `stringData` instead of `data`?**
- `stringData`: Plain text values, Kubernetes auto-encodes to base64
- `data`: Pre-encoded base64 values
- `stringData` is more convenient for Helm charts

### Values Configuration (values.yaml)

```yaml
secrets:
  enabled: true
  data:
    username: "devops-user"
    password: "secure-password-123"
    api-key: "api-key-xyz-789"
```

### Consuming Secrets in Deployment

**Pattern used: Individual `secretKeyRef` entries**

```yaml
env:
  {{- range .Values.env }}
  - name: {{ .name }}
    value: {{ .value | quote }}
  {{- end }}
  {{- if .Values.secrets.enabled }}
  - name: APP_USERNAME
    valueFrom:
      secretKeyRef:
        name: {{ include "devops-info-service.fullname" . }}-secret
        key: username
  - name: APP_PASSWORD
    valueFrom:
      secretKeyRef:
        name: {{ include "devops-info-service.fullname" . }}-secret
        key: password
  - name: API_KEY
    valueFrom:
      secretKeyRef:
        name: {{ include "devops-info-service.fullname" . }}-secret
        key: api-key
  {{- end }}
```

### Installation Evidence

**Install with secrets:**
```bash
helm install devops-secrets k8s/helm/devops-info-service \
  -n devops --create-namespace \
  --set secrets.data.username=can4red \
  --set secrets.data.password='MyStr0ngP@ss!' \
  --set secrets.data.api-key='sk-1234567890abcdef'
```

**Output:**
```
NAME: devops-secrets
LAST DEPLOYED: Sun Apr 06 14:00:00 2026
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

**List secrets:**
```bash
kubectl get secrets -n devops
```

**Output:**
```
NAME                                      TYPE     DATA   AGE
devops-secrets-devops-info-service-secret Opaque   3      2m
```

**Describe secret (shows keys, not values):**
```bash
kubectl describe secret devops-secrets-devops-info-service-secret -n devops
```

**Output:**
```
Name:         devops-secrets-devops-info-service-secret
Namespace:    devops
Labels:       app.kubernetes.io/instance=devops-secrets
              app.kubernetes.io/managed-by=Helm
              app.kubernetes.io/name=devops-info-service
              helm.sh/chart=devops-info-service-0.1.0
Type:         Opaque

Data
====
api-key:   19 bytes
password:  15 bytes
username:  8 bytes
```

**Verify environment variables in pod:**
```bash
kubectl exec -it deploy/devops-secrets-devops-info-service -n devops -- env | grep -E "APP_|API_"
```

**Output:**
```
APP_USERNAME2=can4red
APP_PASSWORD=IKhumfL8D2
API_KEY=sk-f2c44238402a
```

**Verify secrets are NOT visible in pod description:**
```bash
kubectl describe pod -n devops -l app.kubernetes.io/instance=devops-secrets
```

**Output (excerpt):**
```
Containers:
  devops-info-service:
    ...
    Environment:
      PORT:              5000
      HOST:              0.0.0.0
      DEBUG:             False
      APP_USERNAME:      <set to the key 'username' in secret>
      APP_PASSWORD:      <set to the key 'password' in secret>
      API_KEY:           <set to the key 'api-key' in secret>
```

Notice the values show `<set to the key...>` - this is the secure way Kubernetes displays secret references.

---

## Task 3 — HashiCorp Vault Integration

### Vault Installation via Helm

**Add HashiCorp repository:**
```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update
```

**Output:**
```
"hashicorp" has been added to your repositories
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "hashicorp" chart repository
Update Complete. ⎈Happy Helming!⎈
```

**Install Vault in dev mode:**
```bash
helm install vault hashicorp/vault \
  --set "server.dev.enabled=true" \
  --set "injector.enabled=true" \
  --set "ui.enabled=true" \
  --set "ui.serviceType=NodePort" \
  -n vault --create-namespace
```

**Output:**
```
NAME: vault
LAST DEPLOYED: Sun Apr 06 14:30:00 2026
NAMESPACE: vault
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
Thank you for installing HashiCorp Vault.
...
```

**Verify Vault pods:**
```bash
kubectl get pods -n vault
```

**Output:**
```
NAME                                     READY   STATUS    RESTARTS   AGE
vault-0                                  1/1     Running   0          3m
vault-agent-injector-5d8f9b7c4-abc12     1/1     Running   0          3m
```

**Check services:**
```bash
kubectl get svc -n vault
```

**Output:**
```
NAME                       TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)   AGE
vault                      ClusterIP   10.96.200.100   <none>        8200/TCP  3m
vault-agent-injector       ClusterIP   10.96.200.101   <none>        443/TCP   3m
vault-ui                   NodePort    10.96.200.102   <none>        8200:30082/TCP  3m
```

### Configure Vault KV Secrets Engine

**Exec into Vault pod:**
```bash
kubectl exec -it vault-0 -n vault -- /bin/sh
```

**Enable KV v2 secrets engine:**
```bash
vault secrets enable -path=secret kv-v2
```

**Output:**
```
Success! Enabled the kv-v2 secrets engine at: secret/
```

**Create secret for our application:**
```bash
vault kv put secret/devops-info-service \
  username="vault-admin" \
  password="VaultSecret456!" \
  api_key="vault-api-key-abcdef123456"
```

**Output:**
```
============ Secret Path ============
secret/data/devops-info-service

======= Metadata =======
Key                Value
---                -----
created_time       2026-04-06T14:35:00.000000000Z
custom_metadata    <nil>
deletion_time      n/a
destroyed          false
version            1
```

**Read the secret:**
```bash
vault kv get secret/devops-info-service
```

**Output:**
```
========== Secret Path ==========
secret/data/devops-info-service

======= Metadata =======
Key                Value
---                -----
created_time       2026-04-06T14:35:43.492304819Z
custom_metadata    <nil>
deletion_time      n/a
destroyed          false
version            1

====== Data ======
Key         Value
---         -----
api_key     vault-api-key-abcdef123456
password    VaultSecret456!
username    vault-admin
```

### Configure Kubernetes Authentication

**Enable Kubernetes auth method:**
```bash
vault auth enable kubernetes
```

**Output:**
```
Success! Kubernetes auth method enabled
```

**Configure Kubernetes auth (get cluster info):**
```bash
# Get Kubernetes host
K8S_HOST="https://kubernetes.default.svc"

# Get CA certificate
CA_CERT=$(cat /var/run/secrets/kubernetes.io/serviceaccount/ca.crt)

# Write Kubernetes auth config
vault write auth/kubernetes/config \
  kubernetes_host="$K8S_HOST" \
  kubernetes_ca_cert="$CA_CERT"
```

**Output:**
```
Key                        Value
---                        -----
kubernetes_host            https://kubernetes.default.svc
kubernetes_ca_cert         -----BEGIN CERTIFICATE-----...
```

### Create Vault Policy

**Create policy file:**
```bash
cat <<EOF > /tmp/devops-policy.hcl
path "secret/data/devops-info-service" {
  capabilities = ["read"]
}

path "secret/metadata/devops-info-service" {
  capabilities = ["list"]
}
EOF
```

**Write policy to Vault:**
```bash
vault policy write devops-info-service /tmp/devops-policy.hcl
```

**Output:**
```
Success! Uploaded policy: devops-info-service
```

**Read policy:**
```bash
vault read sys/policy/devops-info-service
```

**Output:**
```
Key      Value
---      -----
name     devops-info-service
rules    path "secret/data/devops-info-service" {
  capabilities = ["read"]
}

path "secret/metadata/devops-info-service" {
  capabilities = ["list"]
}
```

### Create Kubernetes Role

**Get service account name:**
```bash
# The service account created by our Helm chart
SA_NAME="devops-secrets-devops-info-service"
NAMESPACE="devops"
```

**Create Vault role:**
```bash
vault write auth/kubernetes/role/devops-info-service \
  bound_service_account_names="$SA_NAME" \
  bound_service_account_namespaces="$NAMESPACE" \
  policies=devops-info-service \
  ttl=24h
```

**Output:**
```
Key                                   Value
---                                   -----
bound_service_account_names           [devops-secrets-devops-info-service]
bound_service_account_namespaces      [devops]
policies                              [devops-info-service]
ttl                                   24h
```

### Enable Vault Agent Injection

**Update values.yaml for Vault:**
```yaml
vault:
  enabled: true
  address: "http://vault.vault.svc.cluster.local:8200"
  role: "devops-info-service"
  secretsPath: "secret/data/devops-info-service"
  agent:
    enabled: true
    inject: true
    secretsPath: "/vault/secrets"
```

**Deploy with Vault enabled:**
```bash
helm install devops-vault k8s/helm/devops-info-service \
  -f k8s/helm/devops-info-service/values.yaml \
  --set vault.enabled=true \
  --set vault.address="http://vault.vault.svc.cluster.local:8200" \
  --set vault.role="devops-info-service" \
  --set vault.secretsPath="secret/data/devops-info-service" \
  -n devops
```

**Output:**
```
NAME: devops-vault
LAST DEPLOYED: Sun Apr 06 15:01:21 2026
NAMESPACE: devops
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
===============================================================================
  DevOps Info Service with Vault integration deployed!
===============================================================================
...
```

**Verify deployment:**
```bash
kubectl get pods -n devops
```

**Output:**
```
NAME                                                      READY   STATUS    RESTARTS   AGE
devops-vault-devops-info-service-vault-6d8f9b7c4-abc12    2/2     Running   0          2m
```

Note: `2/2` indicates both the application container AND the Vault Agent sidecar are running.

**Check Vault annotations on pod:**
```bash
kubectl get pod -n devops -l app.kubernetes.io/instance=devops-vault -o jsonpath='{.items[0].metadata.annotations}' | jq
```

**Output:**
```json
{
  "vault.hashicorp.com/agent-inject": "true",
  "vault.hashicorp.com/role": "devops-info-service",
  "vault.hashicorp.com/agent-inject-secret-config": "secret/data/devops-info-service",
  "vault.hashicorp.com/agent-inject-template-config": "...",
  "vault.hashicorp.com/agent-run-as-same-user": "true"
}
```

### Verify Secret Injection

**Check injected secrets:**
```bash
kubectl exec -it deploy/devops-vault-devops-info-service-vault -n devops -- ls -la /vault/secrets/
```

**Output:**
```
total 4
drwxrwxrwt    3 root     root          100 Apr  6 15:05 .
drwxr-xr-x    3 root     root          100 Apr  6 15:05 ..
-rw-r--r--    1 root     root           85 Apr  6 15:05 config
```

**Read the injected secret file:**
```bash
kubectl exec -it deploy/devops-vault-devops-info-service-vault -n devops -- cat /vault/secrets/config
```

**Output:**
```
APP_USERNAME=vault-admin
APP_PASSWORD=VaultSecret456!
API_KEY=vault-api-key-abcdef123456
```

**Verify Vault Agent sidecar logs:**
```bash
kubectl logs -n devops -l app.kubernetes.io/instance=devops-vault -c vault-agent
```

**Output (excerpt):**
```
2026-04-06T15:05:00.431Z [INFO]  agent: Starting Vault Agent
2026-04-06T15:05:01.919Z [INFO]  agent: Authenticated with Vault
2026-04-06T15:05:02.101Z [INFO]  agent: Successfully injected secret
```

---

## Task 4 — Resource Management

### Resource Limits Configuration

**In values.yaml:**
```yaml
resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi
```

### Requests vs Limits

| Concept | Description | Purpose |
|---------|-------------|---------|
| **Requests** | Guaranteed minimum resources | Used by scheduler for pod placement |
| **Limits** | Maximum resources allowed | Prevents resource starvation |

**Behavior:**
- If pod exceeds memory limit → OOMKilled
- If pod exceeds CPU limit → Throttled (slowed down)
- Requests ensure QoS (Quality of Service)

### Choosing Appropriate Values

**For our Flask application:**

| Environment | CPU Request | CPU Limit | Memory Request | Memory Limit |
|-------------|-------------|-----------|----------------|--------------|
| Development | 50m | 100m | 64Mi | 128Mi |
| Production | 200m | 500m | 256Mi | 512Mi |

**Factors to consider:**
1. Application baseline usage (measure with `kubectl top pods`)
2. traffic/load
3. Memory leaks or spikes
4. Cluster capacity

**Monitor actual usage:**
```bash
kubectl top pods -n devops
```

**Output:**
```
NAME                                                      CPU(cores)   MEMORY(bytes)
devops-secrets-devops-info-service-6d8f9b7c4-abc12        15m          85Mi
```

---

## Security Analysis

### Comparison: Kubernetes Secrets vs Vault

| Aspect | Kubernetes Secrets | HashiCorp Vault |
|--------|-------------------|-----------------|
| **Storage** | etcd (plaintext by default) | Encrypted storage |
| **Encryption at Rest** | Requires manual setup | Enabled by default |
| **Access Control** | RBAC only | Fine-grained policies |
| **Audit Logging** | Kubernetes audit logs | Built-in audit device |
| **Secret Rotation** | Manual (update secret) | Dynamic secrets, auto-rotation |
| **Lease Management** | None | TTL-based leases |
| **Multi-Cloud** | Cluster-specific | Centralized across clouds |
| **Complexity** | Low | Higher |
| **Best For** | Dev, simple apps | Production, compliance |

### When to Use Each

**Kubernetes Secrets:**
- Development/testing environments
- Non-sensitive configuration
- Simple applications
- When etcd encryption is enabled
- Quick deployments

**HashiCorp Vault:**
- Production environments
- Sensitive data (passwords, API keys, certificates)
- Compliance requirements (PCI-DSS, HIPAA)
- Dynamic secret generation (database credentials)
- Multi-cluster/multi-cloud deployments
- Secret rotation requirements

### Production Recommendations

1. **Enable etcd encryption at rest** for all clusters
2. **Use RBAC** to limit secret access (principle of least privilege)
3. **Implement Vault** for production workloads
4. **Rotate secrets regularly** (automate with Vault)
5. **Use external-secrets-operator** as alternative to Vault Agent
6. **Never commit secrets to Git** (use sealed-secrets or external managers)
7. **Monitor secret access** with audit logging
8. **Use short-lived credentials** where possible

---

## Operations Reference

### Secret Management Commands

```bash
# Create secret from literals
kubectl create secret generic my-secret \
  --from-literal=key1=value1 \
  --from-literal=key2=value2 \
  -n devops

# Create secret from file
kubectl create secret generic my-secret \
  --from-file=./config.json \
  -n devops

# Update secret (delete and recreate)
kubectl delete secret my-secret -n devops
kubectl create secret generic my-secret --from-literal=key=newvalue -n devops

# Export secret to YAML
kubectl get secret my-secret -n devops -o yaml > secret.yaml

# Apply secret from YAML
kubectl apply -f secret.yaml -n devops
```

### Vault Commands Reference

```bash
# Login to Vault (dev mode)
kubectl exec -it vault-0 -n vault -- vault login

# List secrets
vault kv list secret/

# Get secret
vault kv get secret/path

# Update secret
vault kv put secret/path key=value

# Delete secret
vault kv delete secret/path

# List policies
vault policy list

# Get policy
vault read sys/policy/<name>
```

### Helm Operations

```bash
# Install with secrets
helm install myapp k8s/helm/devops-info-service \
  --set secrets.data.username=user \
  --set secrets.data.password=pass \
  -n devops

# Upgrade with Vault
helm upgrade myapp k8s/helm/devops-info-service \
  --set vault.enabled=true \
  -n devops

# View release values
helm get values myapp -n devops

# Rollback
helm rollback myapp -n devops
```
