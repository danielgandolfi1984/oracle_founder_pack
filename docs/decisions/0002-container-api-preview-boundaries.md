# ADR 0002: Separate privileged bootstrap from a sandbox-only Container API runtime

- Status: accepted for field preview
- Date: 2026-09-17

## Context

The first executable founder path needs enough infrastructure to prove a real HTTPS endpoint without granting routine deployment automation tenancy-level IAM authority. OCI Container Instances must be able to pull from private OCIR, while public API Gateway networking, logs, alarms, and budgets span different scopes and lifecycles.

The path has not yet passed a live-tenancy, idempotency, rollback, or teardown trial. Calling it production-ready would be unsafe: one Container Instance is a single point of failure, image changes replace it, and centralized application-log retention is not included.

## Decision

Ship `0.2.0-preview.3` as a sandbox-only candidate in the UPL-1.0 public-preview package.

Use two Terraform states:

1. `bootstrap`, run by a tenancy administrator, owns the OCIR repository, Container Instance dynamic group/pull policy, and compartment budget.
2. `runtime`, run by a workload deployer, owns the dedicated VCN, private container, API Gateway, service logs, alarms, and notification subscription.

The image build/push occurs between them. Data crosses the boundary as reviewed, non-secret values rather than through `terraform_remote_state`. Each stack receives its own saved plan, target fingerprint, approval, and receipt.

Use API Gateway as the preview ingress because it provides a managed HTTPS endpoint and can reach the container's private IP. Public exposure has no default and must be selected explicitly. Public gateway traffic is limited by source CIDRs and rate limiting, but the sample has no application authentication.

Require an immutable image digest from the bootstrap-approved repository, a non-root/read-only container security context, no application resource principal, no public Container Instance IP, NSG-only subnets, Service Gateway access to OCIR, bounded tags/expiry, a preflight for the alert-only budget target, gateway logs, container metrics, and a confirmed notification path. Limit the Container Instance pull policy to the exact repository name; the dedicated compartment remains the dynamic-group boundary.

`founderctl` remains non-mutating. It verifies the exact Terraform version and invokes only argv-safe, read-only `terraform show -json` against exact saved plans and raw state snapshots. It binds plan variables and exact provider region/profile expressions to the asserted target; requires the complete resource/output graph and exact critical references; rejects concrete foreign relationship values; compares the root configuration snapshot and provider lock embedded inside the saved plan byte-for-byte with the reviewed stack and binds that manifest hash into approvals; derives the OCIR repository path from plan plus state; summarizes without serializing arbitrary values; performs a bounded, URL-bound HTTPS smoke test; emits allowlisted, bootstrap-chained `locally_verified` receipts with state lineage/serial and address-to-OCID ownership; compares applied network and observability relationship OCIDs within the state graph; and fails teardown unless receipt, current state, delete-plan IDs, and the required post-runtime exact-ID readback evidence—including child container and VNIC identifiers—reconcile. It never executes apply/destroy. Local receipts and readback artifacts are evidence rather than signed attestations.

## Consequences

- Routine runtime credentials do not inherit IAM mutation authority.
- The journey needs two applies and a build/push step.
- Releasing a new image replaces the Container Instance and can cause downtime.
- A public preview is anonymous unless the founder adds and separately validates authentication.
- Local state remains evaluation-only; team/production remote-state design is deferred.
- Field qualification requires a real sandbox run, a zero-change second plan, rollback, alarm delivery, and exact residual audit after teardown.
- Reusable Container Instances deployment/troubleshooting knowledge should move to a proposed upstream Oracle skill; the toolkit retains founder orchestration and safety contracts.

## Rejected alternatives

- A monolithic state: rejected because it couples routine releases to tenancy IAM and repository lifecycle.
- A direct public Container Instance: rejected because it exposes the workload VNIC and leaves TLS/ingress controls to the application.
- OKE: rejected for this path because Kubernetes operations are unnecessary for one stateless API.
- A production label with disclaimers: rejected until HA, authentication, remote state, operations, and live trials are demonstrated.

## Sources

- https://docs.oracle.com/en-us/iaas/Content/container-instances/permissions/policy-reference.htm
- https://docs.oracle.com/en-us/iaas/Content/container-instances/creating-a-container-instance.htm
- https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewaycreatinggateway.htm
- https://developer.hashicorp.com/terraform/internals/json-format
