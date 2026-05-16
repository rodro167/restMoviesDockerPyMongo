terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
  zone    = var.zone
}

# ─── Firewall: allow SSH and port 4000 from anywhere ────────────────────────
resource "google_compute_firewall" "restmovies_fw" {
  name    = "restmovies-allow-ssh-api"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["22", "4000"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["restmovies"]
}

# ─── VM instance ─────────────────────────────────────────────────────────────
resource "google_compute_instance" "restmovies_vm" {
  name         = var.vm_name
  machine_type = var.machine_type
  zone         = var.zone
  tags         = ["restmovies"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-12"
      size  = 20   # GB
      type  = "pd-standard"
    }
  }

  network_interface {
    network = "default"
    access_config {}   # ephemeral public IP
  }

  # SSH key
  metadata = {
    ssh-keys = "${var.ssh_user}:${file(var.ssh_public_key_path)}"
  }

  # Cloud-init startup script — installs Docker, pulls image, runs compose
  metadata_startup_script = templatefile("${path.module}/startup.sh.tpl", {
    docker_image   = var.docker_image
    jwt_secret_key = var.jwt_secret_key
    mongo_db       = var.mongo_db
    mongo_uri      = "mongodb://mongo:27017/"
    flask_port     = "4000"
  })

  service_account {
    scopes = ["cloud-platform"]
  }
}
