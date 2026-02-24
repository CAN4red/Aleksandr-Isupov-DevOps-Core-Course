output "vm_name" {
  description = "Virtual machine name"
  value       = yandex_compute_instance.can4red.name
}

output "vm_external_ip" {
  description = "Virtual machine external IP address"
  value       = yandex_compute_instance.can4red.network_interface.0.nat_ip_address
}

output "vm_internal_ip" {
  description = "Virtual machine internal IP address"
  value       = yandex_compute_instance.can4red.network_interface.0.ip_address
}

output "ssh_connection_string" {
  description = "SSH connection string to connect to the VM"
  value       = "ssh ${var.vm_username}@${yandex_compute_instance.can4red.network_interface.0.nat_ip_address}"
}

output "network_name" {
  description = "Network name"
  value       = yandex_vpc_network.can4red_network.name
}

output "subnet_name" {
  description = "Subnet name"
  value       = yandex_vpc_subnet.can4red_subnet.name
}

output "security_group_name" {
  description = "Security group name"
  value       = yandex_vpc_security_group.can4red_sg.name
}
