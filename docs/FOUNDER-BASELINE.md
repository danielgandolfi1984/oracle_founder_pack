# Founder Baseline

This guide is the minimum governance and operating baseline for a founder or
backend developer running a small OCI project. It keeps the first environment
understandable without pretending that a sandbox is production-ready.

The baseline is a design checklist, not evidence that anything exists in OCI.
A resource is **proposed** until an approved change is applied to the confirmed
target. It is **verified** only after the deployed resource and its controls are
checked and recorded in a deployment receipt.

## Baseline, not landing zone

Use the Founder Baseline for a small team, one project boundary, and a limited
number of environments. It establishes a project compartment, intentional
identity and network boundaries, cost signals, observability, and reversible
delivery.

It is not an enterprise landing zone, a compliance certification, or a
production-readiness claim. Graduate to an enterprise landing-zone design when
requirements include multiple independent teams, stronger production and
non-production isolation, regulated controls, centralized policy or security
operations, or multi-region recovery. The
[OCI Core Landing Zone](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/oci-core-landing-zone.htm)
is the relevant starting point for that work.

## What the founder should decide

### 1. Put the project outside the root compartment

- Create or select a dedicated project compartment; do not place routine
  workload resources in the root compartment.
- Record the exact tenancy, region, environment, compartment name, and
  compartment OCID before any apply.
- Keep tenancy administrators few and reserve that access for tasks that truly
  require it. Daily development and deployment should use narrower access.
- Scope policies to the smallest practical verb, resource family, compartment,
  and condition. Do not use `manage all-resources` as a shortcut.

A proof of concept may use temporary permissions, but its plan must identify
them and state how they will be removed before production.

### 2. Separate people from software

Use distinct identity paths:

| Actor | Expected identity | Rule |
|---|---|---|
| Founder or operator | Named human identity with only the required administrative access | Do not use a tenancy administrator for routine work |
| Deployment automation | A reviewed deployment principal or profile | Grant only the resources and operations needed by the delivery path |
| Running workload | Instance principal, resource principal, or workload identity when the application must call OCI APIs | Never distribute a human API key to the workload |

Platform-managed image pull alone does not justify exposing an OCI identity
inside the application. Give a workload identity to application code only when
there is a specific OCI API need and an exact, reviewed policy.

### 3. Treat state and secrets as sensitive

- Keep Terraform state in a protected backend appropriate to the team's stage;
  never commit local state. Providers may persist sensitive resource
  attributes even when source files look harmless.
- Pin reviewed provider versions, commit the dependency lock file, and run
  formatting, initialization, validation, and a saved plan before apply.
- Store deploy-time and runtime secrets in an approved secret manager such as
  OCI Vault Secret Management, then retrieve them with a workload identity
  where supported.
- Never put secret values in Terraform source, committed variable files,
  container images, example commands, logs, CI output, or receipts.
- Redact secrets from plan summaries and support artifacts.

### 4. Tag ownership and sandbox expiration intent

Use defined tags where governance requires them, or otherwise use a consistent
free-form scheme. At minimum record:

- `project`
- `environment`
- `owner`
- `managed-by`
- `expires-at`

For a sandbox, `expires-at` records cleanup intent; it does not delete anything
and does not authorize deletion. Also record who will review expiration, what
data must be backed up or retained, and how the exact deployment will be found
through its state and receipt.

### 5. Make every public endpoint deliberate

For each endpoint, record whether it is public or private and why. A public
decision must include the protocol and port, allowed source ranges,
authentication, rate limiting, TLS and DNS ownership, and health-check
behavior. Prefer NSGs for workload-level policy, keep databases private unless
a documented requirement and control set justify otherwise, and never allow
administrative access from `0.0.0.0/0`.

A reachable HTTPS endpoint is not proof that the application is authenticated,
highly available, or production-ready. Confirm those properties separately.

### 6. Make failures visible to a monitored person

The smallest useful observability path includes:

- service logs needed to diagnose ingress and workload failures;
- application logs or an explicit statement that centralized ingestion and
  retention are not yet provided;
- metrics for availability, error rate, latency, saturation, and the key user
  transaction;
- alarms whose destinations are routed through Notifications to a channel that
  somebody actually monitors; and
- a tested notification path, deliberate retention, and correlation identifiers
  across the front door, runtime, and downstream calls.

Logging volume and retention are cost drivers. An alarm definition is not
complete until its notification route has been exercised.

## Cost controls: three different tools

| Control | What it does | What it does not do |
|---|---|---|
| Budget | Alerts on configured actual-spend thresholds and, once useful history exists, optional forecast thresholds | It is not a spending cap and does not stop resources |
| Compartment quota | Enforces allowed resource consumption for supported services within its scope | It does not predict the bill or replace workload sizing |
| Service limit | Bounds currently available service capacity for the tenancy and target scope | It is not a project budget or a desired architecture setting |

Check for an existing budget on the exact target before proposing another one,
and route alerts to a real notification destination. Verify current pricing,
region availability, quotas, and service limits for the exact target before
deployment.

### Cost worksheet without fixed prices

Fill this worksheet with current regional rates only when preparing an actual
estimate. Use low, expected, and high usage assumptions rather than a single
false-precision number.

| Driver | Workload assumption to write down | Meter or choice to verify now |
|---|---|---|
| Runtime | Shape, count, active hours, concurrency, or invocation duration | Current compute, Container Instances, or Functions pricing for the selected region |
| Database and storage | Engine/shape, allocated and growing storage, IOPS, and availability model | Current database, block, object, and backup meters |
| Front door | Requests, capacity, protocol, and required policy features | API Gateway or Load Balancer pricing and traffic behavior |
| Network | Public egress, private egress, and gateway traffic paths | Applicable egress, NAT Gateway, Service Gateway, public IP, gateway, and load-balancer charges |
| Observability | Daily log volume, metric/alarm count, and retention | Logging ingestion and retention plus Monitoring and Notifications meters |
| Registry and delivery | Image size, number of versions, scans, and retention | Registry storage and related delivery meters |
| Recovery | Snapshot, backup, and restore-retention requirements | Backup storage and cross-region or egress effects |
| Idle and residual resources | Nights, weekends, expired sandboxes, retained images, IPs, logs, and backups | Which resources continue to meter after the application stops |

For each scenario, calculate `current regional unit rate x expected units`, add
the line items, record the source and check date, and identify the top two cost
drivers. Do not promise a fixed bill, Free Tier eligibility, or a bounded cost
from the architecture name alone.

## Delivery gates

Authorization does not carry forward between gates:

1. **Read-only:** inspect the repository, configured identity, resource
   metadata, logs, metrics, limits, and current inventory. Redact sensitive
   output.
2. **Generate:** create a proposal, Terraform, policy draft, commands, or a
   saved plan. This still does not authorize an OCI change.
3. **Write:** before IAM or resource mutation, summarize the exact saved plan's
   creates, updates, replacements, deletes, IAM changes, public exposure, data
   effects, and directional cost drivers. Show the authenticated principal or
   profile, tenancy, region, compartment name and OCID, and environment. Obtain
   explicit approval immediately before apply.
4. **Destructive:** resolve the exact targets from state and the deployment
   receipt, preview retained data and impact, and obtain a separate explicit
   approval immediately before destroy or deletion.

Bind approval to the exact reviewed plan. If the target, source, lock file, or
plan changes, generate a new preview and request a new approval.

## Evidence after apply

After verification, create a deployment receipt containing:

- the code and IaC revisions and saved-plan lineage;
- exact managed resource identifiers and the image digest;
- the endpoint and bounded smoke-test result;
- observed log, metric, alarm, and notification-path results;
- rollback instructions; and
- the exact teardown scope and retained-resource expectations.

Do not include credentials or raw secret values. A local receipt is operational
evidence, not a signed attestation, and it does not turn a sandbox into a
production deployment.

## Safe teardown

1. Resolve the deployment from its reviewed Terraform state and receipt;
   distinguish managed resources from read-only data sources.
2. Back up persistent data or record an explicit decision to waive it.
3. Preview the exact destroy and separately inventory resources that may remain:
   images, log groups, buckets and objects, secrets, DNS records, certificates,
   reserved public IPs, backups, notification resources, and the state backend.
4. Show the impact and retained data, then obtain destructive approval.
5. Never delete by broad compartment scope, tag query alone, unresolved
   variable, wildcard, or name prefix.
6. After destroy, verify the exact inventory again and report every retained
   resource with its owner and expected cost driver.

An expired sandbox tag is a review signal, not a substitute for this process.

## Founder sign-off checklist

- [ ] Workloads target a dedicated non-root project compartment.
- [ ] Human, deployment, and workload identities are separate and least
      privileged.
- [ ] State is protected and secrets are managed outside source and receipts.
- [ ] Ownership, environment, management, and expiration-intent tags are set.
- [ ] Every public endpoint has an explicit exposure and authentication design.
- [ ] Logs, metrics, alarms, Notifications, retention, and a monitored owner are
      defined and tested.
- [ ] Budget alerts, applicable quotas, service limits, and current cost drivers
      have been checked for the exact target.
- [ ] The approved plan, applied state, and verified receipt are kept distinct.
- [ ] Rollback and exact-scope teardown are documented before the environment is
      considered complete.

## Official references

- [IAM tenancy and compartments](https://docs.oracle.com/en-us/iaas/Content/Security/Reference/iam_security_topic-IAM_Tenancy_and_Compartments.htm)
- [Securing a tenancy](https://docs.oracle.com/en-us/iaas/Content/Security/Tasks/securing_your_tenancy.htm)
- [Budgets overview](https://docs.oracle.com/en-us/iaas/Content/Billing/Concepts/budgetsoverview.htm)
- [OCI cost management](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/era-cost-management.htm)
- [Tagging overview](https://docs.oracle.com/en-us/iaas/Content/Tagging/Concepts/taggingoverview.htm)
- [Managing Vault secrets](https://docs.oracle.com/en-us/iaas/Content/secret-management/Concepts/manage-secrets.htm)
- [Terraform on OCI](https://docs.oracle.com/en-us/iaas/Content/dev/terraform/home.htm)
- [Logging overview](https://docs.oracle.com/en-us/iaas/Content/Logging/Concepts/loggingoverview.htm)
- [Monitoring overview](https://docs.oracle.com/en-us/iaas/Content/Monitoring/Concepts/monitoringoverview.htm)
- [OCI Core Landing Zone](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/oci-core-landing-zone.htm)
