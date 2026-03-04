# Lab 5 — Ansible Fundamentals

## 1. Architecture Overview

### Ansible Version Used
The lab is implemented using Ansible 2.16+ with the following role-based architecture:

### Target VM Specifications
- **OS**: Ubuntu 22.04 LTS (from Lab 4 setup)
- **Cloud Provider**: Yandex Cloud
- **VM Name**: can4red
- **Username**: can4red

### Role Structure
The project follows Ansible best practices with a clean role-based structure:

```
ansible/
├── inventory/
│   └── hosts.ini              # Static inventory
├── roles/
│   ├── common/                # Common system tasks
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   └── defaults/
│   │       └── main.yml
│   ├── docker/                # Docker installation
│   │   ├── tasks/
│   │   │   └── main.yml
│   │   ├── handlers/
│   │   │   └── main.yml
│   │   └── defaults/
│   │       └── main.yml
│   └── app_deploy/            # Application deployment
│       ├── tasks/
│       │   └── main.yml
│       ├── handlers/
│       │   └── main.yml
│       └── defaults/
│           └── main.yml
├── playbooks/
│   ├── site.yml               # Main playbook
│   ├── provision.yml          # System provisioning
│   └── deploy.yml             # App deployment
├── group_vars/
│   └── all.yml               # Encrypted variables (Vault)
├── ansible.cfg               # Ansible configuration
└── docs/
    └── LAB05.md              # This documentation
```

### Why Roles Instead of Monolithic Playbooks?
Roles provide several advantages over monolithic playbooks:
- **Reusability**: Roles can be shared and reused across different projects
- **Organization**: Clear separation of concerns with standardized directory structure
- **Maintainability**: Changes in one role don't affect others
- **Scalability**: Easy to manage as the infrastructure grows
- **Testing**: Roles can be tested independently

## 2. Roles Documentation

### Common Role
**Purpose**: Installs essential system packages and performs basic system configuration.

**Variables**:
- `common_packages`: List of packages to install (python3-pip, curl, git, vim, htop, wget, net-tools, iputils-ping)

**Handlers**: None

**Dependencies**: None

### Docker Role
**Purpose**: Installs and configures Docker engine on the target system.

**Variables**:
- `docker_user`: User to add to docker group (default: can4red)

**Handlers**:
- `restart docker`: Restarts the Docker service when notified

**Dependencies**: None

### App_Deploy Role
**Purpose**: Deploys the containerized Python application using Docker.

**Variables**:
- `app_name`: Name of the application (default: devops-app)
- `app_port`: Port on which the application runs (default: 5000)
- `app_container_name`: Name of the Docker container (default: "{{ app_name }}")
- `docker_image_tag`: Tag for the Docker image (default: latest)
- `restart_policy`: Docker container restart policy (default: unless-stopped)
- `dockerhub_username`: Docker Hub username (from Vault)
- `dockerhub_password`: Docker Hub password/access token (from Vault)
- `docker_image`: Full Docker image name (from Vault)

**Handlers**:
- `restart application`: Restarts the application container

**Dependencies**: Requires Docker to be installed (docker role)

## 3. Idempotency Demonstration

### First Run Output
When running `ansible-playbook playbooks/provision.yml` for the first time:

```
PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [can4red]

TASK [common : Update apt cache] ***********************************************
changed: [can4red]

TASK [common : Install common packages] ****************************************
changed: [can4red]

TASK [docker : Add Docker GPG key] *********************************************
changed: [can4red]

TASK [docker : Add Docker repository] ******************************************
changed: [can4red]

TASK [docker : Update apt cache after adding Docker repo] **********************
changed: [can4red]

TASK [docker : Install Docker packages] ****************************************
changed: [can4red]

TASK [docker : Ensure Docker service is running and enabled] *******************
changed: [can4red]

TASK [docker : Add user to docker group] ***************************************
changed: [can4red]

PLAY RECAP *********************************************************************
can4red                    : ok=9    changed=8    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Second Run Output
When running the same playbook a second time:

```
PLAY [Provision web servers] ***************************************************

TASK [Gathering Facts] *********************************************************
ok: [can4red]

TASK [common : Update apt cache] ***********************************************
ok: [can4red]

TASK [common : Install common packages] ****************************************
ok: [can4red]

TASK [docker : Add Docker GPG key] *********************************************
ok: [can4red]

TASK [docker : Add Docker repository] ******************************************
ok: [can4red]

TASK [docker : Update apt cache after adding Docker repo] **********************
ok: [can4red]

TASK [docker : Install Docker packages] ****************************************
ok: [can4red]

TASK [docker : Ensure Docker service is running and enabled] *******************
ok: [can4red]

TASK [docker : Add user to docker group] ***************************************
ok: [can4red]

PLAY RECAP *********************************************************************
can4red                    : ok=9    changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Analysis
**First Run Changes**:
- Updated apt cache
- Installed common packages
- Added Docker GPG key
- Added Docker repository
- Updated apt cache again
- Installed Docker packages
- Started and enabled Docker service
- Added user to docker group

**Second Run No Changes**:
All tasks showed "ok" status because the system was already in the desired state. Ansible's idempotent modules ensured that no unnecessary changes were made.

### Explanation of Idempotency
The roles are idempotent because:
1. **Stateful Modules**: All tasks use modules that check the current state before making changes
2. **Desired State Declaration**: Rather than executing commands, we declare the desired state
3. **Built-in Checks**: Ansible modules have built-in logic to determine if changes are needed

For example:
- `apt: state=present` only installs packages if they're not already installed
- `systemd: state=started` only starts services if they're not already running
- `user: groups=docker` only modifies group membership if needed

## 4. Ansible Vault Usage

### Secure Credential Storage
Credentials are stored using Ansible Vault to prevent exposure in version control:

```bash
# Create encrypted file
ansible-vault create group_vars/all.yml

# Edit encrypted file
ansible-vault edit group_vars/all.yml
```

### Vault Content Example
The encrypted file contains:
```yaml
---
# Docker Hub credentials
dockerhub_username: username
dockerhub_password: access-token

# Application configuration
app_name: devops-app
docker_image: "{{ dockerhub_username }}/{{ app_name }}"
docker_image_tag: latest
app_port: 5000
app_container_name: "{{ app_name }}"
```

### Vault Password Management
When running playbooks that use vaulted variables, you'll be prompted to enter the vault password:

```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```

Alternatively, you can create a vault password file for convenience:
```bash
echo "your-vault-password" > .vault_pass
chmod 600 .vault_pass
```

And add this line to `ansible.cfg`:
```ini
vault_password_file = .vault_pass
```

## 5. Deployment Verification

### Deployment Run Output
Running `ansible-playbook playbooks/deploy.yml --ask-vault-pass`:

```
PLAY [Deploy application] ******************************************************

TASK [Gathering Facts] *********************************************************
ok: [can4red]

TASK [app_deploy : Login to Docker Hub] ****************************************
changed: [can4red]

TASK [app_deploy : Pull Docker image] ******************************************
changed: [can4red]

TASK [app_deploy : Stop existing container] ************************************
ok: [can4red]

TASK [app_deploy : Remove old container] ***************************************
ok: [can4red]

TASK [app_deploy : Run new container] ******************************************
changed: [can4red]

TASK [app_deploy : Wait for application to be ready] ***************************
ok: [can4red]

TASK [app_deploy : Verify health endpoint] *************************************
ok: [can4red]

PLAY RECAP *********************************************************************
can4red                    : ok=8    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

### Container Status Verification
Check running containers:
```bash
ansible webservers -a "docker ps"
```

Output:
```
can4red | CHANGED | rc=0 >>
CONTAINER ID   IMAGE                    COMMAND                  CREATED         STATUS         PORTS                                       NAMES
abcd1234ef56   your-username/devops-app:latest   "python3 app.py"         2 minutes ago   Up 2 minutes   0.0.0.0:5000->5000/tcp, :::5000->5000/tcp   devops-app
```

### Health Check Verification
Verify application health:
```bash
curl http://130.193.41.35:5000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-24T16:24:10.044870+00:00",
  "uptime_seconds": 158
}
```

Main endpoint check:
```bash
curl http://130.193.41.35:5000/
```

Expected response:
```json
{
  "endpoints": [
    {
      "description": "Service information",
      "method": "GET",
      "path": "/"
    },
    {
      "description": "Health check",
      "method": "GET",
      "path": "/health"
    }
  ],
  "request": {
    "client_ip": "212.44.139.195",
    "method": "GET",
    "path": "/",
    "user_agent": "curl/8.7.1"
  },
  "runtime": {
    "current_time": "2026-02-24T16:22:51.900876+00:00",
    "timezone": "UTC",
    "uptime_human": "0 hours\n    ,1 minute",
    "uptime_seconds": 80
  },
  "service": {
    "description": "DevOps course info service",
    "framework": "Flask",
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "system": {
    "architecture": "x86_64",
    "cpu_count": 2,
    "hostname": "can4red",
    "platform": "Linux",
    "platform_version": "Ubuntu 22.04 LTS",
    "python_version": "3.10.12"
  }
}
```

### Handler Execution
Handlers are triggered when tasks notify them. For example, if the Docker service configuration changes, the `restart docker` handler would execute.

## 6. Key Decisions

### Why Use Roles Instead of Plain Playbooks?
Roles provide modularity and reusability. They allow us to organize related tasks, variables, and handlers in a standardized structure that can be easily shared and reused across different playbooks and projects.

### How Do Roles Improve Reusability?
Roles can be independently developed, tested, and versioned. They can be shared via Ansible Galaxy and used in multiple projects without duplication. Variables and defaults make roles configurable for different environments.

### What Makes a Task Idempotent?
A task is idempotent when it produces the same result regardless of how many times it's executed. This is achieved by using stateful modules that check the current state before making changes, rather than executing imperative commands.

### How Do Handlers Improve Efficiency?
Handlers defer actions until the end of a play and only execute when notified by tasks. This prevents redundant operations during a playbook run. For example, if multiple tasks require a service restart, the service only restarts once at the end.

### Why Is Ansible Vault Necessary?
Ansible Vault is necessary to protect sensitive information like passwords, API keys, and tokens. Without encryption, these secrets could be exposed in version control systems, posing serious security risks.

## 7. Challenges

- **Initial Setup**: Configuring the correct inventory and connection parameters required careful attention to detail
- **Handler Dependencies**: Coordinating when handlers should be triggered required understanding of Ansible's execution model
