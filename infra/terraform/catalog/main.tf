terraform {
  required_version = "= 1.16.4"
  required_providers {
    cloudru = { source = "cloudru/cloud", version = "2.1.3" }
  }
  backend "local" { path = "../../../.local/catalog.tfstate" }
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
provider "cloudru" {
  auth_key_id = var.auth_key_id
  auth_secret = var.auth_secret
}
data "cloudru_evolution_compute_flavor_collection" "available" {
  project_id = "d644930d-f129-41bc-a1f2-4715cff2b478"
  page_size  = 1000
}
data "cloudru_evolution_compute_image_collection" "available" {
  project_id = "d644930d-f129-41bc-a1f2-4715cff2b478"
  page_size  = 1000
}
output "flavors" {
  value = [for item in data.cloudru_evolution_compute_flavor_collection.available.flavors : {
    name = item.name, cpu = item.cpu, ram = item.ram, zones = item.zones, oversubscription = item.oversubscription
  } if item.gpu == 0 && item.cpu <= 4 && item.ram >= 4 && item.ram <= 8]
}
output "images" {
  value = [for item in data.cloudru_evolution_compute_image_collection.available.images : {
    name = item.name, display_name = item.display_name, minimum_disk = item.min_disk, zones = item.zones
  } if strcontains(lower(item.name), "ubuntu")]
}
