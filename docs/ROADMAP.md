# Roadmap

The roadmap is organized by validated capability, not by the number of OCI services covered.

## 0.1 — Foundation

Current evaluation-draft scope:

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
  the evaluation archives.

Exit gate: manifests and skill validate locally, every reference resolves, and
an independent agent produces a safe plan from a realistic backend prompt.

Status on 2026-09-18: **partially met**. Dependency-free repository checks,
the published Agent Plugins `1.0.0` schema snapshot, current skill and Codex
development validators with pinned dependency hashes, static safety checks, and
recorded independent content-forward evaluations pass. The existing 24-case
coverage index and recorded evaluations remain historical and bound to the
former skill fingerprint; none satisfies the native transcript/tool-trace gate
for the current skill. A targeted current-skill assessment passed three focused
content-forward cases at skill tree
`b984f25dc1462c14dc3153eb307f5953d08821970afdd036022eb3d6cbbf653e`,
but it is not host-native evidence and does not close Q2 or Q3.
One blind test exposed an incomplete Container API artifact-routing rule; the
rule was corrected and a fresh blind retest passed. A later portability review
also found that a standalone skill copy could not reach the top-level blueprint;
an in-skill fail-closed adapter now preserves the standalone contract. The
renewed read-only host-preflight receipt passes source validation through an
explicit cycle-breaking mode at the current skill fingerprint and records
`release_qualified: false`. It detects Codex CLI and Cursor IDE, while Cursor
Agent and Claude Code remain absent. A
reviewed-lock `skills@1.7.0` lifecycle passes
install, filtered list, removal, reinstall, filtered list, and final removal in
one disposable project per agent from the checkout and both verified archives.
The archive runs use a copied verified npm cache with `npm ci --offline`, retain
lock and package-integrity checks, and bind committed exact raw receipts from
their summaries. Two evaluation archives build deterministically with content
manifests: skill-only SHA-256
`1e41859b5ac86522356aa922f177189c3f95a1deaba8dae77d6a95e1cd64ab23`
and full-toolkit SHA-256
`aa332c7555ad88e17f86f99dbd1e33e0f211f48e6e40b980eedb8992c1333790`,
whose internal root is `oci-founder-toolkit/`. The high-confidence secret scan
passes over both release
allowlists and the repository source tree. An offline, read-only Oracle Skills
lock verifier now checks commit, trees, clean-worktree state, and `LICENSE.txt`,
but has not been exercised against a real checkout here. The opt-in
native Codex runner now automates reviewed installer acquisition, exact
project-scoped discovery, one explicit `$oci-founder` FastAPI case, structured
output, an effect trace, cloud/deployment deny shims, clean removal, and a
redacted receipt. That receipt is historical: it recorded Q2/Q3 as `PASS`, and
the current assessment normalizes it to Q2 `PASS_WITH_RESERVATIONS` and Q3
`PARTIAL`. The hardened current runner's 12 unit contracts pass and verified
offline-cache installer acquisition is available, but its fresh native renewal
is `BLOCKED` because a new authenticated model session and external model
egress were not authorized. No model session or cloud mutation occurred in that
renewal. Formal Codex Q2/Q3 remain `BLOCKED`; Cursor Agent and Claude Code are
unavailable. Same-name
deduplication in Cursor, global-profile lifecycle, the remaining native cases,
and licensing remain unresolved. A supported public
release remains `BLOCKED`. A public source evaluation preview exists on `main` at
[`danielgandolfi1984/oracle_founder_pack`](https://github.com/danielgandolfi1984/oracle_founder_pack),
under the restrictive evaluation license, without an immutable tag, GitHub
release, marketplace entry, registry coordinate, or package coordinate. It
does not close legal, OSS, publisher, support, naming/trademark, or Oracle
repository-ownership gates.
The first full public CI baseline passed at `bf5ebb3` in
[run 35355021483](https://github.com/danielgandolfi1984/oracle_founder_pack/actions/runs/35355021483).
After pinning the official Node.js 24 action lines by full SHA and moving to
`ubuntu-24.04`, the founder-onboarding baseline at `deb13d8` passed in
[run 35359228279](https://github.com/danielgandolfi1984/oracle_founder_pack/actions/runs/35359228279).
These exact-revision results close the former remote source-CI item but not
native-host, field, or distribution gates; every later revision still requires
its own passing run.
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

## 1.0 — Public founder release

Release criteria:

- Container API and Function API are stable by the quality gate in `PRODUCT.md`;
- installation and invocation are tested in current Codex, Cursor, and Claude Code;
- at least 80% of representative target users complete a path without maintainer intervention;
- median time to a verified endpoint is below 60 minutes in the usability cohort;
- zero credential leaks and zero unapproved mutations in the release test suite;
- legal, naming, trademark, and license review is complete;
- contribution and upstream-sync ownership is assigned.
- distribution owner, support/security contact, compatibility range, release
  notes, and lifecycle/deprecation policy are published.

## Upstream contribution stream

Service-level gaps discovered by field paths should become focused contributions to `oracle/skills`, including likely gaps around generic Container Instances, private OCIR pull plus scan evidence, founder networking, bounded and centralized Container Instance logging, Vault/resource principals, observability baseline, and secure non-OKE Terraform/Resource Manager workflows. The toolkit should consume those contributions rather than retain permanent duplicates.

## Sources

- https://github.com/oracle/skills
- https://github.com/oracle/skills/blob/main/SKILL_AUTHORING_GUIDE.md
