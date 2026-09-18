data "oci_identity_availability_domains" "available" {
  compartment_id = var.tenancy_ocid
}

data "oci_core_services" "oracle_services" {
  filter {
    name   = "name"
    values = ["^All .* Services In Oracle Services Network$"]
    regex  = true
  }
}
