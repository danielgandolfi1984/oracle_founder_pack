# Founder guardrails

Apply these guardrails to plans, generated infrastructure, deployments, and operational recommendations.

## Identity and compartments

- Put workload resources in a project compartment, not the root compartment.
- Keep the tenancy administrator population small and do not use tenancy administrators for daily work.
- Separate human administration from workload authentication.
- Prefer instance principals, resource principals, or workload identity over user API keys in deployed workloads.
- Expose a workload identity inside an application only when it needs OCI APIs and has an exact reviewed policy; platform-managed image pull does not by itself justify giving the app credentials.
- Scope IAM policies to the smallest practical verb, resource family, compartment, and condition.
- Reject `manage all-resources` in stable blueprints.

For a proof of concept, simplicity can be appropriate, but the plan must state which permissions are temporary and how to remove them before production.

## Cost controls

- Create a budget against the project compartment or required tag scope.
- Check for an existing budget on the exact target before creation; do not assume a second target budget is allowed or silently replace one.
- State clearly that budgets are alerting mechanisms, not hard caps.
- Add useful `ACTUAL` thresholds and, after enough usage history exists, consider
  a `FORECAST` rule with a real notification destination. Forecast is an
  extrapolated alert, not a cap or guaranteed bill prediction.
- Use compartment quotas for enforceable resource limits where the service supports them.
- Apply defined or consistent free-form tags for `project`, `environment`, `owner`, `managed-by`, and `expires-at`.
- Validate current pricing, region, shape, limits, and promotional eligibility before estimating cost.
- Explain the workload's cost drivers: active compute, database shape/storage, gateway requests, logs, egress, retained images, backups, and idle resources.

Never promise that an architecture is free or bounded solely because it uses an Always Free-eligible component.

## Networking

- Decide public versus private intentionally for every endpoint.
- Prefer NSGs for workload-level network policy.
- Use narrow ingress sources and ports. Do not use `0.0.0.0/0` for administrative access.
- Keep databases private unless a documented requirement and control set justify otherwise.
- Explain NAT Gateway, Service Gateway, public IP, API Gateway, and Load Balancer costs and traffic paths when used.
- Confirm DNS, TLS certificate ownership, and health-check behavior before exposing production traffic.

## Secrets

- Store deploy-time and runtime secrets in an approved secret manager such as OCI Vault Secret Management.
- Retrieve secrets using a workload identity where supported.
- Never embed secret values in Terraform source, committed variable files, container images, example commands, or deployment receipts.
- Treat Terraform state as sensitive because providers may persist resource attributes.
- Redact secret values from plans, logs, CI output, and support bundles.

## Terraform and delivery

- Pin provider versions according to the repository's update policy and commit the dependency lock file.
- Run `terraform fmt`, initialization with reviewed providers, `terraform validate`, and a plan before apply.
- Store state in a protected backend appropriate to the team stage; do not commit local state.
- Summarize creates, updates, replacements, deletes, IAM changes, public exposure, and estimated cost drivers before approval.
- Bind the summary to the exact saved plan. Do not review arbitrary plan JSON while applying a separately supplied binary plan.
- Before apply, show and confirm the authenticated principal/profile, tenancy, region, target compartment name and OCID, and environment. A correct plan aimed at the wrong tenancy is still a failure.
- Require explicit approval immediately before apply, even if plan generation was already authorized.
- Produce a deployment receipt containing resource identifiers, image digests, code/IaC revision, verification results, plan lineage, and teardown instructions, but no credentials. A local receipt is evidence, not a signed attestation.

## Observability

- Enable the service logs needed to diagnose ingress and workload failures.
- Define metrics for availability, error rate, latency, saturation, and the workload's key transaction.
- Route alarms through Notifications to a destination that is actually monitored.
- Set retention deliberately; logging volume and retention are cost drivers.
- Preserve correlation identifiers across gateway, function/container, and downstream calls.

## Mutation levels

| Level | Examples | Required behavior |
|---|---|---|
| Read-only | Inspect repository, list resources, read logs/metrics, show limits | May proceed within the user's scope; redact sensitive output |
| Generate | Write plan, Terraform, policy proposal, commands | Write files only when the user requested local artifacts; inspect the worktree, preserve existing changes, do not apply, validate, and show diffs |
| Write | IAM update, budget/quota creation, network or workload change, `terraform apply` | Preview exact changes and obtain explicit approval immediately before execution |
| Destructive | Delete resources, revoke access, rotate credentials, `terraform destroy` | Resolve exact targets from state/receipt, preview impact and retained data, then obtain explicit approval |

Authorization for one level does not automatically authorize another.

When routing to another installed skill, pass through the user's constraints and keep these authorization levels, target confirmations, and destructive-operation rules in force. A downstream skill does not expand permission.

## Teardown

- Scope teardown to a reviewed state file and deployment receipt, and compare managed resources separately from read-only Terraform data sources.
- Back up or explicitly waive persistent data before deletion.
- Account for resources often left behind: container images, log groups, buckets/objects, secrets, DNS records, certificates, reserved public IPs, backups, notifications, and state backends.
- Never delete by broad compartment scope, tag query alone, unresolved variable, wildcard, or name prefix.
- Verify post-destroy inventory and report retained resources with their expected cost drivers.

## Sources and claim coverage

- Compartment and IAM boundaries: [IAM tenancy and compartments](https://docs.oracle.com/en-us/iaas/Content/Security/Reference/iam_security_topic-IAM_Tenancy_and_Compartments.htm) and [Securing a tenancy](https://docs.oracle.com/en-us/iaas/Content/Security/Tasks/securing_your_tenancy.htm).
- Budget alert semantics: [Budgets overview](https://docs.oracle.com/en-us/iaas/Content/Billing/Concepts/budgetsoverview.htm).
- Cost-management framework: [OCI cost management](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/era-cost-management.htm).
- Secret storage and lifecycle: [Managing Vault secrets](https://docs.oracle.com/en-us/iaas/Content/secret-management/Concepts/manage-secrets.htm).
- Terraform provider and Resource Manager choices: [Terraform on OCI](https://docs.oracle.com/en-us/iaas/Content/dev/terraform/home.htm).
- Resource Manager runtime compatibility: [Supported Terraform versions](https://docs.oracle.com/en-us/iaas/Content/ResourceManager/Reference/terraformversions.htm).
- Log collection and retention planning: [Logging overview](https://docs.oracle.com/en-us/iaas/Content/Logging/Concepts/loggingoverview.htm).
- Metrics and alarm planning: [Monitoring overview](https://docs.oracle.com/en-us/iaas/Content/Monitoring/Concepts/monitoringoverview.htm).
