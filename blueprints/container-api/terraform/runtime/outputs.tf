output "endpoint" {
  description = "Base HTTPS endpoint for the sample API."
  value       = "https://${oci_apigateway_gateway.api.hostname}${oci_apigateway_deployment.api.path_prefix}"
}

output "healthcheck_url" {
  description = "Health endpoint used by the smoke contract."
  value       = "https://${oci_apigateway_gateway.api.hostname}${oci_apigateway_deployment.api.path_prefix}/healthz"
}

output "gateway_endpoint_type" {
  value = var.gateway_endpoint_type
}

output "container_image_url" {
  description = "Immutable image reference deployed to the Container Instance."
  value       = var.container_image_url
}

output "container_instance_id" {
  value = oci_container_instances_container_instance.api.id
}

output "container_id" {
  value = oci_container_instances_container_instance.api.containers[0].container_id
}

output "container_vnic_id" {
  value = oci_container_instances_container_instance.api.vnics[0].vnic_id
}

output "gateway_id" {
  value = oci_apigateway_gateway.api.id
}

output "deployment_id" {
  value = oci_apigateway_deployment.api.id
}

output "log_group_id" {
  value = oci_logging_log_group.api.id
}

output "gateway_access_log_id" {
  value = oci_logging_log.gateway_access.id
}

output "gateway_execution_log_id" {
  value = oci_logging_log.gateway_execution.id
}

output "notification_topic_id" {
  value = oci_ons_notification_topic.alarms.id
}

output "notification_subscription_id" {
  value = oci_ons_subscription.email.id
}

output "notification_subscription_state" {
  description = "Must become ACTIVE after the email recipient confirms the subscription."
  value       = oci_ons_subscription.email.state
}

output "cpu_alarm_id" {
  value = oci_monitoring_alarm.high_cpu.id
}

output "memory_alarm_id" {
  value = oci_monitoring_alarm.high_memory.id
}
