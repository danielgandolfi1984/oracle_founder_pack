resource "oci_container_instances_container_instance" "api" {
  availability_domain                  = local.availability_domain
  compartment_id                       = var.compartment_id
  display_name                         = "${var.project_slug}-${var.release_id}"
  shape                                = var.container_shape
  container_restart_policy             = "ALWAYS"
  graceful_shutdown_timeout_in_seconds = 30
  freeform_tags                        = local.tags

  shape_config {
    ocpus         = var.ocpus
    memory_in_gbs = var.memory_in_gbs
  }

  containers {
    display_name          = "api"
    image_url             = var.container_image_url
    environment_variables = local.container_environment
    # The sample does not call OCI APIs. Keep workload credentials unavailable to
    # the anonymous application; the Container Instances service still uses its
    # resource identity to pull the private OCIR image.
    is_resource_principal_disabled = true

    health_checks {
      health_check_type        = "HTTP"
      name                     = "healthz"
      path                     = "/healthz"
      port                     = var.container_port
      failure_action           = "KILL"
      initial_delay_in_seconds = 10
      interval_in_seconds      = 30
      timeout_in_seconds       = 5
      failure_threshold        = 3
      success_threshold        = 1
    }

    security_context {
      security_context_type          = "LINUX"
      is_non_root_user_check_enabled = true
      is_root_file_system_readonly   = true
      run_as_user                    = 65532
      run_as_group                   = 65532

      capabilities {
        drop_capabilities = ["ALL"]
      }
    }
  }

  vnics {
    subnet_id             = oci_core_subnet.app.id
    display_name          = "${var.project_slug}-app-vnic"
    is_public_ip_assigned = false
    private_ip            = local.app_private_ip
    nsg_ids               = [oci_core_network_security_group.app.id]
  }

  lifecycle {
    precondition {
      condition = contains(
        data.oci_identity_availability_domains.available.availability_domains[*].name,
        var.availability_domain,
      )
      error_message = "availability_domain is not present in the target tenancy and region."
    }
  }


  # Image resolution and pull occur during create, so the private service and
  # DNS paths must exist before the Container Instance is requested.
  depends_on = [
    oci_core_network_security_group_security_rule.app_to_oracle_services,
    oci_core_network_security_group_security_rule.app_dns_udp,
    oci_core_network_security_group_security_rule.app_dns_tcp,
  ]
}
