output "repository_id" {
  description = "OCID of the private, immutable OCIR repository."
  value       = oci_artifacts_container_repository.api.id
}

output "repository_path" {
  description = "Repository path without image tag or digest."
  value       = "${var.ocir_registry_endpoint}/${oci_artifacts_container_repository.api.namespace}/${oci_artifacts_container_repository.api.display_name}"
}

output "dynamic_group_id" {
  description = "OCID of the Container Instance resource-principal dynamic group."
  value       = oci_identity_dynamic_group.container_instances.id
}

output "image_pull_policy_id" {
  description = "OCID of the least-scope OCIR pull policy."
  value       = oci_identity_policy.container_instances_pull.id
}

output "budget_id" {
  description = "OCID of the alert-only monthly budget."
  value       = oci_budget_budget.sandbox.id
}

output "budget_alert_rule_id" {
  description = "OCID of the actual-spend budget rule."
  value       = oci_budget_alert_rule.actual.id
}
