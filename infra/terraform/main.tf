locals {
  nodes = merge(
    { control = { flavor = var.control_plane_flavor, disk_gb = 30 } },
    { for i in range(var.worker_count) : "worker-${i + 1}" => { flavor = var.worker_flavor, disk_gb = 50 } }
  )
  subnet_cidr = "10.72.0.0/24"
  rules = {
    ssh          = { direction = "INGRESS", protocol = "TCP", ports = "22:22", cidr = var.admin_cidr }
    api          = { direction = "INGRESS", protocol = "TCP", ports = "6443:6443", cidr = var.admin_cidr }
    http         = { direction = "INGRESS", protocol = "TCP", ports = "80:80", cidr = "0.0.0.0/0" }
    https        = { direction = "INGRESS", protocol = "TCP", ports = "443:443", cidr = "0.0.0.0/0" }
    cluster_tcp  = { direction = "INGRESS", protocol = "TCP", ports = "1:65535", cidr = local.subnet_cidr }
    cluster_udp  = { direction = "INGRESS", protocol = "UDP", ports = "1:65535", cidr = local.subnet_cidr }
    outbound_tcp = { direction = "EGRESS", protocol = "TCP", ports = "1:65535", cidr = "0.0.0.0/0" }
    outbound_udp = { direction = "EGRESS", protocol = "UDP", ports = "1:65535", cidr = "0.0.0.0/0" }
  }
}

data "cloudru_evolution_compute_image_collection" "images" {
  project_id = var.project_id
  page_size  = 1000
}

resource "cloudru_evolution_vpc_vpc" "playground" {
  project_id = var.project_id
  name       = "env-playground"
}
resource "cloudru_evolution_compute_subnet" "nodes" {
  project_id     = var.project_id
  name           = "env-playground-nodes"
  zone           = { name = var.zone }
  vpc_id         = cloudru_evolution_vpc_vpc.playground.id
  subnet_address = local.subnet_cidr
  routed_network = true
  default        = false
  dns_servers    = { value = ["1.1.1.1", "8.8.8.8"] }
}
resource "cloudru_evolution_compute_security_group" "nodes" {
  project_id = var.project_id
  name       = "env-playground-nodes"
  zone       = { name = var.zone }
}
resource "cloudru_evolution_compute_security_group_rule" "nodes" {
  for_each          = local.rules
  security_group_id = cloudru_evolution_compute_security_group.nodes.id
  direction         = "TRAFFIC_DIRECTION_${each.value.direction}"
  ether_type        = "ETHER_TYPE_IPV4"
  ip_protocol       = "IP_PROTOCOL_${each.value.protocol}"
  port_range        = each.value.ports
  remote_ip_prefix  = each.value.cidr
}
resource "cloudru_evolution_compute_disk" "boot" {
  for_each   = local.nodes
  project_id = var.project_id
  name       = "env-playground-${each.key}"
  zone       = { name = var.zone }
  size       = each.value.disk_gb
  disk_type  = { name = "SSD" }
  bootable   = true
  image      = { id = one([for image in data.cloudru_evolution_compute_image_collection.images.images : image.id if image.name == var.image_name]) }
  lifecycle {
    precondition {
      condition     = length([for image in data.cloudru_evolution_compute_image_collection.images.images : image.id if image.name == var.image_name]) == 1
      error_message = "Select an unambiguous available image_name from the Evolution image catalog."
    }
  }
}
resource "cloudru_evolution_compute_interface" "nodes" {
  for_each                   = local.nodes
  project_id                 = var.project_id
  name                       = "env-playground-${each.key}"
  zone                       = { name = var.zone }
  subnet                     = { id = cloudru_evolution_compute_subnet.nodes.id }
  security_groups            = [{ id = cloudru_evolution_compute_security_group.nodes.id }]
  interface_security_enabled = true
  type                       = "INTERFACE_TYPE_REGULAR"
}
resource "cloudru_evolution_compute_external_ip" "nodes" {
  for_each          = local.nodes
  project_id        = var.project_id
  name              = "env-playground-${each.key}"
  zone              = { name = var.zone }
  network_interface = { id = cloudru_evolution_compute_interface.nodes[each.key].id }
}
resource "cloudru_evolution_compute_vm" "nodes" {
  for_each           = local.nodes
  project_id         = var.project_id
  name               = "env-playground-${each.key}"
  zone               = { name = var.zone }
  flavor             = { name = each.value.flavor }
  disks              = [{ id = cloudru_evolution_compute_disk.boot[each.key].id }]
  network_interfaces = [{ id = cloudru_evolution_compute_interface.nodes[each.key].id }]
  cloud_init_userdata = base64encode("#cloud-config\n${yamlencode({
    hostname         = "env-playground-${each.key}"
    manage_etc_hosts = true
    ssh_pwauth       = false
    users = [{
      name                = "ubuntu"
      groups              = ["sudo"]
      shell               = "/bin/bash"
      sudo                = ["ALL=(ALL) NOPASSWD:ALL"]
      lock_passwd         = true
      ssh_authorized_keys = [trimspace(file(pathexpand(var.ssh_public_key_path)))]
    }]
    package_update = true
    packages       = ["curl", "ca-certificates"]
  })}")
  depends_on = [cloudru_evolution_compute_security_group_rule.nodes, cloudru_evolution_compute_external_ip.nodes]
}
