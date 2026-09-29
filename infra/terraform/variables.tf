variable "project_id" {
  type    = string
  default = "d644930d-f129-41bc-a1f2-4715cff2b478"
}
variable "auth_key_id" {
  type      = string
  sensitive = true
  ephemeral = true
}
variable "auth_secret" {
  type      = string
  sensitive = true
  ephemeral = true
}
variable "admin_cidr" {
  type        = string
  description = "Operator public IPv4 address with /32"
  validation {
    condition     = can(cidrnetmask(var.admin_cidr)) && endswith(var.admin_cidr, "/32")
    error_message = "Use a single operator IPv4 address followed by /32."
  }
}
variable "ssh_public_key_path" {
  type    = string
  default = "../../.secrets/id_ed25519.pub"
}
variable "zone" {
  type    = string
  default = "ru.AZ-1"
}
variable "image_name" {
  type    = string
  default = "ubuntu-24.04"
}
variable "control_plane_flavor" {
  type    = string
  default = "gen-2-4"
}
variable "worker_flavor" {
  type    = string
  default = "gen-4-8"
}
variable "worker_count" {
  type    = number
  default = 1
  validation {
    condition     = var.worker_count >= 1 && var.worker_count <= 2 && floor(var.worker_count) == var.worker_count
    error_message = "The initial playground supports one or two workers."
  }
}
