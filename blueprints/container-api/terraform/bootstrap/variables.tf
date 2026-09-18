variable "tenancy_ocid" {
  description = "OCID of the tenancy. This stack intentionally needs tenancy-level IAM authority."
  type        = string

  validation {
    condition     = startswith(var.tenancy_ocid, "ocid1.tenancy.")
    error_message = "tenancy_ocid must be a tenancy OCID."
  }
}

variable "compartment_id" {
  description = "Existing non-root sandbox compartment that will own the workload and OCIR repository."
  type        = string

  validation {
    condition     = startswith(var.compartment_id, "ocid1.compartment.") && var.compartment_id != var.tenancy_ocid
    error_message = "compartment_id must be a non-root compartment OCID."
  }
}

variable "home_region" {
  description = "Tenancy home region used for IAM and budget resources."
  type        = string
}

variable "target_region" {
  description = "Region that will hold the OCIR repository and runtime."
  type        = string
}

variable "oci_profile" {
  description = "Name of an already configured OCI CLI profile; credentials never enter Terraform variables."
  type        = string
  default     = "DEFAULT"
}

variable "project_slug" {
  description = "Stable lowercase identifier used in resource names."
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,23}$", var.project_slug))
    error_message = "project_slug must be 3-24 lowercase alphanumeric or hyphen characters and start with a letter."
  }
}

variable "owner" {
  description = "Non-secret owner label for cost and teardown accountability."
  type        = string

  validation {
    condition     = length(trimspace(var.owner)) > 0 && length(var.owner) <= 100
    error_message = "owner must be a non-empty label of at most 100 characters."
  }
}

variable "expires_at" {
  description = "RFC 3339 sandbox review/expiry timestamp stored as a tag. It does not delete resources automatically."
  type        = string

  validation {
    condition     = can(regex("^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$", var.expires_at))
    error_message = "expires_at must use UTC RFC 3339 form, for example 2026-10-01T00:00:00Z."
  }
}

variable "repository_name" {
  description = "OCIR repository display name; nested names such as project/api are allowed."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9._/-]{1,254}$", var.repository_name)) && !strcontains(var.repository_name, "//")
    error_message = "repository_name must be 2-255 lowercase repository characters without empty path segments."
  }
}

variable "ocir_registry_endpoint" {
  description = "Realm-correct OCIR registry hostname without scheme, for example gru.ocir.io."
  type        = string

  validation {
    condition     = !strcontains(var.ocir_registry_endpoint, "://") && !strcontains(var.ocir_registry_endpoint, "/")
    error_message = "ocir_registry_endpoint must be a hostname without scheme or path."
  }
}

variable "monthly_budget_amount" {
  description = "Monthly alert budget in the tenancy rate-card currency. This is an alert, never a spending cap."
  type        = number

  validation {
    condition     = var.monthly_budget_amount > 0
    error_message = "monthly_budget_amount must be greater than zero."
  }
}

variable "budget_alert_percentage" {
  description = "Actual-spend percentage that triggers the budget alert."
  type        = number
  default     = 80

  validation {
    condition     = var.budget_alert_percentage > 0 && var.budget_alert_percentage <= 100
    error_message = "budget_alert_percentage must be greater than 0 and at most 100."
  }
}

variable "budget_target_verified_without_existing_budget" {
  description = "Explicit acknowledgement that a read-only preflight found no existing budget targeting the project compartment."
  type        = bool

  validation {
    condition     = var.budget_target_verified_without_existing_budget
    error_message = "Confirm the read-only budget preflight before this preview can create a budget."
  }
}

variable "budget_recipients" {
  description = "Comma-separated budget notification recipients. Keep the generated tfvars file out of Git."
  type        = string

  validation {
    condition     = length(trimspace(var.budget_recipients)) > 3
    error_message = "budget_recipients must contain at least one notification recipient."
  }
}

variable "extra_freeform_tags" {
  description = "Additional non-secret free-form tags. Mandatory toolkit tags take precedence."
  type        = map(string)
  default     = {}
}
