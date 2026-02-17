variable "yc_token" {
  description = "Yandex Cloud OAuth token"
  type        = string
  sensitive   = true
}

variable "yc_cloud_id" {
  description = "Yandex Cloud ID"
  type        = string
}

variable "yc_folder_id" {
  description = "Yandex Folder ID"
  type        = string
}

variable "yc_zone" {
  description = "Yandex Cloud zone"
  type        = string
  default     = "ru-central1-b"
}

variable "vm_name" {
  description = "Virtual machine name"
  type        = string
  default     = "can4red"
}

variable "vm_username" {
  description = "Username for SSH access"
  type        = string
  default     = "can4red"
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key"
  type        = string
  default     = "~/.ssh/ssh-key-1771345093196.pub"
}

variable "instance_cores" {
  description = "Number of CPU cores"
  type        = number
  default     = 2
}

variable "core_fraction" {
  description = "Core fraction (percentage of CPU performance)"
  type        = number
  default     = 20
}

variable "instance_memory" {
  description = "Memory in GB"
  type        = number
  default     = 2
}

variable "disk_size" {
  description = "Disk size in GB"
  type        = number
  default     = 20
}

variable "disk_type" {
  description = "Disk type"
  type        = string
  default     = "network-hdd"
}
