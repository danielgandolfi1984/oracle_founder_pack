resource "oci_core_vcn" "sandbox" {
  compartment_id = var.compartment_id
  cidr_blocks    = [var.vcn_cidr]
  display_name   = "${var.project_slug}-vcn"
  dns_label      = local.dns_label
  freeform_tags  = local.tags

  lifecycle {
    precondition {
      condition = (
        can(regex("^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}/(?:[0-9]|[12][0-9]|3[0-2])$", var.vcn_cidr)) &&
        can(regex("^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}/(?:[0-9]|[12][0-9]|3[0-2])$", var.gateway_subnet_cidr)) &&
        can(regex("^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}/(?:[0-9]|[12][0-9]|3[0-2])$", var.app_subnet_cidr)) &&
        can(cidrnetmask(var.vcn_cidr)) &&
        can(cidrnetmask(var.gateway_subnet_cidr)) &&
        can(cidrnetmask(var.app_subnet_cidr)) &&
        can(cidrhost(var.gateway_subnet_cidr, 10)) &&
        can(cidrhost(var.app_subnet_cidr, 10)) &&
        try(tonumber(split("/", var.gateway_subnet_cidr)[1]) <= 24, false) &&
        try(tonumber(split("/", var.app_subnet_cidr)[1]) <= 24, false) &&
        try(cidrcontains(var.vcn_cidr, cidrhost(var.gateway_subnet_cidr, 0)), false) &&
        try(cidrcontains(var.vcn_cidr, cidrhost(var.app_subnet_cidr, 0)), false) &&
        !try(cidrcontains(var.gateway_subnet_cidr, cidrhost(var.app_subnet_cidr, 0)), true) &&
        !try(cidrcontains(var.app_subnet_cidr, cidrhost(var.gateway_subnet_cidr, 0)), true)
      )
      error_message = "network_cidr_contract: gateway and app CIDRs must be valid, non-overlapping IPv4 /24-or-larger subnets contained by vcn_cidr."
    }
  }
}

resource "oci_core_internet_gateway" "public" {
  count = local.public_gateway ? 1 : 0

  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.sandbox.id
  display_name   = "${var.project_slug}-public-igw"
  enabled        = true
  freeform_tags  = local.tags
}

resource "oci_core_service_gateway" "oracle_services" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.sandbox.id
  display_name   = "${var.project_slug}-services-sgw"
  freeform_tags  = local.tags

  services {
    service_id = data.oci_core_services.oracle_services.services[0].id
  }
}

resource "oci_core_route_table" "gateway" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.sandbox.id
  display_name   = "${var.project_slug}-gateway-routes"
  freeform_tags  = local.tags

  dynamic "route_rules" {
    for_each = local.public_gateway ? [1] : []
    content {
      destination       = "0.0.0.0/0"
      destination_type  = "CIDR_BLOCK"
      network_entity_id = oci_core_internet_gateway.public[0].id
      description       = "Public API Gateway ingress and return path"
    }
  }
}

resource "oci_core_route_table" "app" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.sandbox.id
  display_name   = "${var.project_slug}-app-routes"
  freeform_tags  = local.tags

  route_rules {
    destination       = data.oci_core_services.oracle_services.services[0].cidr_block
    destination_type  = "SERVICE_CIDR_BLOCK"
    network_entity_id = oci_core_service_gateway.oracle_services.id
    description       = "Private access to OCIR and Oracle Services Network"
  }
}

resource "oci_core_security_list" "empty" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.sandbox.id
  display_name   = "${var.project_slug}-nsg-only"
  freeform_tags  = local.tags
}

resource "oci_core_subnet" "gateway" {
  compartment_id             = var.compartment_id
  vcn_id                     = oci_core_vcn.sandbox.id
  cidr_block                 = var.gateway_subnet_cidr
  display_name               = "${var.project_slug}-gateway-subnet"
  dns_label                  = "gateway"
  prohibit_public_ip_on_vnic = !local.public_gateway
  route_table_id             = oci_core_route_table.gateway.id
  security_list_ids          = [oci_core_security_list.empty.id]
  freeform_tags              = local.tags
}

resource "oci_core_subnet" "app" {
  compartment_id             = var.compartment_id
  vcn_id                     = oci_core_vcn.sandbox.id
  cidr_block                 = var.app_subnet_cidr
  display_name               = "${var.project_slug}-app-private-subnet"
  dns_label                  = "app"
  prohibit_public_ip_on_vnic = true
  route_table_id             = oci_core_route_table.app.id
  security_list_ids          = [oci_core_security_list.empty.id]
  freeform_tags              = local.tags
}

resource "oci_core_network_security_group" "gateway" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.sandbox.id
  display_name   = "${var.project_slug}-gateway-nsg"
  freeform_tags  = local.tags
}

resource "oci_core_network_security_group" "app" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.sandbox.id
  display_name   = "${var.project_slug}-app-nsg"
  freeform_tags  = local.tags
}

resource "oci_core_network_security_group_security_rule" "gateway_https_ingress" {
  for_each = toset(var.allowed_ingress_cidrs)

  network_security_group_id = oci_core_network_security_group.gateway.id
  direction                 = "INGRESS"
  protocol                  = "6"
  source                    = each.value
  source_type               = "CIDR_BLOCK"
  stateless                 = false
  description               = "Explicit client access to the API Gateway"

  tcp_options {
    destination_port_range {
      min = 443
      max = 443
    }
  }
}

resource "oci_core_network_security_group_security_rule" "gateway_to_app" {
  network_security_group_id = oci_core_network_security_group.gateway.id
  direction                 = "EGRESS"
  protocol                  = "6"
  destination               = oci_core_network_security_group.app.id
  destination_type          = "NETWORK_SECURITY_GROUP"
  stateless                 = false
  description               = "API Gateway to the private HTTP backend"

  tcp_options {
    destination_port_range {
      min = var.container_port
      max = var.container_port
    }
  }
}

resource "oci_core_network_security_group_security_rule" "app_from_gateway" {
  network_security_group_id = oci_core_network_security_group.app.id
  direction                 = "INGRESS"
  protocol                  = "6"
  source                    = oci_core_network_security_group.gateway.id
  source_type               = "NETWORK_SECURITY_GROUP"
  stateless                 = false
  description               = "Only API Gateway can call the private container"

  tcp_options {
    destination_port_range {
      min = var.container_port
      max = var.container_port
    }
  }
}

resource "oci_core_network_security_group_security_rule" "app_to_oracle_services" {
  network_security_group_id = oci_core_network_security_group.app.id
  direction                 = "EGRESS"
  protocol                  = "6"
  destination               = data.oci_core_services.oracle_services.services[0].cidr_block
  destination_type          = "SERVICE_CIDR_BLOCK"
  stateless                 = false
  description               = "HTTPS image pull from OCIR through the Service Gateway"

  tcp_options {
    destination_port_range {
      min = 443
      max = 443
    }
  }
}

resource "oci_core_network_security_group_security_rule" "app_dns_udp" {
  network_security_group_id = oci_core_network_security_group.app.id
  direction                 = "EGRESS"
  protocol                  = "17"
  destination               = "169.254.169.254/32"
  destination_type          = "CIDR_BLOCK"
  stateless                 = false
  description               = "VCN DNS resolver over UDP"

  udp_options {
    destination_port_range {
      min = 53
      max = 53
    }
  }
}

resource "oci_core_network_security_group_security_rule" "app_dns_tcp" {
  network_security_group_id = oci_core_network_security_group.app.id
  direction                 = "EGRESS"
  protocol                  = "6"
  destination               = "169.254.169.254/32"
  destination_type          = "CIDR_BLOCK"
  stateless                 = false
  description               = "VCN DNS resolver over TCP"

  tcp_options {
    destination_port_range {
      min = 53
      max = 53
    }
  }
}
