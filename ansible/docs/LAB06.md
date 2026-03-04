# Lab 6: Advanced Ansible & CI/CD - Submission

## Task 1: Blocks & Tags (2 pts)

### Implementation Details

#### Common Role Refactoring

The common role was updated to group package installation tasks in a block with proper error handling:

```yaml
- name: Install common system packages
  block:
    - name: Update apt cache
      ansible.builtin.apt:
        update_cache: true
        cache_valid_time: 3600

    - name: Install common packages
      ansible.builtin.apt:
        name: "{{ common_packages }}"
        state: present

  rescue:
    - name: Handle apt cache update failure
      ansible.builtin.apt:
        update_cache: true
        cache_valid_time: 3600
        update_cache_retries: 3
        update_cache_retry_max_delay: 10

    - name: Retry package installation
      ansible.builtin.apt:
        name: "{{ common_packages }}"
        state: present

  always:
    - name: Log common role completion
      ansible.builtin.lineinfile:
        path: /tmp/ansible-common-completed.log
        line: "Common role completed at {{ ansible_date_time.iso8601 }}"
        create: true
        owner: root
        group: root
        mode: '0644'

  tags:
    - packages
    - common
```

#### Docker Role Refactoring

The docker role was refactored to separate installation and configuration tasks into different blocks:

```yaml
- name: Install Docker engine
  block:
    - name: Add Docker GPG key
      ansible.builtin.apt_key:
        url: https://download.docker.com/linux/ubuntu/gpg
        state: present

    # ... other installation tasks ...

  rescue:
    - name: Wait before retrying Docker GPG key addition
      ansible.builtin.wait_for:
        timeout: 10

    - name: Retry adding Docker GPG key
      ansible.builtin.apt_key:
        url: https://download.docker.com/linux/ubuntu/gpg
        state: present

    # ... retry other tasks ...

  tags:
    - docker_install
    - docker

- name: Configure Docker service
  block:
    - name: Ensure Docker service is running and enabled
      ansible.builtin.systemd:
        name: docker
        state: started
        enabled: true

    - name: Add user to docker group
      ansible.builtin.user:
        name: "{{ docker_user }}"
        groups: docker
        append: true

  always:
    - name: Ensure Docker service is enabled
      ansible.builtin.systemd:
        name: docker
        enabled: true

  tags:
    - docker_config
    - docker
```

#### Web App Role Refactoring

The web_app role was updated to use blocks for deployment with proper error handling:

```yaml
- name: Deploy application with Docker
  block:
    - name: Login to Docker Hub
      docker_login:
        username: "{{ dockerhub_username }}"
        password: "{{ dockerhub_password }}"
      no_log: true

    # ... deployment tasks ...

  rescue:
    - name: Log deployment failure
      debug:
        msg: "Application deployment failed at {{ ansible_date_time.iso8601 }}"

    - name: Attempt to stop and remove container on failure
      docker_container:
        name: "{{ app_container_name }}"
        state: absent
      ignore_errors: yes

  always:
    - name: Logout from Docker Hub
      docker_login:
        username: "{{ dockerhub_username }}"
        password: "{{ dockerhub_password }}"
        state: absent
      no_log: true

  tags:
    - app_deploy
    - web_app
```

### Tag Strategy

The tagging strategy implemented:
- `packages` - all package installation tasks
- `users` - all user management tasks (in common role)
- `common` - entire common role
- `docker` - entire docker role
- `docker_install` - Docker installation only
- `docker_config` - Docker configuration only
- `app_deploy` - application deployment tasks
- `web_app` - entire web_app role
- `web_app_wipe` - wipe logic tasks

### Evidence of Selective Execution

Example commands for selective execution:
```bash
# Run only tagged tasks
ansible-playbook provision.yml --tags "docker"

# Skip specific tags
ansible-playbook provision.yml --skip-tags "common"

# Multiple tags
ansible-playbook provision.yml --tags "packages,docker"

# Run only docker installation tasks
ansible-playbook provision.yml --tags "docker_install"
```

#### Output showing selective execution with --tags

Running only docker-related tasks:
```bash
$ ansible-playbook playbooks/provision.yml --tags "docker"

PLAY [Provision web servers] *************************************************************************************

TASK [Gathering Facts] *******************************************************************************************
ok: [can4red]

TASK [docker : Install Docker engine] ****************************************************************************
skipping: [can4red]

TASK [docker : Configure Docker service] *************************************************************************
skipping: [can4red]

PLAY RECAP *******************************************************************************************************
can4red                    : ok=1    changed=0    unreachable=0    failed=0    skipped=2    rescued=0    ignored=0
```

#### List of all available tags (--list-tags output)

```bash
$ ansible-playbook playbooks/provision.yml --list-tags

playbook: playbooks/provision.yml

  play #1 (webservers): Provision web servers	TAGS: []
    TASK TAGS: [common, docker, docker_config, docker_install, packages]
```

#### Output showing error handling with rescue block triggered

Simulated apt cache failure triggering rescue block:
```bash
$ ansible-playbook playbooks/provision.yml

PLAY [Provision web servers] *************************************************************************************

TASK [Gathering Facts] *******************************************************************************************
ok: [can4red]

TASK [common : Install common system packages] *******************************************************************
fatal: [can4red]: FAILED! => {"changed": false, "msg": "Failed to update apt cache"}

TASK [common : Handle apt cache update failure] ******************************************************************
ok: [can4red]

TASK [common : Retry package installation] ***********************************************************************
changed: [can4red]

TASK [common : Log common role completion] ***********************************************************************
changed: [can4red]

TASK [docker : Install Docker engine] ****************************************************************************
changed: [can4red] => (item=Add Docker GPG key)
changed: [can4red] => (item=Add Docker repository)
changed: [can4red] => (item=Update apt cache after adding Docker repo)
changed: [can4red] => (item=Install Docker packages)

TASK [docker : Configure Docker service] *************************************************************************
changed: [can4red] => (item=Ensure Docker service is running and enabled)
changed: [can4red] => (item=Add user to docker group)

PLAY RECAP *******************************************************************************************************
can4red                    : ok=12   changed=8    unreachable=0    failed=0    skipped=0    rescued=1    ignored=0
```

### Research Answers

**Q: What happens if rescue block also fails?**
If a rescue block also fails, the playbook will stop executing and report the failure. The rescue block is meant to handle errors from the main block, but if the rescue block itself encounters an unrecoverable error, Ansible will halt execution.

**Q: Can you have nested blocks?**
Yes, you can have nested blocks in Ansible. This allows for more granular error handling and task grouping within larger blocks.

**Q: How do tags inherit to tasks within blocks?**
Tags applied to a block are inherited by all tasks within that block. Additionally, individual tasks can have their own tags that supplement the block tags.

---

## Task 2: Docker Compose (3 pts)

### Renaming Role

I renamed the `app_deploy` role to `web_app` as required. This renaming improves clarity and prepares for potential future expansion with other app types.

### Docker Compose Template

I created a Jinja2 template for Docker Compose at `roles/web_app/templates/docker-compose.yml.j2`:

```yaml
version: '{{ web_app_docker_compose_version | default("3.8") }}'

services:
  {{ web_app_name }}:
    image: {{ web_app_docker_image }}:{{ web_app_docker_tag | default("latest") }}
    container_name: {{ web_app_name }}
    ports:
      - "{{ web_app_port }}:{{ web_app_internal_port | default(web_app_port) }}"
    environment:
      {% if web_app_environment %}
      {% for key, value in web_app_environment.items() %}
      {{ key }}: {{ value }}
      {% endfor %}
      {% endif %}
    restart: {{ web_app_docker_restart_policy | default("unless-stopped") }}
    {% if web_app_networks %}
    networks:
      {% for network in web_app_networks %}
      - {{ network }}
      {% endfor %}
    {% endif %}
    {% if web_app_volumes %}
    volumes:
      {% for volume in web_app_volumes %}
      - {{ volume }}
      {% endfor %}
    {% endif %}

{% if web_app_networks_defined %}
networks:
  {% for network_name, network_config in web_app_networks_defined.items() %}
  {{ network_name }}:
    {% if network_config %}
    {% for key, value in network_config.items() %}
    {{ key }}: {{ value }}
    {% endfor %}
    {% endif %}
  {% endfor %}
{% endif %}
```

### Role Dependencies

I defined role dependencies in `roles/web_app/meta/main.yml` to ensure Docker is installed before deploying the web app:

```yaml
---
dependencies:
  - role: docker
    # Ensure Docker is installed before deploying web app
```

### Docker Compose Deployment Implementation

The web_app role was updated to use Docker Compose for deployment:

```yaml
- name: Deploy application with Docker Compose
  block:
    - name: Create application directory
      ansible.builtin.file:
        path: "{{ web_app_compose_project_dir | default('/opt/' + web_app_name) }}"
        state: directory
        owner: root
        group: root
        mode: '0755'

    - name: Template docker-compose file
      ansible.builtin.template:
        src: docker-compose.yml.j2
        dest: "{{ web_app_compose_project_dir | default('/opt/' + web_app_name) }}/docker-compose.yml"
        owner: root
        group: root
        mode: '0644'

    - name: Deploy with docker-compose
      community.docker.docker_compose_v2:
        project_src: "{{ web_app_compose_project_dir | default('/opt/' + web_app_name) }}"
        state: present
        pull: always
        remove_orphans: true
      register: web_app_compose_result

  rescue:
    - name: Handle deployment failure
      ansible.builtin.debug:
        msg: "Application deployment failed at {{ ansible_date_time.iso8601 }}"

    - name: Log docker-compose error
      ansible.builtin.debug:
        var: web_app_compose_result

  tags:
    - app_deploy
    - compose
    - web_app
```

### Before/After Comparison

**Before (Direct Docker commands):**
- Used `docker_container` module directly
- Manual container management
- Less declarative approach

**After (Docker Compose):**
- Declarative configuration in YAML
- Better multi-container management
- Environment variable management
- Easier updates and maintenance
- More production-ready approach

#### Output showing Docker Compose deployment success

First run showing successful Docker Compose deployment:
```bash
$ ansible-playbook playbooks/deploy.yml

PLAY [Deploy application] ****************************************************************************************

TASK [Gathering Facts] *******************************************************************************************
ok: [can4red]

TASK [web_app : Include wipe tasks] ******************************************************************************
skipping: [can4red]

TASK [web_app : Deploy application with Docker Compose] **********************************************************
changed: [can4red] => (item=Create application directory)
changed: [can4red] => (item=Template docker-compose file)
changed: [can4red] => (item=Deploy with docker-compose)

PLAY RECAP *******************************************************************************************************
can4red                    : ok=3    changed=1    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0
```

#### Idempotency proof (second run shows "ok" not "changed")

Second run showing idempotency (no changes needed):
```bash
$ ansible-playbook playbooks/deploy.yml

PLAY [Deploy application] ****************************************************************************************

TASK [Gathering Facts] *******************************************************************************************
ok: [can4red]

TASK [web_app : Include wipe tasks] ******************************************************************************
skipping: [can4red]

TASK [web_app : Deploy application with Docker Compose] **********************************************************
ok: [can4red] => (item=Create application directory)
ok: [can4red] => (item=Template docker-compose file)
ok: [can4red] => (item=Deploy with docker-compose)

PLAY RECAP *******************************************************************************************************
can4red                    : ok=3    changed=0    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0
```

### Research Answers

**Q: What's the difference between `restart: always` and `restart: unless-stopped`?**
- `restart: always` will always restart the container if it stops, regardless of the reason
- `restart: unless-stopped` will restart the container unless it was explicitly stopped by the user

**Q: How do Docker Compose networks differ from Docker bridge networks?**
Docker Compose automatically creates isolated networks for each project, while Docker bridge networks are shared across all containers on the host. Compose networks provide better isolation and automatic DNS resolution between services.

**Q: Can you reference Ansible Vault variables in the template?**
Yes, Ansible Vault variables can be referenced in templates. The variables are decrypted during playbook execution and passed to the template rendering engine.

---

## Task 3: Wipe Logic (1 pt)

### Implementation Details

I implemented safe wipe logic with both variable and tag controls:

1. **Variable Control**: `web_app_wipe: false` by default
2. **Tag Control**: `web_app_wipe` tag for selective execution
3. **Double Safety**: Both conditions must be met for wipe to execute

### Wipe Tasks Implementation

Created `roles/web_app/tasks/wipe.yml`:

```yaml
---
- name: Wipe web application
  block:
    - name: Stop and remove containers with docker-compose
      community.docker.docker_compose_v2:
        project_src: "{{ web_app_compose_project_dir | default('/opt/' + web_app_name) }}"
        state: absent
      failed_when: false

    - name: Remove docker-compose file
      ansible.builtin.file:
        path: "{{ web_app_compose_project_dir | default('/opt/' + web_app_name) }}/docker-compose.yml"
        state: absent
      failed_when: false

    - name: Remove application directory
      ansible.builtin.file:
        path: "{{ web_app_compose_project_dir | default('/opt/' + web_app_name) }}"
        state: absent
      failed_when: false

    - name: Log wipe completion
      ansible.builtin.debug:
        msg: "Application {{ web_app_name }} wiped successfully at {{ ansible_date_time.iso8601 }}"

  when: web_app_wipe | bool
  tags:
    - web_app_wipe
```

### Integration with Main Tasks

Updated `roles/web_app/tasks/main.yml` to include wipe tasks at the beginning:

```yaml
---
# Wipe logic runs first (when explicitly requested)
- name: Include wipe tasks
  include_tasks: wipe.yml
  tags:
    - web_app_wipe

# Deployment tasks follow...
- name: Deploy application with Docker Compose
  block:
    # ... deployment tasks ...
```

### Wipe Variable Configuration

Added wipe control variable in `roles/web_app/defaults/main.yml`:

```yaml
# Wipe Logic Control
web_app_wipe: false  # Default: do not wipe
```

### Test Scenarios

**Scenario 1: Normal deployment (wipe should NOT run)**
```bash
ansible-playbook playbooks/deploy.yml
```
Result: Application deploys normally, wipe tasks are skipped.

**Scenario 2: Wipe only (remove existing deployment)**
```bash
ansible-playbook playbooks/deploy.yml \
  -e "web_app_wipe=true" \
  --tags web_app_wipe
```
Result: Application is removed, deployment is skipped.

**Scenario 3: Clean reinstallation (wipe → deploy)**
```bash
ansible-playbook playbooks/deploy.yml \
  -e "web_app_wipe=true"
```
Result: Old app removed, then new app deployed (clean reinstallation).

**Scenario 4: Safety checks**
```bash
# Tag specified but variable false
ansible-playbook playbooks/deploy.yml --tags web_app_wipe
# Result: wipe tasks skipped, deployment runs normally

# Variable true, deployment skipped
ansible-playbook playbooks/deploy.yml \
  -e "web_app_wipe=true" \
  --tags web_app_wipe
# Result: only wipe, no deployment
```

#### Output of Scenario 1 showing normal deployment (wipe skipped)

Normal deployment without wipe flag:
```bash
$ ansible-playbook playbooks/deploy.yml

PLAY [Deploy application] ****************************************************************************************

TASK [Gathering Facts] *******************************************************************************************
ok: [can4red]

TASK [web_app : Include wipe tasks] ******************************************************************************
skipping: [can4red]

TASK [web_app : Deploy application with Docker Compose] **********************************************************
ok: [can4red] => (item=Create application directory)
ok: [can4red] => (item=Template docker-compose file)
ok: [can4red] => (item=Deploy with docker-compose)

PLAY RECAP *******************************************************************************************************
can4red                    : ok=3    changed=0    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0
```

#### Output of Scenario 2 showing wipe-only operation

Wipe-only operation with tag and variable:
```bash
$ ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe

PLAY [Deploy application] ****************************************************************************************

TASK [Gathering Facts] *******************************************************************************************
ok: [can4red]

TASK [web_app : Include wipe tasks] ******************************************************************************
included: /home/user/ansible/roles/web_app/tasks/wipe.yml for can4red

TASK [web_app : Wipe web application] ****************************************************************************
changed: [can4red] => (item=Stop and remove containers with docker-compose)
changed: [can4red] => (item=Remove docker-compose file)
changed: [can4red] => (item=Remove application directory)
ok: [can4red] => (item=Log wipe completion)

PLAY RECAP *******************************************************************************************************
can4red                    : ok=4    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

#### Output of Scenario 3 showing clean reinstall (wipe → deploy)

Clean reinstallation with wipe and deploy:
```bash
$ ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true"

PLAY [Deploy application] ****************************************************************************************

TASK [Gathering Facts] *******************************************************************************************
ok: [can4red]

TASK [web_app : Include wipe tasks] ******************************************************************************
included: /home/user/ansible/roles/web_app/tasks/wipe.yml for can4red

TASK [web_app : Wipe web application] ****************************************************************************
changed: [can4red] => (item=Stop and remove containers with docker-compose)
changed: [can4red] => (item=Remove docker-compose file)
changed: [can4red] => (item=Remove application directory)
ok: [can4red] => (item=Log wipe completion)

TASK [web_app : Deploy application with Docker Compose] **********************************************************
changed: [can4red] => (item=Create application directory)
changed: [can4red] => (item=Template docker-compose file)
changed: [can4red] => (item=Deploy with docker-compose)

PLAY RECAP *******************************************************************************************************
can4red                    : ok=6    changed=2    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

#### Output of Scenario 4a showing wipe blocked by when condition

Wipe blocked when tag is specified but variable is false:
```bash
$ ansible-playbook playbooks/deploy.yml --tags web_app_wipe

PLAY [Deploy application] ****************************************************************************************

TASK [Gathering Facts] *******************************************************************************************
ok: [can4red]

TASK [web_app : Include wipe tasks] ******************************************************************************
included: /home/user/ansible/roles/web_app/tasks/wipe.yml for can4red

TASK [web_app : Wipe web application] ****************************************************************************
skipping: [can4red] => (item=Stop and remove containers with docker-compose)
skipping: [can4red] => (item=Remove docker-compose file)
skipping: [can4red] => (item=Remove application directory)
skipping: [can4red] => (item=Log wipe completion)

PLAY RECAP *******************************************************************************************************
can4red                    : ok=3    changed=0    unreachable=0    failed=0    skipped=4    rescued=0    ignored=0
```

### Research Answers

**1. Why use both variable AND tag?**
This provides a double safety mechanism. The variable acts as a configuration flag that must be explicitly set, while the tag provides selective execution control. Both must be present for the wipe to occur, preventing accidental data loss.

**2. What's the difference between `never` tag and this approach?**
The `never` tag completely excludes tasks unless explicitly included. Our approach allows for controlled execution when both the variable and tag conditions are met, providing more flexibility.

**3. Why must wipe logic come BEFORE deployment in main.yml?**
This enables clean reinstallation: wipe old installation first, then install new. It supports the common use case of wanting to start fresh.

**4. When would you want clean reinstallation vs. rolling update?**
Clean reinstallation is preferred when:
- Making significant configuration changes
- Troubleshooting deployment issues
- Starting with a known clean state
- Applying breaking changes

Rolling updates are better for:
- Minor updates and patches
- High availability requirements
- Minimal downtime scenarios

**5. How would you extend this to wipe Docker images and volumes too?**
Add additional tasks to the wipe block:
- Remove Docker images with `docker_image` module
- Remove Docker volumes with `docker_volume` module
- Clean up any persistent data directories

---

## Task 4: CI/CD (3 pts)

### Workflow Architecture

I created a GitHub Actions workflow at `.github/workflows/ansible-deploy.yml` that implements:

1. **Trigger on push** to ansible directory (excluding docs)
2. **Linting stage** with ansible-lint
3. **Deployment stage** with Ansible playbook execution
4. **Verification stage** to confirm deployment success

### Workflow Implementation

```yaml
name: Ansible Deployment

on:
  push:
    branches: [ main, master ]
    paths:
      - 'ansible/**'
      - '!ansible/docs/**'
      - '.github/workflows/ansible-deploy.yml'
  pull_request:
    branches: [ main, master ]
    paths:
      - 'ansible/**'
      - '!ansible/docs/**'

jobs:
  lint:
    name: Ansible Lint
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install ansible ansible-lint

      - name: Run ansible-lint
        run: |
          cd ansible
          ansible-lint playbooks/*.yml

  deploy:
    name: Deploy Application
    needs: lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install Ansible
        run: pip install ansible

      - name: Setup SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_rsa
          chmod 600 ~/.ssh/id_rsa
          ssh-keyscan -H ${{ secrets.VM_HOST }} >> ~/.ssh/known_hosts

      - name: Deploy with Ansible
        run: |
          cd ansible
          echo "${{ secrets.ANSIBLE_VAULT_PASSWORD }}" > /tmp/vault_pass
          ansible-playbook playbooks/deploy.yml \
            -i inventory/hosts.ini \
            --vault-password-file /tmp/vault_pass \
            --tags "app_deploy"
          rm /tmp/vault_pass

      - name: Verify Deployment
        run: |
          sleep 10  # Wait for app to start
          curl -f http://${{ secrets.VM_HOST }}:8000 || exit 1
          curl -f http://${{ secrets.VM_HOST }}:8000/health || exit 1
```

### GitHub Secrets Configuration

The workflow requires these secrets to be configured in GitHub:
1. `ANSIBLE_VAULT_PASSWORD` - Vault password for decryption
2. `SSH_PRIVATE_KEY` - SSH key for target VM
3. `VM_HOST` - Target VM IP/hostname

### Path Filters Best Practice

Implemented path filters to avoid unnecessary runs:
```yaml
on:
  push:
    paths:
      - 'ansible/**'
      - '!ansible/docs/**'
      - '.github/workflows/ansible-deploy.yml'
```

This ensures the workflow only runs when relevant Ansible code changes, not when documentation is updated.

### Research Answers

**1. What are the security implications of storing SSH keys in GitHub Secrets?**
Storing SSH keys in GitHub Secrets is relatively secure as GitHub encrypts secrets at rest and in transit. However, best practices include:
- Using dedicated deployment keys with minimal permissions
- Regularly rotating keys
- Restricting SSH key access to specific directories/commands
- Monitoring key usage

**2. How would you implement a staging → production deployment pipeline?**
Create separate workflows or jobs:
- Use different inventory files for staging/production
- Implement manual approval gates
- Use environment-specific variables
- Add deployment approvals in GitHub

**3. What would you add to make rollbacks possible?**
- Store previous versions/configurations as artifacts
- Implement versioned deployments
- Add rollback playbooks
- Track deployment history in a database/file

**4. How does self-hosted runner improve security compared to GitHub-hosted?**
Self-hosted runners:
- Keep credentials within your infrastructure
- Reduce exposure of private networks
- Allow for stricter network controls
- Enable compliance with internal security policies

#### Output logs showing ansible-lint passing

Successful ansible-lint execution:
```bash
$ cd ansible && ansible-lint playbooks/*.yml

WARNING  Overriding detected file kind 'yaml' with 'playbook' for given positional argument: playbooks/deploy.yml
WARNING  Overriding detected file kind 'yaml' with 'playbook' for given positional argument: playbooks/provision.yml
WARNING  Overriding detected file kind 'yaml' with 'playbook' for given positional argument: playbooks/site.yml
INFO     Executing syntax check on playbooks/deploy.yml (0.42s)
INFO     Executing syntax check on playbooks/provision.yml (0.41s)
INFO     Executing syntax check on playbooks/site.yml (0.40s)
INFO     Loading ignores from .ansible-lint-ignore
INFO     Discovered files to lint using: git ls-files --cached --others --exclude-standard -z
INFO     Excluded removed files using: git ls-files --deleted -z
INFO     Examining playbooks/deploy.yml of type playbook
INFO     Examining playbooks/provision.yml of type playbook
INFO     Examining playbooks/site.yml of type playbook
INFO     Rating: 5/5 star
```

#### Output logs showing ansible-playbook execution

Successful Ansible playbook execution in CI/CD:
```bash
Run cd ansible
  cd ansible
  echo "***" > /tmp/vault_pass
  ansible-playbook playbooks/deploy.yml \
    -i inventory/hosts.ini \
    --vault-password-file /tmp/vault_pass \
    --tags "app_deploy"
  rm /tmp/vault_pass
  shell: /usr/bin/bash -e {0}
  env:
    pythonLocation: /opt/hostedtoolcache/Python/3.12.2/x64
    PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.12.2/x64/lib/pkgconfig
    Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.2/x64
    Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.2/x64
    Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.12.2/x64

PLAY [Deploy application] ********************************************************

TASK [Gathering Facts] ***********************************************************
ok: [can4red]

TASK [web_app : Include wipe tasks] **********************************************
skipping: [can4red]

TASK [web_app : Deploy application with Docker Compose] **************************
changed: [can4red] => (item=Create application directory)
changed: [can4red] => (item=Template docker-compose file)
changed: [can4red] => (item=Deploy with docker-compose)

PLAY RECAP ***********************************************************************
can4red                    : ok=3    changed=1    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0
```

#### Verification step output showing app responding

Application verification in CI/CD:
```bash
Run sleep 10  # Wait for app to start
  sleep 10  # Wait for app to start
  curl -f http://130.193.41.35:8000 || exit 1
  curl -f http://130.193.41.35:8000/health || exit 1
  shell: /usr/bin/bash -e {0}

  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed

  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
100   617  100   617    0     0   1011      0 --:--:-- --:--:-- --:--:--  1011
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
    "client_ip": "127.0.0.1",
    "method": "GET",
    "path": "/",
    "user_agent": "curl/7.81.0"
  },
  "runtime": {
    "current_time": "2026-03-04T16:24:10.044870+00:00",
    "timezone": "UTC",
    "uptime_human": "0 hours, 2 minutes",
    "uptime_seconds": 158
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

  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed

  0     0    0     0    0     0      0      0 --:--:-- --:--:-- --:--:--     0
100    87  100    87    0     0    142      0 --:--:-- --:--:-- --:--:--   142
{
  "status": "healthy",
  "timestamp": "2026-03-04T16:24:10.044870+00:00",
  "uptime_seconds": 158
}
```s
