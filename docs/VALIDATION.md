# Validation record

This document distinguishes evidence collected for the `0.1.0` evaluation draft
and the separately versioned `0.2.0-preview.3` Container API candidate from
capabilities that remain unverified. It is not a release certification.

## Environment

- Date: 2026-09-18
- Toolkit state: locally validated source evaluation prepared for public `main`;
  this dated record predates any successful remote CI claim
- Reviewed Oracle Skills commit: `b0afa3bfd7c7e3547458d7fe52649ab1b59706b7`
- Cloud tenancy used: none
- OCI resources created or changed: none
- Terraform version: `1.16.3`
- Oracle OCI provider version: `9.2.0`
- Codex CLI version: `0.153.4`
- Current skill tree SHA-256:
  `b984f25dc1462c14dc3153eb307f5953d08821970afdd036022eb3d6cbbf653e`
- Cursor IDE/editor CLI version: `3.0.12`; Cursor Agent CLI absent
- Claude Desktop version: `1.569.0`; Claude Code CLI absent
- Canonical internal presentation: local Git-ignored
  `artifacts/OCI-Founder-Toolkit-Oracle-Template-v11-User-Guide.pptx`, marked
  `Confidential: Internal`
- Public source evaluation repository:
  [`danielgandolfi1984/oracle_founder_pack`](https://github.com/danielgandolfi1984/oracle_founder_pack);
  source preview on `main` under the restrictive evaluation license, with no
  immutable tag, GitHub release, marketplace, registry, or package coordinate

## Evidence collected

| Check | Result | Evidence |
|---|---|---|
| Dependency-free repository validation | Passed | `python3 scripts/validate.py` covers standalone-skill closure, package/evidence freshness, and the machine-readable historical behavioral coverage index; host-preflight renewal uses the explicit cycle-breaking mode before the full evidence check |
| Host-preflight unit contracts | Passed | Tests cover fingerprints, path redaction, safe Cursor probing, Codex validator classification, secret-dropping subprocess environment, explicit validator dependencies, atomic output, overwrite refusal, and symlink rejection |
| Read-only host preflight | Passed as current inventory; release blocked | The fresh receipt passes source validation in the explicit cycle-breaking mode at current skill tree `b984f25dc1462c14dc3153eb307f5953d08821970afdd036022eb3d6cbbf653e`. It detected Codex CLI and Cursor IDE; Cursor Agent and Claude Code were absent. No install, model session, OCI command, host-configuration change, or cloud mutation occurred, and `release_qualified` remains `false`. Evidence: [`tests/results/2026-09-18-host-preflight.json`](../tests/results/2026-09-18-host-preflight.json) |
| Isolated project install lifecycle | Passed with native-host reservations | A reviewed dependency lock and CLI hashes gate execution of `skills@1.7.0`. The renewed run copied a verified npm cache and used `npm ci --offline` while retaining lock and package-integrity checks. Separate Codex, Cursor, and Claude Code projects each passed install, filtered list, removal, reinstall, filtered list, and final removal with exact destination and tree-hash checks. Residual allowlists passed; observed global skill targets remained unchanged. Cursor duplicate discovery, global lifecycle, and native Cursor/Claude visibility remain open. Evidence: [`tests/results/2026-09-18-skill-install-lifecycle.json`](../tests/results/2026-09-18-skill-install-lifecycle.json) |
| Portable skill validation | Passed | Skill Creator `quick_validate.py` returned `Skill is valid!` using explicit PyYAML `6.0.2`; reviewed macOS/Python 3.9 and Linux/Python 3.12 wheel hashes are pinned in `requirements-validation.txt` |
| Codex plugin manifest validation | Passed with CLI limitation | Plugin Creator `validate_plugin.py` returned `Plugin validation passed` with the same explicit dependency runtime; Codex CLI `0.153.4` exposes plugin management but no native `plugin validate` |
| Agent Plugins v1 schema | Passed locally; workflow configured | Root `plugin.json` passes the vendored published `1.0.0` schema snapshot. The snapshot hash and Apache-2.0 provenance are recorded, and the dependency-free check is in the GitHub Actions workflow. No successful remote CI run is claimed by this dated record |
| Deterministic evaluation packages | Passed | Two clean builds are byte-for-byte identical. Skill-only SHA-256: `876fe40dbac703b092110f106f6797fa7eaa753c6bb9b711e61e67f61c2fd315`. Full-toolkit SHA-256: `62501591cdc53b2e366dd7fbe39c7c87a47a838ff034ff7ad734040d1f96eaa8`, with internal root `oci-founder-toolkit/`. Both archives reject symlinks/unexpected members and include checksum plus per-file manifests; presentations, development output, secrets, state, plans, receipts, and caches are excluded |
| Packaged archive install lifecycle | Passed with native-host reservations | Both current verified archives passed project-scoped install/list/remove/reinstall/list/remove in isolated Codex, Cursor, and Claude Code layouts, with installed skill tree `b984f25dc1462c14dc3153eb307f5953d08821970afdd036022eb3d6cbbf653e` and clean residuals. Each renewed summary hash-binds its committed exact raw receipt. Evidence: [skill-only summary](../tests/results/2026-09-18-skill-package-install-lifecycle.json), [skill-only raw](../tests/results/2026-09-18-skill-package-install-lifecycle.raw.json), [full-toolkit summary](../tests/results/2026-09-18-full-package-install-lifecycle.json), and [full-toolkit raw](../tests/results/2026-09-18-full-package-install-lifecycle.raw.json) |
| Offline Oracle Skills lock verifier | Available; real-checkout run not completed | `python3 scripts/verify_oracle_skills_lock.py --checkout /absolute/path/to/oracle-skills-reviewed` checks the locked commit, reviewed trees, clean worktree, and `LICENSE.txt` through Git object reads without network or mutation. It has not been run against a real checkout in this workspace |
| Hardened native Codex runner unit contracts | Passed | All 12 current unit contracts pass, covering offline-cache parsing, response and semantic contracts, command/path rejection, effect accounting, deny-shim detection and fail-closed behavior, installed-skill binding, redaction, and clean removal |
| Historical native Codex receipt and current assessment | Q2 `PASS_WITH_RESERVATIONS`; Q3 `PARTIAL`; formal gates blocked | The historical Codex CLI `0.153.4` receipt recorded probe Q2/Q3 as `PASS`, exact copied-skill identity, structured founder guidance, deny shims, clean removal, and no observed forbidden or cloud-mutation effect. The current assessment normalizes Q2 to `PASS_WITH_RESERVATIONS` and Q3 to `PARTIAL`. Verified offline-cache installer acquisition is available; a fresh hardened rerun is `BLOCKED` only because a new authenticated model session and external model egress were not authorized. It started no model session and attempted no cloud mutation. Formal Q2 and Q3 remain `BLOCKED`. Evidence: [historical receipt](../tests/results/2026-09-18-codex-native-runner-probe.json) and [current assessment](../tests/results/2026-09-18-codex-native-runner-assessment.json) |
| Targeted current-skill revision assessment | Three content-forward cases passed; formal gates blocked | Focused-answer routing, skill-only upstream fail-closed behavior, and full-toolkit verification-first routing passed in Codex subagent sessions against skill tree `b984f25dc1462c14dc3153eb307f5953d08821970afdd036022eb3d6cbbf653e`. The assessment used no network, file write, OCI command, or cloud mutation; it is not host-native evidence. Evidence: [`tests/results/2026-09-18-skill-revision-assessment.json`](../tests/results/2026-09-18-skill-revision-assessment.json) |
| Standalone-skill package closure | Passed | The Container API route now resolves to an adapter inside the copied skill and fails closed when the full toolkit blueprint is absent |
| Static safety and secret review | Passed locally with no recorded critical/high finding | Preview, approval, least-privilege, exact-target teardown, delegated-skill, and tenancy-target gates were exercised; the high-confidence scan passes over both exact package allowlists and the repository source tree |
| Historical independent founder-plan evaluation | Passed with reservations as supporting evidence | Safe planning response, no mutation, and correct Cloud Run non-equivalence, bound to the former skill fingerprint; it is not current-skill native evidence. Evidence: [`tests/results/2026-09-17-orient-fastapi-gcp.md`](../tests/results/2026-09-17-orient-fastapi-gcp.md) |
| Historical behavioral prompt evaluation | Prior 24-case results indexed; native gate blocked | The coverage index and recorded results are bound to the former skill fingerprint. It explicitly records zero native-complete, transcript-bound, or tool-trace-bound cases, so it cannot close Q3 or represent the current skill. Evidence: [`tests/results/2026-09-18-behavioral-case-index.json`](../tests/results/2026-09-18-behavioral-case-index.json) |
| Internal Oracle source review | Passed with follow-up gates | Read-only searches and selected-document review across authorized internal Oracle knowledge sources confirmed the sandbox boundaries and identified the scan, production ingress, cost-governance, remote-state, logging, and plugin-governance gaps below; no internal-only content was copied into the distributable repository |
| Relative links and local JSON | Passed | Covered by `scripts/validate.py` |
| Container API unit contracts | Passed | The unit suite covers the HTTP contract, config rejection, plan redaction/blocking, concrete and unknown relationship attacks, exact provider/reference bindings, observability state relationships, saved-plan/source-snapshot provenance, repository derivation, receipt lineage, symlink-safe artifact writing, and exact teardown/readback reconciliation including child container/VNIC IDs |
| Terraform formatting | Passed | `terraform fmt -check -recursive blueprints/container-api/terraform` |
| Bootstrap Terraform validation | Passed | Offline provider-schema validation with Terraform `1.16.3` and OCI provider `9.2.0` |
| Runtime Terraform validation | Passed | Offline provider-schema validation with Terraform `1.16.3` and OCI provider `9.2.0` |
| Provider lock portability | Passed locally | Lock files are identical and include signed packages for Darwin/Linux on amd64/arm64; CI is configured to initialize with `-lockfile=readonly` |

## Not yet verified

- Cursor native plugin installation and runtime behavior. Cursor IDE and its
  editor CLI are present, but `cursor-agent` is absent and the editor CLI exposes
  no native plugin validator. Cursor also scans universal, Cursor, Claude, and
  Codex skill directories; same-name deduplication remains unqualified. The app
  wrapper must not be probed with `cursor agent` because it may download the
  missing agent.
- Claude Code `claude plugin validate . --strict`, installation, and runtime
  behavior. Claude Desktop is present, but the Claude Code CLI is not.
- Formal Codex Q2 in a fully disposable OS profile with the reviewed
  `oracle/skills` dependencies installed. The historical project-scoped receipt
  normalizes to `PASS_WITH_RESERVATIONS`; a fresh hardened renewal is `BLOCKED`
  only because a new authenticated model session and external model egress were
  not authorized. Verified offline-cache installer acquisition is available. It
  started no model session and attempted no cloud mutation.
- Global-profile lifecycle. The real user profile was intentionally not changed.
- The offline Oracle Skills lock verifier has not been run against a real
  `oracle/skills` checkout in this workspace. Its implementation is not a
  substitute for a passing checkout-bound receipt.
- A successful GitHub Actions run for the public source commit. Actions are
  pinned by commit SHA and the workflow includes schema, secret,
  package-determinism, installer-lifecycle, unit, and Terraform gates, but this
  dated local record does not claim a completed remote run.
- Formal Codex Q3 and full native replay of the behavioral prompt fixtures on
  the current skill across Codex, Cursor, and Claude Code, with deny shims,
  transcript/tool-trace binding, and independent semantic grading. The older
  24-case index is bound to the former skill fingerprint, and the targeted
  three-case current-skill assessment is not a native natural-language replay.
- Any authenticated Terraform plan, apply, second-plan idempotency, rollback,
  or destroy behavior in an OCI tenancy. Local format and provider-schema
  validation are not field evidence.
- Any image build, SBOM/provenance output, OCIR push, private image pull, VCN DNS
  behavior, Vulnerability Scanning result for the exact digest, proof of the
  digest actually pulled, or container process execution on OCI.
- API Gateway service-log availability under the configured Logging service
  identifier in the target region.
- Container metrics, alarm firing, Notifications email confirmation, budget
  alert delivery, or exact-ID post-destroy inventory.
- Any OCI region, quota, pricing, IAM, or service behavior in a live tenancy.
- Production API Gateway authentication/authorization, custom certificate and
  domain ownership, Vault integration, verified Audit search/export, or central
  security-log routing. OCI Audit is automatic for supported public API calls;
  this gate is about verifying access and routing, not enabling Audit.
- Defined-tag cost governance, forecast alerts, usage-report/Cloud Advisor
  review, and quota baselines.
- A tested OCI Resource Manager/remote-state variant. Current public Oracle
  documentation identifies the operational Resource Manager line as Terraform
  `1.5.x` (runtime `1.5.7`), so this repository's exact `1.16.3` pin is **not
  Resource Manager compatible** and no such compatibility claim is made.
- Centralized Container Instance application stdout/stderr ingestion; the
  current preview intentionally offers only bounded on-demand retrieval.
- Approved distribution owner, publisher identity, support/security contacts,
  compatibility range, signing/SBOM policy, and lifecycle/deprecation policy
  for a supported plugin release. Evaluation changelog and release checklist now
  exist but do not authorize publication.
- An approved open-source/public-use license and the remaining publisher,
  naming/trademark, support, security, and Oracle repository-ownership gates.
  Public source availability under restrictive evaluation terms does not close
  them, and no immutable tag, GitHub release, marketplace entry, registry
  coordinate, or package coordinate exists.
- The under-60-minute endpoint target.
- Public naming, trademark, security, legal, and open-source approval.

## Source reconciliation on 2026-09-17

Authorized internal Oracle knowledge sources were searched and selected current
materials were reviewed read-only. A follow-up review on
2026-09-17 also challenged the packaging and developer-onboarding flow. It
reinforced the need for one portable capability package, explicit context and
permissions, pinned compatibility, clear onboarding completion criteria, and a
traceable install/update/removal lifecycle. No internal-only policy text,
identifiers, retention values, or organization-specific workflow was copied
here. Every resulting OCI service claim below was then checked against current
public Oracle documentation:

- OCIR scanning is not enabled merely by creating a repository. The documented
  scan-result API does not expose a direct digest filter, so future evidence must
  correlate the reviewed digest, OCIR image OCID, and scan-result OCID rather
  than claim a single “scan by digest” lookup.
- The default Oracle-managed API Gateway certificate path is documented only in
  realm OC1. Public production designs need explicit custom certificate/domain,
  authentication, and logging/security review; this anonymous preview is not
  that design.
- Budgets alert but do not cap spend. `ACTUAL` and `FORECAST` rules exist, while
  defined cost-tracking tags and compartment quotas are governance additions
  still absent from this preview.
- Resource Manager currently accepts the `1.5.x` operational line, not this
  blueprint's `1.16.3` pin. A separate compatible variant is required.
- Container Instance log retrieval returns only the most recent 256 KB. It is
  troubleshooting evidence, not centralized application-log retention.

Public evidence: [OCIR image scanning](https://docs.oracle.com/en-us/iaas/Content/Registry/Tasks/registryscanningimagesforvulnerabilities.htm),
[scan-result CLI](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/vulnerability-scanning/container/scan/result/list.html),
[API Gateway custom domains and certificates](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewaysettingupcustomdomainscerts.htm),
[Audit overview](https://docs.oracle.com/en-us/iaas/Content/Audit/Concepts/auditoverview.htm),
[Budgets overview](https://docs.oracle.com/en-us/iaas/Content/Billing/Concepts/budgetsoverview.htm),
[Resource Manager Terraform versions](https://docs.oracle.com/en-us/iaas/Content/ResourceManager/Reference/terraformversions.htm),
and [Container Instance log retrieval](https://docs.oracle.com/en-us/iaas/Content/container-instances/retrieve-logs.htm).

## Release gate

Do not describe this draft as generally available or cross-host certified. A
public release requires native install/runtime tests on Codex, Cursor, and Claude
Code; native cross-host replay of the behavioral suite; an approved license; and, for executable paths,
the apply/verify/idempotency/rollback/teardown quality gate in
[`PRODUCT.md`](PRODUCT.md). Follow the Q0–Q4 evidence contract in
[`HOST-QUALIFICATION.md`](HOST-QUALIFICATION.md). Do not treat the preview's
local receipt files as signed deployment attestations.
