# Roadmap

The roadmap is organized by validated capability, not by the number of OCI services covered.

## 0.1 — Foundation

Current public-preview scope:

- product promise, personas, boundaries, and success measures;
- portable `oci-founder` orientation and routing skill;
- AWS, Google Cloud, and Azure mental-model translation;
- Founder Baseline guardrails;
- Container API and Function API decision contracts;
- `oracle/skills` ownership boundary and immutable review lock;
- Agent Plugins, Codex, and Claude Code manifests;
- cross-agent prompt cases and dependency-free repository validation;
- a read-only, fingerprinted host-preflight contract and Q0–Q4 qualification
  playbook;
- the canonical Oracle-template founder guide presentation, v11, kept outside
  the repository, public packages, and UPL-1.0 grant.

Exit gate: manifests and skill validate locally, every reference resolves, and
an independent agent produces a safe plan from a realistic backend prompt.

Status on 2026-09-18: **partially met**. Dependency-free repository validation
passed against the released public-preview source. The Agent Plugins
`1.0.0` schema, Skill Creator and Plugin Creator validators, static safety and
secret checks, fail-closed standalone adapter, and relative-link/local-JSON
checks passed. The current skill tree SHA-256 is
`c9ca7081b818f85a248836a53d12b94b6c995da9825696346a1075bf42c2dd37`.

The source, skill-package, and full-package project-scoped lifecycles passed
install, filtered list, removal, reinstall, filtered list, and cleanup in
separate Codex, Cursor, and Claude Code layouts. Current deterministic archive
SHA-256 values are
`517c4f6d4d29b35d085d4cf534656608e6c1d7315526563ee632ee5ae9fe7954`
for the skill package and
`33037edf2783895c03a5e40bb03a0f18468a26945dc7fce8a9e251ea7e75ca80`
for the full package. The renewed read-only host preflight and its embedded
repository validation passed, while correctly retaining
`release_qualified: false` because native-host gates remain.

The three-case current-skill assessment passed focused-answer routing,
skill-only upstream fail-closed behavior, and full-toolkit verification-first
routing without file writes, network calls, OCI commands, or cloud mutations.
It is non-native evidence and does not close Q2 or Q3.

The project is now an independent public source preview on `main` at
[`danielgandolfi1984/oracle_founder_pack`](https://github.com/danielgandolfi1984/oracle_founder_pack),
licensed under UPL-1.0 and maintained by Daniel Gandolfi with best-effort
community support and no SLA. The published
[`v0.1.0` GitHub release](https://github.com/danielgandolfi1984/oracle_founder_pack/releases/tag/v0.1.0)
at commit `6cf08bf30febc434cefed228f53c43a1f8802ec2` provides the immutable
public-preview coordinate. Its exact-source
[CI run 35375372149](https://github.com/danielgandolfi1984/oracle_founder_pack/actions/runs/35375372149),
public-tag Codex install/list/remove check, and redownloaded asset verification
passed. Follow-up docs and evidence on `main` retain version `0.1.0` without
replacing the published artifacts. Marketplace and registry publication
remain outside this milestone and separate from the technical qualification
gates.

Formal Codex Q2/Q3 remain `BLOCKED`; Cursor Agent and Claude Code are
unavailable; Cursor same-name deduplication, global-profile lifecycle, native
cross-host replay, and OCI sandbox field evidence remain unresolved. The real
locked `oracle/skills` checkout now passes verification, and its OCI domain
passes isolated Codex project install/list/remove/reinstall with the exact
source hash; upstream native discovery and sibling Database navigation remain
open. The fresh post-release Codex probe passed one explicit safety/schema
prompt against the released skill with no observed mutation, valid structured
output, and clean removal. It records probe Q2 `PASS` and Q3 `PARTIAL`;
independent semantic review passed with reservations. The response was safe and
grounded in the fixture but too long for the focused request. Improving
conciseness and loading fewer references for focused questions is a follow-up
usability task; the released skill remains unchanged. Historical receipts and
the current assessment are tracked separately in [`VALIDATION.md`](VALIDATION.md).

The first full public CI baseline passed at `bf5ebb3` in
[run 35355021483](https://github.com/danielgandolfi1984/oracle_founder_pack/actions/runs/35355021483).
After pinning the official Node.js 24 action lines by full SHA and moving to
`ubuntu-24.04`, the founder-onboarding baseline at `deb13d8` passed in
[run 35359228279](https://github.com/danielgandolfi1984/oracle_founder_pack/actions/runs/35359228279).
These historical exact-revision results are retained alongside the passing
`v0.1.0` CI run above. Every later commit needs its own remote CI result;
native-host, field, and stable-release gates remain separate.
See [`VALIDATION.md`](VALIDATION.md).

## 0.2 — Container API field path (preview in progress)

Implemented in `0.2.0-preview.3`:

- a minimal example backend with a health endpoint;
- an immutable multi-architecture build contract with SBOM/provenance flags;
- separate bootstrap and runtime Terraform authority/state boundaries;
- Terraform for an existing dedicated compartment, VCN, explicit NSGs, private immutable OCIR, one private Container Instance, API Gateway, service logs, metrics, alarms, tags, Notifications, and an alert-only budget;
- explicit private and intentionally public API Gateway variants;
- argv-safe saved-plan/state decoding, target-bound complete-graph plan contracts, bounded smoke test, rollback contract, state-lineage/OCID-bound local receipts, and exact managed-resource teardown reconciliation;
- Terraform `1.16.3` and Oracle OCI provider `9.2.0` exact pins with portable lock files;
- unit tests and offline Terraform validation.

Still planned before a stable `0.2`:

- live shape/capacity, IAM propagation, OCIR pull, DNS, API Gateway logging identifier, metrics, alarm delivery, and email confirmation checks;
- sandbox plan/apply, second-plan idempotency, rollback, exact-ID post-destroy inventory, and retained-image handling;
- OCIR Vulnerability Scanning evidence that correlates the reviewed digest,
  OCIR image OCID, and scan-result OCID, plus proof that runtime pulled the
  reviewed digest (the documented scan-result API has no direct digest filter);
- quota checks, cost-tracking defined tags, usage-report/Cloud Advisor review, and early-actual plus forecast alert guidance;
- a tested remote-state/OCI Resource Manager variant on its supported Terraform
  line; the current `1.16.3` stack is explicitly not Resource Manager compatible;
- a field-tested centralized Container Instance application-log pattern; native
  on-demand retrieval exposes only the most recent 256 KB and is not retention;
- a production availability/TLS/authentication design (explicitly outside the current single-instance preview);
- AWS App Runner, Fargate, Cloud Run, and Azure Container Apps migration prompts.

Exit gate: two independent users reach a verified endpoint in a sandbox tenancy, second apply is idempotent, and teardown leaves no unexpected resources.

Status on 2026-09-17: **not met**. Local code, unit, format, provider-schema,
and safety-contract checks pass, but no OCI plan or mutation has been performed.

## 0.3 — Function API composition

Planned capability:

- compose the official `oci-functions-deploy` and troubleshooting skills;
- add API Gateway, founder IAM, cost attribution, observability, and receipt contracts;
- add an event-driven example and an HTTP example;
- verify direct signed invocation before public ingress;
- contribute any reusable Functions gaps upstream.

Exit gate: the journey works without copying upstream service procedures and passes deploy, failure, rollback, and teardown tests.

## 0.4 — Read-only OCI context

Planned capability:

- local, read-only identity/profile discovery;
- region, compartment, service-limit, and resource inventory queries;
- logs, metrics, work request, and cost evidence retrieval;
- Terraform validation and structured plan summaries;
- command allowlist, argument-safe execution, redaction, and structured output;
- separate configuration adapters where MCP portability differs across hosts.

Exit gate: threat model and abuse tests demonstrate that the plugin cannot apply, destroy, mutate IAM, or disclose secret values.

## 0.5 — Data add-ons and operations

Planned capability:

- PostgreSQL, MySQL HeatWave, Autonomous AI Database, and Object Storage decision modules;
- migration and connection verification contracts;
- backup and restore drills;
- cost and log-volume diagnostics;
- graduation from a single environment to dev/staging/prod.

## 1.0 — Stable founder release

Release criteria:

- Container API and Function API are stable by the quality gate in `PRODUCT.md`;
- installation and invocation are tested in current Codex, Cursor, and Claude Code;
- at least 80% of representative target users complete a path without maintainer intervention;
- median time to a verified endpoint is below 60 minutes in the usability cohort;
- zero credential leaks and zero unapproved mutations in the release test suite;
- the UPL-1.0, independent-project, support, security, and internal-material
  boundaries remain published and internally consistent;
- contribution and upstream-sync ownership is assigned; and
- compatibility range, release notes, signing/provenance policy, and
  lifecycle/deprecation policy are published.

## Upstream contribution stream

Service-level gaps discovered by field paths should become focused contributions to `oracle/skills`, including likely gaps around generic Container Instances, private OCIR pull plus scan evidence, founder networking, bounded and centralized Container Instance logging, Vault/resource principals, observability baseline, and secure non-OKE Terraform/Resource Manager workflows. The toolkit should consume those contributions rather than retain permanent duplicates.

## Sources

- https://github.com/oracle/skills
- https://github.com/oracle/skills/blob/main/SKILL_AUTHORING_GUIDE.md
