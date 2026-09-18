locals {
  name_suffix        = substr(sha256(var.compartment_id), 0, 8)
  dynamic_group_name = "${var.project_slug}-ci-${local.name_suffix}"
  tags = merge(var.extra_freeform_tags, {
    "environment"         = "sandbox"
    "expires-at"          = var.expires_at
    "managed-by"          = "terraform"
    "oci-founder-toolkit" = "container-api-0.2-preview"
    "owner"               = var.owner
    "project"             = var.project_slug
  })
}

resource "oci_artifacts_container_repository" "api" {
  provider = oci.target

  compartment_id = var.compartment_id
  display_name   = var.repository_name
  is_immutable   = true
  is_public      = false
  freeform_tags  = local.tags
}

resource "oci_identity_dynamic_group" "container_instances" {
  compartment_id = var.tenancy_ocid
  name           = local.dynamic_group_name
  description    = "Sandbox Container Instances for ${var.project_slug}; managed by OCI Founder Toolkit"
  matching_rule  = "ALL {resource.type='computecontainerinstance', resource.compartment.id='${var.compartment_id}'}"
  freeform_tags  = local.tags
}

resource "oci_identity_policy" "container_instances_pull" {
  compartment_id = var.tenancy_ocid
  name           = "${var.project_slug}-ci-pull-${local.name_suffix}"
  description    = "Permit only the project Container Instance resource principals to pull private OCIR images"
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.container_instances.name} to read repos in compartment id ${var.compartment_id} where target.repo.name = '${var.repository_name}'",
  ]
  freeform_tags = local.tags
}

resource "oci_budget_budget" "sandbox" {
  compartment_id = var.tenancy_ocid
  amount         = var.monthly_budget_amount
  reset_period   = "MONTHLY"
  target_type    = "COMPARTMENT"
  targets        = [var.compartment_id]
  display_name   = "${var.project_slug}-sandbox-monthly"
  description    = "Alert-only sandbox budget for ${var.project_slug}; not a hard spending cap"
  freeform_tags  = local.tags

  lifecycle {
    precondition {
      condition     = var.budget_target_verified_without_existing_budget
      error_message = "The preview creates the compartment budget and requires a read-only preflight proving no budget already targets this compartment."
    }
  }
}

resource "oci_budget_alert_rule" "actual" {
  budget_id      = oci_budget_budget.sandbox.id
  threshold      = var.budget_alert_percentage
  threshold_type = "PERCENTAGE"
  type           = "ACTUAL"
  display_name   = "${var.project_slug}-actual-spend"
  description    = "Notify when actual sandbox spend crosses the configured percentage"
  message        = "OCI Founder sandbox budget threshold reached. Review resources and expiry tags."
  recipients     = var.budget_recipients
  freeform_tags  = local.tags
}
