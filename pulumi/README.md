# Lab 4 - Pulumi Implementation

This directory contains the Pulumi implementation for Lab 4 of the DevOps course.

## Prerequisites

- Pulumi CLI installed
- Python 3.x installed
- Yandex Cloud account with appropriate permissions
- SSH key pair for VM access

## Setup

1. Create a Yandex Cloud service account with required permissions
2. Generate an OAuth token for authentication
3. Note your cloud ID and folder ID from Yandex Cloud console

## Configuration

Copy the example configuration file and fill in your values:

```bash
cp Pulumi.dev.yaml.example Pulumi.dev.yaml
```

Then edit `Pulumi.dev.yaml` with your actual values:
- `yc_token`: Your Yandex Cloud OAuth token
- `yc_cloud_id`: Your Yandex Cloud ID
- `yc_folder_id`: Your Yandex Folder ID

## Deployment

1. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

2. Install dependencies (if not already installed):
   ```bash
   pip install -r requirements.txt
   ```

3. Deploy the infrastructure:
   ```bash
   pulumi up
   ```

## Destroy Infrastructure

To tear down the infrastructure:
```bash
pulumi destroy
