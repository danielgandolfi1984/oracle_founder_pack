variable "tenancy_ocid" {
  description = "OCID of the tenancy, used only to discover availability domains."
  type        = string

  validation {
    condition     = startswith(var.tenancy_ocid, "ocid1.tenancy.")
    error_message = "tenancy_ocid must be a tenancy OCID."
  }
}

variable "compartment_id" {
  description = "Existing non-root sandbox compartment for all runtime resources."
  type        = string

  validation {
    condition     = startswith(var.compartment_id, "ocid1.compartment.")
    error_message = "compartment_id must be a compartment OCID."
  }
}

variable "region" {
  description = "OCI region for the sandbox runtime."
  type        = string
}

variable "oci_profile" {
  description = "Name of an already configured OCI CLI profile; credentials never enter Terraform variables."
  type        = string
  default     = "DEFAULT"
}

variable "environment_class" {
  description = "The preview is deliberately sandbox-only."
  type        = string
  default     = "sandbox"

  validation {
    condition     = var.environment_class == "sandbox"
    error_message = "Container API 0.2 preview refuses production environments."
  }
}

variable "project_slug" {
  description = "Stable lowercase identifier used in names and tags."
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,23}$", var.project_slug))
    error_message = "project_slug must be 3-24 lowercase alphanumeric or hyphen characters and start with a letter."
  }
}

variable "release_id" {
  description = "Non-secret release identifier, such as a short source revision."
  type        = string

  validation {
    condition     = can(regex("^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$", var.release_id))
    error_message = "release_id contains unsupported characters or is longer than 64 characters."
  }
}

variable "owner" {
  description = "Non-secret owner label for cost and teardown accountability."
  type        = string
}

variable "expires_at" {
  description = "RFC 3339 sandbox review/expiry timestamp stored as a tag. It does not delete resources automatically."
  type        = string

  validation {
    condition     = can(regex("^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$", var.expires_at))
    error_message = "expires_at must use UTC RFC 3339 form, for example 2026-10-01T00:00:00Z."
  }
}

variable "container_image_url" {
  description = "Immutable OCIR image reference. Tag-only references are rejected."
  type        = string

  validation {
    condition = (
      can(regex("@sha256:[0-9a-f]{64}$", var.container_image_url)) &&
      startswith(var.container_image_url, "${var.approved_repository_path}@sha256:")
    )
    error_message = "container_image_url must use approved_repository_path and end in an immutable lowercase sha256 digest."
  }
}

variable "approved_repository_path" {
  description = "Exact repository_path from the reviewed bootstrap output, without tag or digest."
  type        = string

  validation {
    condition = (
      !strcontains(var.approved_repository_path, "://") &&
      !strcontains(var.approved_repository_path, "@") &&
      can(regex("^[A-Za-z0-9.-]+/[A-Za-z0-9._/-]+$", var.approved_repository_path))
    )
    error_message = "approved_repository_path must be the bootstrap repository path without scheme, tag, or digest."
  }
}

variable "availability_domain" {
  description = "Explicit availability domain selected after checking target-region shape capacity."
  type        = string

  validation {
    condition     = length(trimspace(var.availability_domain)) > 0
    error_message = "availability_domain must be selected explicitly."
  }
}

variable "container_shape" {
  description = "Current Container Instance shape selected after checking regional capacity."
  type        = string
  default     = "CI.Standard.E4.Flex"
}

variable "ocpus" {
  description = "OCPUs allocated to the single sandbox Container Instance."
  type        = number
  default     = 1

  validation {
    condition     = var.ocpus > 0
    error_message = "ocpus must be greater than zero."
  }
}

variable "memory_in_gbs" {
  description = "Memory in GB allocated to the single sandbox Container Instance."
  type        = number
  default     = 2

  validation {
    condition     = var.memory_in_gbs > 0
    error_message = "memory_in_gbs must be greater than zero."
  }
}

variable "container_port" {
  description = "HTTP port exposed inside the VCN."
  type        = number
  default     = 8080

  validation {
    condition     = var.container_port >= 1024 && var.container_port <= 65535
    error_message = "container_port must be an unprivileged TCP port between 1024 and 65535."
  }
}

variable "environment_variables" {
  description = "Non-secret application environment variables. Secret-like names are rejected."
  type        = map(string)
  default     = {}

  validation {
    condition = alltrue([
      for name in keys(var.environment_variables) :
      length(regexall("(secret|password|passwd|token|api[_-]?key|private[_-]?key)", lower(name))) == 0
    ])
    error_message = "environment_variables must not contain secret-like names; use a runtime secret retrieval design instead."
  }
}

variable "vcn_cidr" {
  description = "IPv4 CIDR for the dedicated sandbox VCN."
  type        = string
  default     = "10.42.0.0/16"
}

variable "gateway_subnet_cidr" {
  description = "IPv4 CIDR for the regional API Gateway subnet."
  type        = string
  default     = "10.42.0.0/24"
}

variable "app_subnet_cidr" {
  description = "IPv4 CIDR for the private Container Instance subnet."
  type        = string
  default     = "10.42.1.0/24"
}

variable "gateway_endpoint_type" {
  description = "PUBLIC or PRIVATE. There is intentionally no default because exposure is a founder decision."
  type        = string

  validation {
    condition     = contains(["PUBLIC", "PRIVATE"], var.gateway_endpoint_type)
    error_message = "gateway_endpoint_type must be PUBLIC or PRIVATE."
  }
}

variable "allowed_ingress_cidrs" {
  description = "Explicit IPv4 sources allowed to reach API Gateway on TCP 443."
  type        = list(string)

  validation {
    condition     = length(var.allowed_ingress_cidrs) > 0 && alltrue([for cidr in var.allowed_ingress_cidrs : can(cidrnetmask(cidr))])
    error_message = "allowed_ingress_cidrs must contain at least one valid IPv4 CIDR."
  }
}

variable "api_path_prefix" {
  description = "Prefix under which the three sample routes are published."
  type        = string
  default     = "/api"

  validation {
    condition     = can(regex("^/[A-Za-z0-9._~-]+$", var.api_path_prefix))
    error_message = "api_path_prefix must be a single non-root URL path segment beginning with /."
  }
}

variable "rate_limit_requests_per_second" {
  description = "Per-client API Gateway rate limit for the anonymous sandbox endpoint."
  type        = number
  default     = 10

  validation {
    condition     = var.rate_limit_requests_per_second > 0
    error_message = "rate_limit_requests_per_second must be greater than zero."
  }
}

variable "notification_email" {
  description = "Email endpoint for alarm notifications. OCI requires the recipient to confirm the subscription."
  type        = string

  validation {
    condition     = can(regex("^[^@[:space:]]+@[^@[:space:]]+\\.[^@[:space:]]+$", var.notification_email))
    error_message = "notification_email must look like an email address."
  }
}

variable "api_gateway_logging_service_name" {
  description = "Logging service identifier discovered in the target region; currently expected to be apigateway."
  type        = string
  default     = "apigateway"

  validation {
    condition     = length(trimspace(var.api_gateway_logging_service_name)) > 0
    error_message = "api_gateway_logging_service_name must not be empty."
  }
}

variable "cpu_alarm_threshold" {
  description = "Mean CPU utilization percentage that triggers a warning after five minutes."
  type        = number
  default     = 80

  validation {
    condition     = var.cpu_alarm_threshold > 0 && var.cpu_alarm_threshold <= 100
    error_message = "cpu_alarm_threshold must be greater than 0 and at most 100."
  }
}

variable "memory_alarm_threshold" {
  description = "Mean memory utilization percentage that triggers a warning after five minutes."
  type        = number
  default     = 85

  validation {
    condition     = var.memory_alarm_threshold > 0 && var.memory_alarm_threshold <= 100
    error_message = "memory_alarm_threshold must be greater than 0 and at most 100."
  }
}

variable "extra_freeform_tags" {
  description = "Additional non-secret free-form tags. Mandatory toolkit tags take precedence."
  type        = map(string)
  default     = {}
}
