variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP zone"
  type        = string
  default     = "us-central1-a"
}

variable "machine_type" {
  description = "GCP VM machine type"
  type        = string
  default     = "e2-small"   # 2 vCPU, 2 GB RAM — enough for Flask + Mongo
}

variable "vm_name" {
  description = "Name of the VM instance"
  type        = string
  default     = "restmovies-vm"
}

variable "ssh_user" {
  description = "SSH username to add to the VM"
  type        = string
  default     = "gcpuser"
}

variable "ssh_public_key_path" {
  description = "Path to your SSH public key file"
  type        = string
  default     = "~/.ssh/google_compute_engine.pub"
}

variable "docker_image" {
  description = "Docker Hub image for the REST API"
  type        = string
  default     = "rodro167/restmovies:latest"
}

variable "jwt_secret_key" {
  description = "JWT secret key for the API (keep this secret)"
  type        = string
  sensitive   = true
}

variable "mongo_db" {
  description = "MongoDB database name"
  type        = string
  default     = "restMovies"
}
