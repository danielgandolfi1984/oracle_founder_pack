terraform {
  required_version = "= 1.16.3"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "= 9.2.0"
    }
  }
}

provider "oci" {
  config_file_profile = var.oci_profile
  region              = var.home_region
}

provider "oci" {
  alias               = "target"
  config_file_profile = var.oci_profile
  region              = var.target_region
}
