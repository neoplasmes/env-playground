terraform {
  required_version = "= 1.16.4"
  required_providers {
    cloudru = {
      source  = "cloudru/cloud"
      version = "= 2.1.3"
    }
  }
  backend "local" {
    path = "../../.local/terraform.tfstate"
  }
}

provider "cloudru" {
  project_id  = var.project_id
  auth_key_id = var.auth_key_id
  auth_secret = var.auth_secret
}
