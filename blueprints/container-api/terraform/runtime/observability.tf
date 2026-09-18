resource "oci_logging_log_group" "api" {
  compartment_id = var.compartment_id
  display_name   = "${var.project_slug}-logs"
  description    = "API Gateway service logs for the Container API sandbox"
  freeform_tags  = local.tags
}

resource "oci_logging_log" "gateway_access" {
  display_name       = "${var.project_slug}-gateway-access"
  log_group_id       = oci_logging_log_group.api.id
  log_type           = "SERVICE"
  is_enabled         = true
  retention_duration = 30
  freeform_tags      = local.tags

  configuration {
    compartment_id = var.compartment_id
    source {
      category    = "access"
      resource    = oci_apigateway_deployment.api.id
      service     = var.api_gateway_logging_service_name
      source_type = "OCISERVICE"
    }
  }
}

resource "oci_logging_log" "gateway_execution" {
  display_name       = "${var.project_slug}-gateway-execution"
  log_group_id       = oci_logging_log_group.api.id
  log_type           = "SERVICE"
  is_enabled         = true
  retention_duration = 30
  freeform_tags      = local.tags

  configuration {
    compartment_id = var.compartment_id
    source {
      category    = "execution"
      resource    = oci_apigateway_deployment.api.id
      service     = var.api_gateway_logging_service_name
      source_type = "OCISERVICE"
    }
  }
}

resource "oci_ons_notification_topic" "alarms" {
  compartment_id = var.compartment_id
  name           = "${var.project_slug}-alarms"
  description    = "Container API sandbox alarms"
  freeform_tags  = local.tags
}

resource "oci_ons_subscription" "email" {
  compartment_id = var.compartment_id
  topic_id       = oci_ons_notification_topic.alarms.id
  protocol       = "EMAIL"
  endpoint       = var.notification_email
  freeform_tags  = local.tags
}

resource "oci_monitoring_alarm" "high_cpu" {
  compartment_id        = var.compartment_id
  metric_compartment_id = var.compartment_id
  display_name          = "${var.project_slug}-high-cpu"
  namespace             = "oci_computecontainerinstance"
  query                 = "CpuUtilization[1m]{resourceId = \"${oci_container_instances_container_instance.api.id}\"}.mean() > ${var.cpu_alarm_threshold}"
  severity              = "WARNING"
  is_enabled            = true
  pending_duration      = "PT5M"
  destinations          = [oci_ons_notification_topic.alarms.id]
  body                  = "Sustained high CPU on the Founder Toolkit for OCI sandbox Container Instance."
  freeform_tags         = local.tags
}

resource "oci_monitoring_alarm" "high_memory" {
  compartment_id        = var.compartment_id
  metric_compartment_id = var.compartment_id
  display_name          = "${var.project_slug}-high-memory"
  namespace             = "oci_computecontainerinstance"
  query                 = "MemoryUtilization[1m]{resourceId = \"${oci_container_instances_container_instance.api.id}\"}.mean() > ${var.memory_alarm_threshold}"
  severity              = "WARNING"
  is_enabled            = true
  pending_duration      = "PT5M"
  destinations          = [oci_ons_notification_topic.alarms.id]
  body                  = "Sustained high memory use on the Founder Toolkit for OCI sandbox Container Instance."
  freeform_tags         = local.tags
}
