output "nodes" {
  value = { for key, vm in cloudru_evolution_compute_vm.nodes : key => {
    id         = vm.id
    public_ip  = cloudru_evolution_compute_external_ip.nodes[key].ip_address
    private_ip = cloudru_evolution_compute_interface.nodes[key].ip_address
  } }
}
output "base_domain" {
  value = "${replace(cloudru_evolution_compute_external_ip.nodes["control"].ip_address, ".", "-")}.sslip.io"
}
output "ci_url" {
  value = "https://ci.${replace(cloudru_evolution_compute_external_ip.nodes["control"].ip_address, ".", "-")}.sslip.io"
}
