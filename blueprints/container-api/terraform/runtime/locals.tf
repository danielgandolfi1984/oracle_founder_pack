locals {
  availability_domain = var.availability_domain
  app_private_ip      = cidrhost(var.app_subnet_cidr, 10)
  public_gateway      = var.gateway_endpoint_type == "PUBLIC"
  dns_label           = substr(replace(var.project_slug, "-", ""), 0, 15)
  tags = merge(var.extra_freeform_tags, {
    "environment"         = var.environment_class
    "expires-at"          = var.expires_at
    "managed-by"          = "terraform"
    "oci-founder-toolkit" = "container-api-0.2-preview"
    "owner"               = var.owner
    "project"             = var.project_slug
    "release"             = var.release_id
  })
  container_environment = merge(var.environment_variables, {
    "OCI_FOUNDER_RELEASE" = var.release_id
    "PORT"                = tostring(var.container_port)
  })
}
