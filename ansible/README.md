# Ansible Infrastructure Automation

This directory contains Ansible playbooks and roles for provisioning and deploying the DevOps course application.

## Project Structure

```
ansible/
├── ansible.cfg                 # Ansible configuration
├── .gitignore                  # Git ignore file
├── inventory/
│   ├── hosts.ini              # Static inventory (example)
│   └── yandexcloud.yml        # Dynamic inventory for Yandex Cloud
├── group_vars/
│   └── all.yml                # Placeholder variables (documentation)
├── roles/
│   ├── common/                # Common system setup
│   ├── docker/                # Docker installation
│   └── app_deploy/            # Application deployment
├── playbooks/
│   ├── site.yml               # Main playbook
│   ├── provision.yml          # System provisioning
│   └── deploy.yml             # Application deployment
└── docs/
    └── LAB05.md               # Lab 5 documentation
```

## Setup Instructions

### 1. Install Ansible
```bash
# On macOS
brew install ansible

# On Ubuntu/Debian
sudo apt update
sudo apt install ansible
```

### 2. Install Yandex Cloud Collection (for dynamic inventory)
```bash
ansible-galaxy collection install yandex.cloud
```

### 3. Set Up Credentials

#### For Yandex Cloud Dynamic Inventory:
Export your Yandex Cloud credentials as environment variables:
```bash
export YC_TOKEN=your_yandex_oauth_token
export YC_CLOUD_ID=your_cloud_id
export YC_FOLDER_ID=your_folder_id
```

#### For Docker Hub (Application Deployment):
Create an encrypted vault file:
```bash
ansible-vault create group_vars/all.yml
```

Add your Docker Hub credentials to the vault file:
```yaml
---
# Docker Hub credentials
dockerhub_username: your_actual_dockerhub_username
dockerhub_password: your_dockerhub_access_token

# Application configuration
app_name: devops-app
docker_image: "{{ dockerhub_username }}/{{ app_name }}"
docker_image_tag: latest
app_port: 5000
app_container_name: "{{ app_name }}"
```

When running playbooks, you'll be prompted for the vault password:
```bash
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```

### 4. Update Inventory (if not using dynamic inventory)
Edit `inventory/hosts.ini` with your VM details:
```ini
[webservers]
your-vm-name ansible_host=YOUR_VM_IP ansible_user=your_username
```

## Usage

### Provision System (install Docker, common packages)
```bash
ansible-playbook playbooks/provision.yml
```

### Deploy Application
```bash
ansible-playbook playbooks/deploy.yml
```

### Run Both Provisioning and Deployment
```bash
ansible-playbook playbooks/site.yml
```

### Test Dynamic Inventory
```bash
# Show inventory structure
ansible-inventory --graph

# Show detailed inventory
ansible-inventory --list

# Test connectivity
ansible all -m ping
```

## Security Notes

- Never commit actual credentials to version control
- Use `ansible-vault` to encrypt sensitive data
- Use Docker Hub access tokens instead of passwords
- When using vault password files, ensure they are properly protected and excluded from version control
