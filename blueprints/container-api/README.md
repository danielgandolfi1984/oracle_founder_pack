# Container API field preview

Version `0.2.0-preview.4` is a generate-and-review path for a stateless HTTP API on OCI Container Instances. It is deliberately limited to a sandbox and a single container instance. It is **not production-qualified**, highly available, zero-downtime, or field-tested in an OCI tenancy yet.

Security update: use this revision's helper and tests together. Earlier helpers
could accept unexpected API routes and re-added container capabilities in their
offline security gates. Do not use the full-toolkit archives from `v0.1.0` or
`v0.1.1` to validate infrastructure. Those immutable artifacts remain historical;
the standalone planning skills are unchanged. See the
[security update](https://github.com/danielgandolfi1984/oracle_founder_pack/blob/container-api-v0.2.0-preview.4/docs/SECURITY-UPDATE-2026-09-21.md).

The Terraform has been formatted and validated locally with Terraform `1.16.3` and Oracle OCI provider `9.2.0`. No `terraform plan` has been run against a real target, no image has been built on this host, and no OCI resource has been created. This exact Terraform pin is not compatible with OCI Resource Manager's currently documented `1.5.x` operational line; the preview is local-Terraform only.

Upstream status: `temporary-upstream-gap`. Proposed contribution: reusable `oracle/skills` guidance for Container Instances deploy/troubleshoot, private OCIR pull plus exact-digest scan evidence, bounded and centralized application logging, metrics, and provider replacement behavior. Founder sequencing, approvals, receipts, and cross-cloud migration remain toolkit responsibilities.

## What it creates

```text
client
  │ HTTPS 443, explicit source CIDRs
  ▼
OCI API Gateway (PUBLIC or PRIVATE; regional subnet)
  │ HTTP on the application port; NSG-to-NSG only
  ▼
one OCI Container Instance (private subnet, fixed private IP, no public IP)
  │ HTTPS through Service Gateway
  ▼
private immutable OCIR repository

API Gateway ── access/execution logs ── OCI Logging
Container Instance ── CPU/memory metrics ── Alarms ── Notifications email
project compartment ── alert-only monthly budget
```

For the public variant, API Gateway uses a public regional subnet and Internet Gateway. The container remains private. For the private variant, neither the gateway nor the container receives internet ingress. Oracle documents the default managed API Gateway certificate path only for realm OC1; do not use this generated-certificate preview in another realm or present it as a custom-domain production design.

The sample publishes only `GET /`, `GET /healthz`, and `GET /readyz` below the configured path prefix. The endpoint has rate limiting but no application authentication. A public gateway is therefore an intentionally anonymous sandbox endpoint, further bounded by the configured ingress CIDRs.

## Authority boundaries

| Stack | Authority | Resources | Apply cadence |
|---|---|---|---|
| `terraform/bootstrap` | Tenancy administrator | Private immutable OCIR repository, Container Instance dynamic group, narrowly scoped image-pull policy, alert-only budget | Infrequent and separately approved |
| `terraform/runtime` | Workload deployer | VCN, subnets, gateways, NSGs, Container Instance, API Gateway, logs, alarms, notification topic/subscription | Per sandbox/release |

The stacks have separate state and separate approvals. Runtime contains no `oci_identity_*` resource. The blueprint assumes an existing dedicated, non-root project compartment and an already-authorized human or CI deployer; it does not create users, API keys, groups, or broad deployer policies. The sample application cannot access the Container Instance resource principal.

OCIR is created before the image can be pushed, so the journey has two independent applies. Do not merge the stacks and do not give routine runtime automation the bootstrap administrator profile.

## Prerequisites

- An existing dedicated, non-root sandbox compartment. The bootstrap dynamic group intentionally matches Container Instances in that compartment, while its policy is restricted to the one repository name.
- A reviewed OCI CLI profile; credentials stay in the standard OCI configuration, never in tfvars.
- A tenancy administrator for the bootstrap plan and a separately authorized workload deployer for runtime.
- Terraform `1.16.3`, Docker Buildx, Python 3.9 or newer, and optionally the OCI CLI for read-only checks and log retrieval.
- An explicit availability domain selected after checking Container Instance shape availability/capacity in the target region.
- A notification email whose OCI Notifications subscription can be confirmed.
- A secure Terraform state location. Local state is acceptable only for an individual sandbox evaluation; state may contain identifiers and configured environment variables.

Before relying on pricing, availability, service limits, or shape capacity, verify the current target region. Use a read-only Budgets lookup to prove that no budget already targets the project compartment, then set `budget_target_verified_without_existing_budget` to `true`. The preview does not reuse an existing budget, and OCI permits only one budget for a target. A budget sends alerts; it does not cap or stop spend.

## 1. Prepare private configuration

Run from the repository root. The generated files are ignored by Git, but still contain tenancy identifiers and personal contact data, so keep them mode `0600` and do not share them.

```bash
umask 077
mkdir -p .oci-founder
chmod 700 .oci-founder
cp blueprints/container-api/terraform/bootstrap/terraform.tfvars.example.json .oci-founder/bootstrap.tfvars.json
cp blueprints/container-api/terraform/runtime/terraform.tfvars.example.json .oci-founder/runtime.tfvars.json
```

Replace every bootstrap example value. Set an expiry within 90 days, and do not set the budget preflight flag until the read-only check is complete. Validate bootstrap first:

```bash
python3 blueprints/container-api/tools/founderctl.py config-check \
  --kind bootstrap \
  --config .oci-founder/bootstrap.tfvars.json

```

Runtime configuration is completed after bootstrap returns the exact `repository_path`. Its check rejects production classification, images outside that approved repository, mutable image tags, overlapping or undersized subnets, expired sandboxes, placeholder inputs, and secret-like environment-variable names.

## 2. Validate both Terraform stacks

Use the committed lock files. Never run `init -upgrade` during an approved deployment.

```bash
terraform -chdir=blueprints/container-api/terraform/bootstrap init -backend=false -input=false -lockfile=readonly
terraform -chdir=blueprints/container-api/terraform/bootstrap fmt -check -diff
terraform -chdir=blueprints/container-api/terraform/bootstrap validate

terraform -chdir=blueprints/container-api/terraform/runtime init -backend=false -input=false -lockfile=readonly
terraform -chdir=blueprints/container-api/terraform/runtime fmt -check -diff
terraform -chdir=blueprints/container-api/terraform/runtime validate
```

`-backend=false` is appropriate for this local-state preview because no backend block is included. Before team use, design and review a remote backend rather than copying local state.

## 3. Plan and review bootstrap

Resolve the authenticated principal, tenancy, region, and compartment read-only. Record literal values in local shell variables; do not infer the target from a resource name.

```bash
terraform -chdir=blueprints/container-api/terraform/bootstrap plan \
  -input=false \
  -out=../../../../.oci-founder/bootstrap.tfplan \
  -var-file=../../../../.oci-founder/bootstrap.tfvars.json
```

`founderctl` verifies Terraform `1.16.3`, then runs the read-only `terraform show -json` operation itself, with an argument array and no shell. That binds the redacted review to the exact saved plan and avoids persisting raw plan JSON, which can contain sensitive values:

```bash
python3 blueprints/container-api/tools/founderctl.py plan-summary \
  --stack bootstrap \
  --saved-plan .oci-founder/bootstrap.tfplan \
  --principal "$FOUNDER_PRINCIPAL_OCID" \
  --tenancy "$FOUNDER_TENANCY_OCID" \
  --region "$FOUNDER_TARGET_REGION" \
  --home-region "$FOUNDER_HOME_REGION" \
  --oci-profile "$FOUNDER_OCI_PROFILE" \
  --compartment "$FOUNDER_COMPARTMENT_OCID" \
  --out .oci-founder/bootstrap-plan-summary.json
```

Review every resource, IAM statement, cost driver, replacement/delete, target field, and risk code. The gate compares target variables and exact provider region/profile expressions embedded in the plan, requires the complete resource/output graph, and checks security-critical IAM, network, logging, notification, and alarm relationships. It rejects concrete foreign relationship OCIDs before apply and rechecks create-time unknown IDs in state. It also compares the root configuration snapshot and provider lock embedded in the saved plan byte-for-byte with the reviewed local stack. The approval phrase binds the review to the target fingerprint (including the OCI profile), saved-plan SHA-256, rendered-plan SHA-256, and that reviewed source-manifest hash. `founderctl` never applies Terraform; approval enforcement remains a human/CI process boundary.

Only after an administrator explicitly approves that exact phrase, apply the exact saved plan:

```bash
terraform -chdir=blueprints/container-api/terraform/bootstrap apply \
  -input=false \
  ../../../../.oci-founder/bootstrap.tfplan
```

IAM resource-principal membership and policy changes can take time to propagate. A completed Terraform apply is not proof that an immediate image pull will succeed.

Capture one private raw state snapshot immediately, then issue the bootstrap receipt that runtime will be required to reference. Raw state can contain identifiers, personal data, and application values; never print, commit, or share it:

```bash
umask 077
terraform -chdir=blueprints/container-api/terraform/bootstrap state pull > .oci-founder/bootstrap-state.tfstate
chmod 600 .oci-founder/bootstrap-state.tfstate

python3 blueprints/container-api/tools/founderctl.py receipt \
  --layer bootstrap \
  --summary .oci-founder/bootstrap-plan-summary.json \
  --saved-plan .oci-founder/bootstrap.tfplan \
  --state .oci-founder/bootstrap-state.tfstate \
  --provider-lock blueprints/container-api/terraform/bootstrap/.terraform.lock.hcl \
  --source-revision "$FOUNDER_SOURCE_REVISION" \
  --iac-revision "$FOUNDER_IAC_REVISION" \
  --out .oci-founder/deployment-receipt-bootstrap.json
```

## 4. Build and push an immutable multi-architecture image

The Dockerfile intentionally has no default base. Supply a reviewed multi-architecture base image by digest, not only by tag. Authenticate Docker to the realm-correct OCIR endpoint using Oracle's current instructions; never store an auth token in this repository or pass it as a Docker build argument.

```bash
python3 blueprints/container-api/tools/founderctl.py image-ref-check \
  --image "$FOUNDER_BASE_IMAGE_BY_DIGEST"

docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --build-arg PYTHON_IMAGE="$FOUNDER_BASE_IMAGE_BY_DIGEST" \
  --tag "$FOUNDER_REPOSITORY_PATH:$FOUNDER_RELEASE_ID" \
  --provenance=true \
  --sbom=true \
  --push \
  --metadata-file .oci-founder/build-metadata.json \
  blueprints/container-api/app
```

Read the pushed manifest digest from the Buildx metadata. Copy `repository_path` from the protected bootstrap receipt into `approved_repository_path`, then set `container_image_url` to that exact path plus `@sha256:<digest>` in the runtime tfvars. Retain the previous locally verified image URL for rollback. Select the availability domain explicitly; do not accept the first AD from an unordered list without checking shape capacity. Complete the runtime contract check now:

Creating the private immutable repository does not enable OCI Vulnerability
Scanning. This preview has no scanner/target or scan receipt and makes no claim
that the image was scanned. A future evidence contract must correlate this
digest with the resolved OCIR image OCID and scan-result OCID because the
documented scan-result API has no direct digest filter.

```bash
python3 blueprints/container-api/tools/founderctl.py config-check \
  --kind runtime \
  --config .oci-founder/runtime.tfvars.json
```

## 5. Plan and review runtime

Set `gateway_endpoint_type` explicitly:

- `PUBLIC`: public regional gateway subnet plus Internet Gateway; generated API Gateway TLS is acceptable only for this sandbox preview.
- `PRIVATE`: private gateway subnet; run smoke verification from a network that can route to the VCN.

Restrict `allowed_ingress_cidrs` whenever possible. `0.0.0.0/0` is allowed only as an explicit decision and appears as `world_ingress` in the plan summary.

```bash
terraform -chdir=blueprints/container-api/terraform/runtime plan \
  -input=false \
  -out=../../../../.oci-founder/runtime.tfplan \
  -var-file=../../../../.oci-founder/runtime.tfvars.json

python3 blueprints/container-api/tools/founderctl.py plan-summary \
  --stack runtime \
  --saved-plan .oci-founder/runtime.tfplan \
  --bootstrap-receipt .oci-founder/deployment-receipt-bootstrap.json \
  --principal "$FOUNDER_PRINCIPAL_OCID" \
  --tenancy "$FOUNDER_TENANCY_OCID" \
  --region "$FOUNDER_TARGET_REGION" \
  --oci-profile "$FOUNDER_OCI_PROFILE" \
  --compartment "$FOUNDER_COMPARTMENT_OCID" \
  --out .oci-founder/runtime-plan-summary.json
```

The summary fails closed on an incomplete resource/output set; target-variable or provider-region mismatch; runtime IAM; an image outside the bootstrap-approved repository; a mutable/unknown image; an exposed application resource principal; a public/unknown Container Instance VNIC; altered gateway, route, security-list, NSG, or API route contracts; broad or wrong-target IAM; security-critical unknowns; or an unsupported plan format. Its approval phrase also includes the bootstrap receipt hash.

After a separate explicit runtime approval, apply only the reviewed saved plan:

```bash
terraform -chdir=blueprints/container-api/terraform/runtime apply \
  -input=false \
  ../../../../.oci-founder/runtime.tfplan
```

## 6. Verify and issue receipts

For a public endpoint, run the bounded HTTPS smoke test. It refuses redirects, query data, oversized bodies, non-HTTPS URLs, and any response other than the exact health contract. It stores only status, lengths, hashes, and assertions—never response bodies or headers.

```bash
python3 blueprints/container-api/tools/founderctl.py smoke \
  --url "$FOUNDER_HEALTHCHECK_URL" \
  --out .oci-founder/smoke-result.json
```

Also verify:

- the subscription output is `ACTIVE` after the email confirmation;
- CPU and memory metrics appear in namespace `oci_computecontainerinstance` after traffic;
- both API Gateway service logs receive events;
- the budget targets the intended compartment;
- all mandatory tags are present;
- the Container Instance VNIC has no public IP;
- the deployed image URL is the reviewed digest.

Container stdout/stderr is bounded troubleshooting evidence, not centralized retention. OCI documents retrieval of only the most recent 256 KB (and supports the previous run separately):

```bash
oci container-instances container retrieve-logs \
  --container-id "$FOUNDER_CONTAINER_OCID" \
  --file -
```

Capture one private raw state snapshot, then generate the runtime receipt. `founderctl` decodes the snapshot with Terraform, records its lineage and serial, derives allowlisted outputs and address-to-OCID ownership from that single source, re-decodes the saved plan, verifies bootstrap lineage, compares the deployed image to the plan, derives the health URL from gateway state, and binds the smoke URL hash to it. Receipts are `locally_verified`, not signed attestations. They are ignored, mode `0600`, and contain exact OCIDs, so preserve them securely outside the Git repository.

```bash
umask 077
terraform -chdir=blueprints/container-api/terraform/runtime state pull > .oci-founder/runtime-state.tfstate
chmod 600 .oci-founder/runtime-state.tfstate

python3 blueprints/container-api/tools/founderctl.py receipt \
  --layer runtime \
  --summary .oci-founder/runtime-plan-summary.json \
  --saved-plan .oci-founder/runtime.tfplan \
  --state .oci-founder/runtime-state.tfstate \
  --provider-lock blueprints/container-api/terraform/runtime/.terraform.lock.hcl \
  --source-revision "$FOUNDER_SOURCE_REVISION" \
  --iac-revision "$FOUNDER_IAC_REVISION" \
  --smoke .oci-founder/smoke-result.json \
  --bootstrap-receipt .oci-founder/deployment-receipt-bootstrap.json \
  --out .oci-founder/deployment-receipt-runtime.json
```

## Rollback

Rollback is a new deployment, not a state restore and not an automatic mutation:

1. Read the previous locally verified digest from the protected receipt.
2. Confirm that exact digest still exists in OCIR.
3. Change only `container_image_url` and the release identifier.
4. Produce a fresh runtime plan and redacted summary.
5. Review Container Instance replacement and API impact; obtain a new approval bound to the new plan hash.
6. Apply, smoke-test, and issue a new receipt.

Changing the image replaces the Container Instance. This single-instance preview has downtime and makes no blue/green, traffic-shifting, or zero-downtime claim.

## Teardown

Destroy in this order: `runtime`, then `bootstrap`. Never use `-target`, name patterns, tags, compartment-wide deletion, or an old plan.

For each layer, create a fresh saved destroy plan and reconcile it with the locally verified receipt and a fresh raw state snapshot:

```bash
terraform -chdir=blueprints/container-api/terraform/runtime plan \
  -destroy \
  -input=false \
  -out=../../../../.oci-founder/runtime-destroy.tfplan \
  -var-file=../../../../.oci-founder/runtime.tfvars.json
terraform -chdir=blueprints/container-api/terraform/runtime state pull > .oci-founder/runtime-current-state.tfstate
chmod 600 .oci-founder/runtime-current-state.tfstate

python3 blueprints/container-api/tools/founderctl.py teardown-audit \
  --receipt .oci-founder/deployment-receipt-runtime.json \
  --saved-plan .oci-founder/runtime-destroy.tfplan \
  --state .oci-founder/runtime-current-state.tfstate \
  --principal "$FOUNDER_PRINCIPAL_OCID" \
  --tenancy "$FOUNDER_TENANCY_OCID" \
  --region "$FOUNDER_TARGET_REGION" \
  --oci-profile "$FOUNDER_OCI_PROFILE" \
  --compartment "$FOUNDER_COMPARTMENT_OCID" \
  --out .oci-founder/runtime-teardown-audit.json
```

The audit decodes the exact saved plan and current state itself. It requires matching target variables/provider bindings, state lineage, non-regressing serial, address-to-OCID ownership, security-critical state values, outputs, and a delete-only plan whose `before.id` values match current state exactly. The destructive approval phrase binds the target, saved/rendered plan, reviewed IaC source, receipt, and current-state hashes. A ready audit is still only local preview evidence. Obtain that separate approval before applying the exact saved destroy plan.

After applying the approved runtime destroy plan, capture a fresh post-destroy state snapshot and perform authenticated, read-only OCI GETs for every exact runtime OCID from the receipt. This includes every managed address-to-OCID entry plus the child `container_id` and `container_vnic_id` outputs. Do not translate authorization failures, timeouts, or ambiguous service responses into `not_found`. Record only confirmed absence in a private `oci-destroy-readback-evidence` JSON artifact with schema `1.2`, the runtime receipt SHA-256, runtime target fingerprint, post-destroy state lineage/serial, and one exact `{address, resource_id, result: "not_found"}` check per readback target. This artifact is local operator/verifier evidence, not a signed OCI attestation.

The strict shape is:

```json
{
  "schema_version": "1.2",
  "artifact": "oci-destroy-readback-evidence",
  "generated_at": "2026-09-17T18:00:00Z",
  "verification_method": "authenticated-read-only-oci-get",
  "runtime_receipt_sha256": "<64 lowercase hex characters>",
  "target_fingerprint": "<fingerprint from the runtime receipt>",
  "state_lineage": "<lineage from the post-destroy runtime state>",
  "state_serial": 11,
  "checks": [
    {
      "address": "<managed state address, or the #container/#vnic child key>",
      "resource_id": "<matching managed OCID or child output OCID>",
      "result": "not_found"
    }
  ]
}
```

`checks` must cover the complete `state.resource_ids` map plus exactly
`oci_container_instances_container_instance.api#container` mapped to output
`container_id` and `oci_container_instances_container_instance.api#vnic` mapped
to output `container_vnic_id`, with no duplicates or extras. The artifact must
be no more than 24 hours old when audited.

Only then plan bootstrap destroy. The bootstrap audit rejects an empty state by itself: it requires the runtime receipt, the empty higher-serial state, and the exact-ID readback artifact, in addition to its own receipt/state/plan reconciliation:

```bash
umask 077
terraform -chdir=blueprints/container-api/terraform/runtime state pull > .oci-founder/runtime-post-destroy-state.tfstate
chmod 600 .oci-founder/runtime-post-destroy-state.tfstate

terraform -chdir=blueprints/container-api/terraform/bootstrap plan \
  -destroy \
  -input=false \
  -out=../../../../.oci-founder/bootstrap-destroy.tfplan \
  -var-file=../../../../.oci-founder/bootstrap.tfvars.json
terraform -chdir=blueprints/container-api/terraform/bootstrap state pull > .oci-founder/bootstrap-current-state.tfstate
chmod 600 .oci-founder/bootstrap-current-state.tfstate

python3 blueprints/container-api/tools/founderctl.py teardown-audit \
  --receipt .oci-founder/deployment-receipt-bootstrap.json \
  --saved-plan .oci-founder/bootstrap-destroy.tfplan \
  --state .oci-founder/bootstrap-current-state.tfstate \
  --runtime-receipt .oci-founder/deployment-receipt-runtime.json \
  --runtime-state .oci-founder/runtime-post-destroy-state.tfstate \
  --runtime-destroy-evidence .oci-founder/runtime-destroy-readback-evidence.json \
  --principal "$FOUNDER_BOOTSTRAP_PRINCIPAL_OCID" \
  --tenancy "$FOUNDER_TENANCY_OCID" \
  --region "$FOUNDER_TARGET_REGION" \
  --home-region "$FOUNDER_HOME_REGION" \
  --oci-profile "$FOUNDER_OCI_PROFILE" \
  --compartment "$FOUNDER_COMPARTMENT_OCID" \
  --out .oci-founder/bootstrap-teardown-audit.json
```

The bootstrap approval phrase includes the readback artifact hash. Before destroying bootstrap, decide what happens to every image. Repository deletion can fail or erase rollback material; inspect and remove only exact image targets after explicit approval. After each destroy, perform exact-ID read-only checks and retain a durable record of deleted and intentionally retained resources. An empty Terraform state alone is not proof of a clean compartment.

## Known limits and open field checks

- Single region, one backend, one Container Instance, fixed private IP, and replacement downtime.
- No autoscaling, SLA, production TLS/custom domain, WAF, application authentication, database, backups, DR, or compliance claim.
- No arbitrary public egress from the app subnet; add NAT only after an explicit workload requirement and cost/security review.
- No application secret injection. Environment variables are non-secret. A future Vault/resource-principal extension needs its own policy and application contract.
- API Gateway access/execution logs are centralized; Container Instance stdout/stderr uses bounded on-demand retrieval unless a separately tested ingestion design is added.
- `apigateway` is the expected Logging service identifier, but it must be verified with the current target-region Logging service list before field qualification.
- Shape availability/capacity, service limits, IAM propagation, image pull, metric queries, alarm delivery, and second-plan idempotency require a real sandbox tenancy.
- The budget no-existing-target flag, `--principal`, and post-destroy OCI GET results are operator/verifier assertions until a live read-only OCI plugin is integrated; re-check them immediately before approval and never classify an authorization failure as absence.
- The generated API Gateway certificate is documented for private or non-production use; production requires explicit certificate/domain ownership.
- Oracle documents the default managed API Gateway certificate only for realm
  OC1. Other realms require the explicit custom-certificate path, which this
  preview does not implement.
- Local Terraform only: the exact `1.16.3` pin is not compatible with OCI
  Resource Manager's currently documented `1.5.x` runtime line.
- Local `founderctl` trusts the reviewed local Terraform binary after an exact version check and cannot prevent someone from bypassing it and calling Terraform directly; receipts are local evidence, not signed attestations.
- Saved-plan/source provenance relies on the pinned Terraform `1.16.3` archive
  layout and fails closed if the embedded root configuration or provider lock is
  absent or different. A Terraform upgrade requires an explicit contract and
  adversarial-test update.

## Official sources

- [Container Instances overview](https://docs.oracle.com/en-us/iaas/Content/container-instances/overview-of-container-instances.htm)
- [Creating a Container Instance](https://docs.oracle.com/en-us/iaas/Content/container-instances/creating-a-container-instance.htm)
- [DNS in a VCN](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/dns.htm)
- [Container Instances IAM policies](https://docs.oracle.com/en-us/iaas/Content/container-instances/permissions/policy-reference.htm)
- [Container Instance metrics](https://docs.oracle.com/en-us/iaas/Content/container-instances/container-instance-metrics.htm)
- [Retrieving Container Instance logs](https://docs.oracle.com/en-us/iaas/Content/container-instances/retrieve-logs.htm)
- [Creating an API Gateway](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewaycreatinggateway.htm)
- [API Gateway custom domains and TLS certificates](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewaysettingupcustomdomainscerts.htm)
- [API Gateway service logs](https://docs.oracle.com/en-us/iaas/Content/Logging/Reference/details_for_api_gateway.htm)
- [Scanning OCIR images for vulnerabilities](https://docs.oracle.com/en-us/iaas/Content/Registry/Tasks/registryscanningimagesforvulnerabilities.htm)
- [Vulnerability scan-result CLI](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/vulnerability-scanning/container/scan/result/list.html)
- [OCI Budgets](https://docs.oracle.com/en-us/iaas/Content/Billing/Concepts/budgetsoverview.htm)
- [Creating a budget](https://docs.oracle.com/en-us/iaas/Content/Billing/Tasks/create-budget.htm)
- [Repository-level OCIR policies](https://docs.oracle.com/en-us/iaas/Content/Registry/Concepts/registrypolicyrepoaccess.htm)
- [OCI Terraform provider releases](https://github.com/oracle/terraform-provider-oci/releases)
- [Resource Manager supported Terraform versions](https://docs.oracle.com/en-us/iaas/Content/ResourceManager/Reference/terraformversions.htm)
- [Terraform plan JSON format](https://developer.hashicorp.com/terraform/internals/json-format)
