# Founder Toolkit for OCI: product brief

Founder Toolkit for OCI is a personal, independent public-preview project
created and maintained by Daniel Gandolfi, an Oracle employee publishing in his
personal capacity. The views expressed here are his own and do not represent
Oracle. This is not an Oracle product and is not sponsored, endorsed,
maintained, or supported by Oracle.

The project's original public content is licensed under the Universal
Permissive License 1.0 (`UPL-1.0`); see [`LICENSE`](../LICENSE). The internal
Oracle-template presentation remains confidential, is excluded from the public
repository and every public distribution, and is outside this license grant.

## Thesis

OCI adoption for founders is primarily an experience problem, not a catalog problem. A backend developer who already understands containers, HTTP APIs, relational databases, CI/CD, and cloud tradeoffs should not need to become an OCI specialist before shipping the first useful workload.

Founder Toolkit for OCI turns OCI into a guided journey inside the developer's
existing coding agent.

**Tagline:** Plan your backend's path to OCI with the coding agent you already use.

**MVP target:** A backend developer new to OCI can move from a repository to a
verified OCI endpoint in under 60 minutes using a coding agent, after account
access and prerequisites are ready. Console guidance is part of onboarding;
repeatable deployment should use reviewed CLI, SDK, or IaC procedures.

This is a target to validate with users, not a current performance claim.

Version `0.1.1` is the current planning and portability preview. The repository also
contains a separately versioned, unsupported `0.2.0-preview.3` Container API
candidate for sandbox evaluation. Neither may be marketed as a production
deployment product or as having shipped a workload in OCI.

## Primary users

### Technical founder or solo developer

- Knows backend development and usually Docker.
- Wants a working endpoint the same day.
- Fears losing time to unfamiliar IAM, networking, and service names.
- Needs low operational overhead and visible cost drivers.

### Backend engineer arriving from AWS, Google Cloud, or Azure

- Thinks in Lambda, Fargate, Cloud Run, RDS, S3, IAM Role, or Managed Identity.
- Needs semantic translation, not a logo-comparison table.
- Often has an existing repository and deployment contract to preserve.

### First platform or backend hire

- Needs to turn a prototype into repeatable dev, staging, and production environments.
- Values IaC, least privilege, observability, rollback, and clean teardown.
- Is secondary for the first deployment and primary for graduation features.

### Maintainer, DevRel engineer, or solution architect

- Validates golden paths against real tenancies.
- Contributes reusable service knowledge to `oracle/skills`.
- Maintains journey composition and cross-agent behavior here.

## Anti-personas for the MVP

- Enterprise landing-zone teams.
- Regulated workloads requiring a compliance baseline.
- Complex Kubernetes platforms.
- Full-account cloud migrations.
- Frontend or mobile product scaffolding.

The toolkit should route these users to appropriate Oracle guidance rather than imply that a Founder Baseline is production certification.

## Jobs to be done

1. **Orient:** Explain OCI through the user's existing cloud vocabulary and repository evidence.
2. **Bootstrap:** Locate account identifiers, prepare local authentication, and
   understand compartments, VCNs, subnets, VM access, cost, and cleanup before
   proposing a repeatable deployment baseline.
3. **Ship:** Select and execute a founder-friendly golden path with explicit approval gates.
4. **Verify:** Demonstrate endpoint health, logs, metrics, alarms, cost attribution, and access boundaries.
5. **Operate:** Diagnose failures from read-only evidence and route to service-specific official skills.
6. **Teardown or graduate:** Remove the exact environment safely or evolve into stronger platform patterns.

These jobs describe the product direction, not six implemented automation
features. Current foundational documentation consists of
[account and local access](ACCOUNT-SETUP.md) and a
[human-executed VCN/VM lab](FIRST-VM.md). It complements the planning skill and
does not establish live field validation or a standalone operational VM skill.

## Founder-facing adoption materials

The documentation now connects those foundations to a product decision:

- [Why OCI for this backend?](WHY-OCI.md) defines evidence and reversal
  conditions instead of claiming a universal price or performance advantage.
- [Reference backend](REFERENCE-BACKEND.md) defines a small B2B product journey,
  identifies missing implementation, and specifies authorization, persistence,
  upload and recovery tests. It is a design, not an executable full-stack sample.
- [Cost scenarios](COST-SCENARIOS.md) expose workload units, full TCO and missing
  rates. No observed bill or validated customer-capacity claim is available yet.
- [Evidence](EVIDENCE.md) separates current records from future field tests and
  provides a consent-aware structure for real founder stories.
- [Getting started](GETTING-STARTED.md) provides routes for different team stages,
  account and region decisions, help channels, and maintained PT-BR/ES entry guides.

An optional AI product feature appears as an evaluation requirement in the
reference design, not an implemented integration or a default architecture.

## Product boundaries

The toolkit owns:

- end-to-end founder journeys;
- cross-cloud translation;
- opinionated golden paths and blueprints;
- founder-level security and cost policies;
- deployment and teardown receipts;
- distribution adapters for coding agents;
- behavioral evaluations across agents.

[`oracle/skills`](https://github.com/oracle/skills) owns reusable Oracle service facts and procedures. Oracle documentation remains authoritative for current product behavior.

## MVP golden paths

### Container API

For an existing Dockerized HTTP backend without Kubernetes requirements:

- OCI Container Registry;
- Container Instances;
- API Gateway or Load Balancer, based on protocol and policy needs;
- minimal VCN and NSGs;
- Vault secrets;
- front-door logs, explicit application-log collection, Monitoring, Alarms, and Notifications;
- Terraform, verification, rollback, and teardown.

### Function API

For function-compatible, event-driven, or intermittent workloads:

- OCI Functions;
- OCI Container Registry;
- API Gateway when public HTTP ingress is needed;
- VCN/subnets for downstream access;
- resource-principal access to secrets and services;
- observability, verification, rollback, and teardown.

This path composes the existing official Functions deployment and troubleshooting skills.

### Data as an add-on

The first smoke deployment should be stateless unless data is the workload's purpose. The toolkit will select among external/no database, Object Storage, OCI Database with PostgreSQL, MySQL HeatWave, and Autonomous AI Database based on compatibility and operational value rather than brand preference.

## Non-goals

- Teach every OCI service.
- Default to Kubernetes.
- Rebuild or fork `oracle/skills`.
- Autonomously mutate a tenancy.
- Promise Free Tier eligibility, fixed prices, compliance, or regional availability.
- Hide IAM and networking decisions behind generated code.
- Build a proprietary web console.

## Success measures

### North Star

Percentage of target users who reach a verified OCI endpoint in under 60 minutes
after account access and prerequisites are ready. Record onboarding and total
elapsed time separately, including failed attempts. This remains an unvalidated
target, not a published completion-rate or speed claim.

### Supporting measures

- first-deployment success rate;
- time to the first valid Terraform plan;
- account-access setup success and completion of the foundational lab;
- repeatable deployment completion after onboarding;
- successful rollback and teardown rate;
- forecast-versus-observed cost, including credits and retained resources;
- successful tenant-isolation and data-restore tests for implemented product paths;
- percentage of service-level knowledge sourced upstream;
- cross-agent behavioral pass rate;
- secret exposure and excessive-permission incidents: zero;
- time from a relevant upstream change to a reviewed toolkit release.

## Stable asset quality gate

An executable golden path is stable only after:

- consequential OCI claims link to current official sources;
- upstream dependencies are pinned to immutable commits;
- Terraform formatting, validation, and security checks pass;
- apply, verify, rollback, and destroy pass in a sandbox tenancy;
- a second apply is idempotent;
- teardown leaves no unexpected billable resources;
- IAM is reviewed for least privilege;
- no credential or secret appears in Git, state output, logs, or receipts;
- the same journey contract works in Codex, Cursor, and Claude Code;
- representative target users can complete it without maintainer intervention.

## Sources

- https://github.com/oracle/skills
- https://docs.oracle.com/en-us/iaas/Content/container-instances/overview-of-container-instances.htm
- https://docs.oracle.com/en-us/iaas/Content/Functions/home.htm
- https://docs.oracle.com/en-us/iaas/Content/dev/terraform/home.htm
- https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/oci-core-landing-zone.htm
