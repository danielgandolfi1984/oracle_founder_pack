resource "oci_apigateway_gateway" "api" {
  compartment_id             = var.compartment_id
  endpoint_type              = var.gateway_endpoint_type
  subnet_id                  = oci_core_subnet.gateway.id
  network_security_group_ids = [oci_core_network_security_group.gateway.id]
  display_name               = "${var.project_slug}-gateway"
  ip_mode                    = "IPV4"
  freeform_tags              = local.tags
}

resource "oci_apigateway_deployment" "api" {
  compartment_id = var.compartment_id
  gateway_id     = oci_apigateway_gateway.api.id
  path_prefix    = var.api_path_prefix
  display_name   = "${var.project_slug}-${var.release_id}"
  freeform_tags  = local.tags

  specification {
    request_policies {
      rate_limiting {
        rate_in_requests_per_second = var.rate_limit_requests_per_second
        rate_key                    = "CLIENT_IP"
      }
    }

    routes {
      path    = "/"
      methods = ["GET"]
      backend {
        type                       = "HTTP_BACKEND"
        url                        = "http://${local.app_private_ip}:${var.container_port}/"
        connect_timeout_in_seconds = 5
        read_timeout_in_seconds    = 15
        send_timeout_in_seconds    = 15
      }
    }

    routes {
      path    = "/healthz"
      methods = ["GET"]
      backend {
        type                       = "HTTP_BACKEND"
        url                        = "http://${local.app_private_ip}:${var.container_port}/healthz"
        connect_timeout_in_seconds = 5
        read_timeout_in_seconds    = 15
        send_timeout_in_seconds    = 15
      }
    }

    routes {
      path    = "/readyz"
      methods = ["GET"]
      backend {
        type                       = "HTTP_BACKEND"
        url                        = "http://${local.app_private_ip}:${var.container_port}/readyz"
        connect_timeout_in_seconds = 5
        read_timeout_in_seconds    = 15
        send_timeout_in_seconds    = 15
      }
    }
  }

  depends_on = [oci_container_instances_container_instance.api]
}
