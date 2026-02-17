"""Lab 4 Pulumi implementation for Yandex Cloud"""

import pulumi
import pulumi_yandex as yandex
import os

# Configuration
config = pulumi.Config()

# Get values from config or use defaults
yc_token = config.require_secret("yc_token")
yc_cloud_id = config.require("yc_cloud_id")
yc_folder_id = config.require("yc_folder_id")
yc_zone = config.get("yc_zone") or "ru-central1-b"

vm_name = config.get("vm_name") or "can4red"
vm_username = config.get("vm_username") or "can4red"
ssh_public_key_path = config.get("ssh_public_key_path") or "~/.ssh/ssh-key-1771345093196.pub"

instance_cores = config.get_int("instance_cores") or 2
core_fraction = config.get_int("core_fraction") or 20
instance_memory = config.get_int("instance_memory") or 2
disk_size = config.get_int("disk_size") or 20
disk_type = config.get("disk_type") or "network-hdd"

# Read SSH public key
expanded_ssh_path = os.path.expanduser(ssh_public_key_path)
with open(expanded_ssh_path, 'r') as f:
    ssh_public_key = f.read().strip()

# Create provider
provider = yandex.Provider(
    "yandex-provider",
    token=yc_token,
    cloud_id=yc_cloud_id,
    folder_id=yc_folder_id,
    zone=yc_zone
)

# Create network
network = yandex.VpcNetwork(
    "can4red-network",
    name="can4red-network",
    opts=pulumi.ResourceOptions(provider=provider)
)

# Create subnet
subnet = yandex.VpcSubnet(
    "can4red-subnet",
    name="can4red-subnet",
    zone=yc_zone,
    network_id=network.id,
    v4_cidr_blocks=["10.10.0.0/24"],
    opts=pulumi.ResourceOptions(provider=provider)
)

# Create security group
security_group = yandex.VpcSecurityGroup(
    "can4red-security-group",
    name="can4red-security-group",
    network_id=network.id,
    rules=[
        yandex.VpcSecurityGroupRuleArgs(
            description="SSH",
            direction="ingress",
            port=22,
            protocol="TCP",
            v4_cidr_blocks=["0.0.0.0/0"]
        ),
        yandex.VpcSecurityGroupRuleArgs(
            description="HTTP",
            direction="ingress",
            port=80,
            protocol="TCP",
            v4_cidr_blocks=["0.0.0.0/0"]
        ),
        yandex.VpcSecurityGroupRuleArgs(
            description="Custom application port",
            direction="ingress",
            port=5000,
            protocol="TCP",
            v4_cidr_blocks=["0.0.0.0/0"]
        ),
        yandex.VpcSecurityGroupRuleArgs(
            description="All outgoing traffic",
            direction="egress",
            protocol="ANY",
            v4_cidr_blocks=["0.0.0.0/0"]
        )
    ],
    opts=pulumi.ResourceOptions(provider=provider)
)

# Create virtual machine
vm = yandex.ComputeInstance(
    "can4red",
    name=vm_name,
    platform_id="standard-v2",
    zone=yc_zone,
    resources=yandex.ComputeInstanceResourcesArgs(
        cores=instance_cores,
        core_fraction=core_fraction,
        memory=instance_memory
    ),
    boot_disk=yandex.ComputeInstanceBootDiskArgs(
        initialize_params=yandex.ComputeInstanceBootDiskInitializeParamsArgs(
            image_id="fd8073pi3afqvtb46mu5",  # Ubuntu 22.04 LTS
            type=disk_type,
            size=disk_size
        )
    ),
    network_interfaces=[
        yandex.ComputeInstanceNetworkInterfaceArgs(
            subnet_id=subnet.id,
            nat=True,
            security_group_ids=[security_group.id]
        )
    ],
    metadata={
        "ssh-keys": f"{vm_username}:{ssh_public_key}"
    },
    labels={
        "environment": "lab4",
        "purpose": "devops-course"
    },
    opts=pulumi.ResourceOptions(provider=provider)
)

# Export outputs
pulumi.export("vm_name", vm.name)
pulumi.export("vm_external_ip", vm.network_interfaces[0].nat_ip_address)
pulumi.export("vm_internal_ip", vm.network_interfaces[0].ip_address)
pulumi.export("ssh_connection_string", pulumi.Output.concat("ssh ", vm_username, "@", vm.network_interfaces[0].nat_ip_address))
pulumi.export("network_name", network.name)
pulumi.export("subnet_name", subnet.name)
pulumi.export("security_group_name", security_group.name)
