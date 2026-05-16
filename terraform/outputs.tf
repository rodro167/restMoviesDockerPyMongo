output "vm_public_ip" {
  description = "Public IP of the VM — use this to reach your API"
  value       = google_compute_instance.restmovies_vm.network_interface[0].access_config[0].nat_ip
}

output "api_url" {
  description = "Base URL of the REST API"
  value       = "http://${google_compute_instance.restmovies_vm.network_interface[0].access_config[0].nat_ip}:4000"
}

output "ssh_command" {
  description = "SSH command to connect to the VM"
  value       = "ssh ${var.ssh_user}@${google_compute_instance.restmovies_vm.network_interface[0].access_config[0].nat_ip}"
}
