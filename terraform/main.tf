terraform {
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = "~> 0.76"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }
  }
}

provider "yandex" {
  token     = var.yc_token
  cloud_id  = var.yc_cloud_id
  folder_id = var.yc_folder_id
  zone      = var.yc_zone
}

# Create network
resource "yandex_vpc_network" "can4red_network" {
  name = "can4red-network"
}

# Create subnet
resource "yandex_vpc_subnet" "can4red_subnet" {
  name           = "can4red-subnet"
  zone           = var.yc_zone
  network_id     = yandex_vpc_network.can4red_network.id
  v4_cidr_blocks = ["10.10.0.0/24"]
}

# Create security group
resource "yandex_vpc_security_group" "can4red_sg" {
  name       = "can4red-security-group"
  network_id = yandex_vpc_network.can4red_network.id

  # Allow SSH access
  ingress {
    protocol       = "TCP"
    description    = "SSH"
    port           = 22
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow HTTP access
  ingress {
    protocol       = "TCP"
    description    = "HTTP"
    port           = 80
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow custom port 5000
  ingress {
    protocol       = "TCP"
    description    = "Custom application port"
    port           = 5000
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow all outgoing traffic
  egress {
    protocol       = "ANY"
    description    = "All outgoing traffic"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
}

# Read SSH public key
data "local_file" "ssh_public_key" {
  filename = pathexpand(var.ssh_public_key_path)
}

# Create virtual machine
resource "yandex_compute_instance" "can4red" {
  name        = var.vm_name
  platform_id = "standard-v2"
  zone        = var.yc_zone

  resources {
    cores         = var.instance_cores
    core_fraction = var.core_fraction
    memory        = var.instance_memory
  }

  boot_disk {
    initialize_params {
      image_id = "fd8073pi3afqvtb46mu5" # Ubuntu 22.04 LTS
      type     = var.disk_type
      size     = var.disk_size
    }
  }

  network_interface {
    subnet_id          = yandex_vpc_subnet.can4red_subnet.id
    nat                = true
    security_group_ids = [yandex_vpc_security_group.can4red_sg.id]
  }

  metadata = {
    ssh-keys = "${var.vm_username}:${data.local_file.ssh_public_key.content}"
  }

  labels = {
    environment = "lab4"
    purpose     = "devops-course"
  }
}
