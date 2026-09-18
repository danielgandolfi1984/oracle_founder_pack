# Validation record

This document distinguishes evidence for the published `0.1.0` and `0.1.1`
previews, and the separately versioned `0.2.0-preview.3` Container API candidate from
capabilities that remain unverified. It is not a stable-release certification,
an Oracle review, or an Oracle support statement.

## Environment

- Date: 2026-09-18
- Toolkit state: independent public preview licensed under UPL-1.0 and maintained
  by Daniel Gandolfi with best-effort support and no SLA. The published
  [`v0.1.1` release](https://github.com/danielgandolfi1984/oracle_founder_pack/releases/tag/v0.1.1)
  is fixed at commit `8765266e3ef77110b30827d5c89da7cf1b15ee08`, which passed
  [GitHub Actions run 35385557348](https://github.com/danielgandolfi1984/oracle_founder_pack/actions/runs/35385557348).
  Publication verification passed as recorded below; the `v0.1.0` tag and
  assets remain unchanged at commit `6cf08bf30febc434cefed228f53c43a1f8802ec2`.
  The first historical complete remote workflow baseline passed at commit
  [`bf5ebb3`](https://github.com/danielgandolfi1984/oracle_founder_pack/commit/bf5ebb3bef3d53ff03601a05221f7825ecd849f2)
  in [GitHub Actions run 35355021483](https://github.com/danielgandolfi1984/oracle_founder_pack/actions/runs/35355021483); the later founder-onboarding baseline
  [`deb13d8`](https://github.com/danielgandolfi1984/oracle_founder_pack/commit/deb13d83e037704e3aa3894304673ba7a58da68d)
  passed in [run 35359228279](https://github.com/danielgandolfi1984/oracle_founder_pack/actions/runs/35359228279)
- Reviewed Oracle Skills commit: `b0afa3bfd7c7e3547458d7fe52649ab1b59706b7`
- Cloud tenancy used: none
- OCI resources created or changed: none
- Terraform version: `1.16.3`
- Oracle OCI provider version: `9.2.0`
- Codex CLI version: `0.153.4`
- Current `0.1.1` skill tree SHA-256:
  `dba58d1984513e44aa77a5729a20b16e23186dac00e0de17ef1db01ddd0bda49`.
- Published `0.1.0` skill tree SHA-256:
  `c9ca7081b818f85a248836a53d12b94b6c995da9825696346a1075bf42c2dd37`.
  The earlier `b984f25dc1462c14dc3153eb307f5953d08821970afdd036022eb3d6cbbf653e`
  fingerprint is retained only for pre-transition historical evidence.
- Cursor IDE/editor CLI version: `3.0.12`; Cursor Agent CLI absent
- Claude Desktop version: `1.569.0`; Claude Code CLI absent
- Canonical internal presentation: local Git-ignored
  `artifacts/OCI-Founder-Toolkit-Oracle-Template-v11-User-Guide.pptx`, marked
  `Confidential: Internal`
- Public source preview repository:
  [`danielgandolfi1984/oracle_founder_pack`](https://github.com/danielgandolfi1984/oracle_founder_pack);
  source on `main` under UPL-1.0, with `v0.1.1` as the current immutable GitHub
  public-preview tag and prerelease; no marketplace or registry coordinate

## `0.1.1` publication verification

The [GitHub prerelease](https://github.com/danielgandolfi1984/oracle_founder_pack/releases/tag/v0.1.1)
was published on 2026-09-18 at 19:25:13 UTC with six assets. The
[publication receipt](../tests/results/2026-09-18-v0.1.1-publication.json)
binds the release commit, successful exact-revision CI, and redownloaded assets.
The public tag passed Codex install/list/remove/reinstall/final cleanup with
the exact released skill hash in the
[tag lifecycle receipt](../tests/results/2026-09-18-v0.1.1-public-tag-lifecycle.json).
Both downloaded archives passed `build_release.py verify` with the same
skill-only and full-toolkit hashes recorded below.
These checks qualify the publication coordinate, not the remaining native
cross-host or live OCI gates. Later `main` commits need their own CI result.

## `0.1.1` prepublication evidence

These checks were captured before publication and remain unchanged. The
completed publication checks are recorded above. Existing `0.1.0` receipts retain their original hashes and results;
they do not qualify this revision. See the
[prepublication assessment](../tests/results/2026-09-18-v0.1.1-assessment.json).

| Check | Result | Evidence |
|---|---|---|
| Focused and full-plan evaluations | Both passed; non-native | Fresh content-forward sessions produced [focused Portuguese guidance](../tests/results/2026-09-18-v0.1.1-focused-forward.md) of 224 words without a full plan or `use-cases` read, and a [requested ten-section founder plan](../tests/results/2026-09-18-v0.1.1-full-plan-forward.md) of 1,890 words. Neither session changed files, used network access, or ran cloud commands |
| Native Codex comparison | Passed with reservations; probe Q2 `PASS`, Q3 `PARTIAL` | The same prompt, schema, fixture, and Codex binary produced a 185-word recommendation versus 1,489 words for `0.1.0`, reading `discovery` and `golden-paths` instead of four references. Counts cover the recommendation field, excluding separate guardrails and evidence fields. This is one comparison, not a benchmark. Structured output, machine assertions, and independent semantic review passed. All recorded effects were false and removal was clean. [Native receipt](../tests/results/2026-09-18-v0.1.1-codex-native.json) |
| Local source checks | Passed | Repository validation passed 1,591 checks, all 109 toolkit unit tests and 45 Container API tests passed, and the source secret scan found no high-confidence secrets. Both archive builds remained deterministic |
| Read-only host preflight | Passed with native-host reservations | The [renewed receipt](../tests/results/2026-09-18-host-preflight.json) binds the 0.1.1 skill and manifests and the final validator source. Skill Creator and Plugin Creator validators passed; native Cursor/Claude surfaces remain unavailable and `release_qualified` remains `false` |
| Source installation lifecycle | Passed across three layouts | Exact current skill hash matched each Codex, Cursor, and Claude Code project installation through install/list/remove/reinstall/list/remove. [Receipt](../tests/results/2026-09-18-v0.1.1-skill-install-lifecycle.json) |
| Local skill-only package lifecycle | Passed across three layouts | Archive SHA-256 `6167f1ca7da9a06204e8e0d028622c490b727581532c15ec1d5d78629b2aa8ff`. [Summary](../tests/results/2026-09-18-v0.1.1-skill-package-install-lifecycle.json) and [raw receipt](../tests/results/2026-09-18-v0.1.1-skill-package-install-lifecycle.raw.json) |
| Local full-toolkit package lifecycle | Passed across three layouts | Archive SHA-256 `7296477c39da42f830edd4e5dee6713288cdef695da0957145f79057cd17218b`. [Summary](../tests/results/2026-09-18-v0.1.1-full-package-install-lifecycle.json) and [raw receipt](../tests/results/2026-09-18-v0.1.1-full-package-install-lifecycle.raw.json) |

Formal Q2/Q3, native cross-host replay, fully isolated profiles, and live OCI
field qualification remain open.

## Published `0.1.0` baseline and shared evidence

The skill-bound receipts below describe `0.1.0` or their explicitly recorded
earlier fingerprint. Oracle upstream verification remains a separate dependency
check. Historical local check counts are not counts for `0.1.1`.

| Check | Result | Evidence |
|---|---|---|
| Dependency-free repository validation | Passed for the post-release update | `python3 scripts/validate.py` passed 1,499 checks after the documentation, runner, and evidence update. Coverage includes manifests and schema, standalone-skill closure, links and local JSON, package/evidence freshness, secret scanning, and the historical behavioral coverage index. All 98 toolkit unit tests and 45 Container API blueprint tests also passed; this is local validation, not native cross-host or live OCI qualification |
| Host-preflight unit contracts | Passed | Tests cover fingerprints, path redaction, safe Cursor probing, Codex validator classification, secret-dropping subprocess environment, explicit validator dependencies, atomic output, overwrite refusal, and symlink rejection |
| Published `0.1.0` source install lifecycle | Passed with native-host reservations | The recorded source run used the reviewed dependency lock, verified CLI hashes, and a copied npm cache with `npm ci --offline`. Separate Codex, Cursor, and Claude Code project layouts passed install, filtered list, removal, reinstall, filtered list, and final removal at skill tree `c9ca7081b818f85a248836a53d12b94b6c995da9825696346a1075bf42c2dd37`. Cursor duplicate discovery, global lifecycle, and native Cursor/Claude visibility remain open. Evidence: [`tests/results/2026-09-18-skill-install-lifecycle.json`](../tests/results/2026-09-18-skill-install-lifecycle.json) |
| Published skill validation | Passed | Skill Creator `quick_validate.py` returned `Skill is valid!` against the `0.1.0` public-preview skill using the explicit development-validator runtime |
| Codex plugin manifest validation | Passed | Plugin Creator `validate_plugin.py` returned `Plugin validation passed` against the current UPL/publisher manifests. Codex CLI `0.153.4` exposes plugin management but no native `plugin validate` |
| Agent Plugins v1 schema | Passed | Root `plugin.json` passed the vendored published `1.0.0` schema snapshot as part of the 1,437-check pre-release repository validation and the exact-release CI run 35375372149 at `6cf08bf` |
| Published v0.1.0 source CI | Passed for the immutable release commit | [Run 35375372149](https://github.com/danielgandolfi1984/oracle_founder_pack/actions/runs/35375372149) succeeded for `6cf08bf30febc434cefed228f53c43a1f8802ec2`. Later commits on `main` need their own CI result |
| Published tag installation and release assets | Passed | The immutable public `v0.1.0` tag passed project-scoped Codex install/list/remove; the installed skill tree was `c9ca7081b818f85a248836a53d12b94b6c995da9825696346a1075bf42c2dd37`. All release assets were downloaded again and verified against the published checksums and manifests. The [GitHub release](https://github.com/danielgandolfi1984/oracle_founder_pack/releases/tag/v0.1.0) is available; native host qualification is a separate gate |
| Public GitHub Actions baselines | Passed for the recorded revisions | [Run 35355021483](https://github.com/danielgandolfi1984/oracle_founder_pack/actions/runs/35355021483) completed successfully for `bf5ebb3bef3d53ff03601a05221f7825ecd849f2`, including repository/schema/secret checks, both unit suites, deterministic package verification, source and archive install lifecycles, and Terraform format/init/validate. It emitted runner migration warnings. The workflow was then pinned to `ubuntu-24.04` and official Node.js 24 action lines by full commit SHA; [run 35359228279](https://github.com/danielgandolfi1984/oracle_founder_pack/actions/runs/35359228279) passed that updated workflow for `deb13d83e037704e3aa3894304673ba7a58da68d` |
| Deterministic published `0.1.0` packages | Passed | The published archives were rebuilt deterministically and verified: skill-only SHA-256 `517c4f6d4d29b35d085d4cf534656608e6c1d7315526563ee632ee5ae9fe7954` and full-toolkit SHA-256 `33037edf2783895c03a5e40bb03a0f18468a26945dc7fce8a9e251ea7e75ca80`. The earlier `1e41859b5ac86522356aa922f177189c3f95a1deaba8dae77d6a95e1cd64ab23` and `aa332c7555ad88e17f86f99dbd1e33e0f211f48e6e40b980eedb8992c1333790` values are historical pre-transition hashes only |
| Packaged archive install lifecycle | Passed with native-host reservations | Both renewed public-preview archives passed project-scoped install/list/remove/reinstall/list/remove in isolated Codex, Cursor, and Claude Code layouts at skill tree `c9ca7081b818f85a248836a53d12b94b6c995da9825696346a1075bf42c2dd37`. Exact raw receipts and summaries are committed; native host discovery and global-profile lifecycle remain separate. The public-tag check is recorded above. Evidence: [skill-only summary](../tests/results/2026-09-18-skill-package-install-lifecycle.json), [skill-only raw](../tests/results/2026-09-18-skill-package-install-lifecycle.raw.json), [full-toolkit summary](../tests/results/2026-09-18-full-package-install-lifecycle.json), and [full-toolkit raw](../tests/results/2026-09-18-full-package-install-lifecycle.raw.json) |
| Real Oracle Skills lock verification | Passed | A fresh public `oracle/skills` checkout at locked commit `b0afa3bfd7c7e3547458d7fe52649ab1b59706b7` passed before and after the installation lifecycle: exact HEAD, clean worktree, all three reviewed tree IDs, and `LICENSE.txt` hash. The verifier itself used no network or mutation. Evidence: [verification receipt](../tests/results/2026-09-18-oracle-skills-verified.json) |
| Verified upstream OCI domain lifecycle | Passed with scope reservations | The reviewed `skills@1.7.0` runtime used a copied npm cache and `npm ci --offline --ignore-scripts`. A disposable Codex project passed install/list/remove/reinstall/list/remove with exact OCI source/installed SHA-256 `1d339b2826f1d5e5b10df72f2b5b931bb0ea0ec1dc7ed3c81a02e46ef344bb80` and all nine domain `SKILL.md` files retained. Four named global OCI targets were unchanged. No model session, OCI command, or cloud mutation occurred. Native discovery, sibling `db` navigation, and the rest of the user profile were not qualified. Evidence: [lifecycle receipt](../tests/results/2026-09-18-oracle-skills-verified-codex-lifecycle.json) |
| Hardened native Codex runner unit contracts | Passed | The runner contracts cover offline-cache parsing, response and semantic contracts, command/path rejection, effect accounting, deny-shim detection and fail-closed behavior, installed-skill binding, redaction, and clean removal. Post-release fixes also cover quoted shell syntax and explicit invocation schema semantics |
| Historical native Codex receipt and prepublication assessment | Q2 `PASS_WITH_RESERVATIONS`; Q3 `PARTIAL`; formal gates blocked | The historical Codex CLI `0.153.4` receipt recorded probe Q2/Q3 as `PASS`, exact copied-skill identity, structured founder guidance, deny shims, clean removal, and no observed forbidden or cloud-mutation effect. The prepublication assessment normalizes Q2 to `PASS_WITH_RESERVATIONS` and Q3 to `PARTIAL`. Its attempted renewal stopped before model execution because authorization had not yet been given; that restriction was superseded for the post-release checks. The historical attempt started no model session and attempted no cloud mutation. Evidence: [historical receipt](../tests/results/2026-09-18-codex-native-runner-probe.json) and [prepublication assessment](../tests/results/2026-09-18-codex-native-runner-assessment.json) |
| Initial authorized post-release Codex probe | Failed harness checks; retained | The native session ran against the unchanged released skill and produced a planning-only response without cloud mutation. The harness misparsed a quoted `rg` pattern and required an invocation label that its output schema had not specified. This failed receipt is retained unchanged; the fixes were tested in the separate fresh run below. Evidence: [initial receipt](../tests/results/2026-09-18-codex-native-postrelease-initial.json) |
| Fresh post-release native Codex probe | Passed with reservations; probe Q2 `PASS`, Q3 `PARTIAL` | Codex CLI `0.153.4` exited successfully after loading the exact released skill and references. Structured output was valid and all four machine assertions passed. No project edits, source changes, unreviewed commands, OCI commands, cloud mutations, or changes to the observed global skill targets were recorded; removal was clean. This is one explicit safety/schema prompt using the signed-in profile for authentication, without upstream dependencies in the model session or the 24-case replay. Formal Q2/Q3 remain `BLOCKED` and `release_qualified` remains `false`. Evidence: [fresh receipt](../tests/results/2026-09-18-codex-native-postrelease.json) and [post-release assessment](../tests/results/2026-09-18-codex-native-postrelease-assessment.json) |
| Independent review of the fresh native response | Passed with reservations | The response correctly used fixture evidence, identified the health-check mismatch, kept Vault conditional, surfaced decision-changing unknowns, and preserved mutation boundaries. The reviewer noted excessive length for a focused recommendation and an unnecessary `use-cases` reference read. Current OCI service claims remained explicitly unverified. This single-response review does not grade the 24-case suite. Evidence: [post-release assessment](../tests/results/2026-09-18-codex-native-postrelease-assessment.json) |
| Targeted published `0.1.0` assessment | Three content-forward cases passed; formal native gates blocked | Focused-answer routing, skill-only upstream fail-closed behavior, and full-toolkit verification-first Cursor routing passed in Codex subagent sessions against published skill tree `c9ca7081b818f85a248836a53d12b94b6c995da9825696346a1075bf42c2dd37`. The assessment used no network, file write, OCI command, or cloud mutation. It is historical, non-native evidence and does not close Q2 or Q3. Evidence: [`tests/results/2026-09-18-skill-revision-assessment.json`](../tests/results/2026-09-18-skill-revision-assessment.json) |
| Standalone-skill package closure | Passed | The Container API route now resolves to an adapter inside the copied skill and fails closed when the full toolkit blueprint is absent |
| Static safety and secret review | Passed for the release source | Preview, approval, least-privilege, exact-target teardown, delegated-skill, and tenancy-target gates were exercised. The high-confidence scan passed over the public-preview package allowlists and repository source tree |
| Historical independent founder-plan evaluation | Passed with reservations as supporting evidence | Safe planning response, no mutation, and correct Cloud Run non-equivalence, bound to the former skill fingerprint; it is not current-skill native evidence. Evidence: [`tests/results/2026-09-17-orient-fastapi-gcp.md`](../tests/results/2026-09-17-orient-fastapi-gcp.md) |
| Historical behavioral prompt evaluation | Prior 24-case results indexed; native gate blocked | The coverage index and recorded results are bound to the former skill fingerprint. It explicitly records zero native-complete, transcript-bound, or tool-trace-bound cases, so it cannot close Q3 or represent the current skill. Evidence: [`tests/results/2026-09-18-behavioral-case-index.json`](../tests/results/2026-09-18-behavioral-case-index.json) |
| Author's internal source cross-check | Completed with follow-up technical gates | Daniel Gandolfi reviewed selected authorized internal Oracle sources read-only as an individual accuracy cross-check. This was not an Oracle review or approval. It confirmed sandbox boundaries and identified the scan, production ingress, cost-governance, remote-state, logging, and plugin-governance gaps below; no internal-only content was copied into the public repository or packages |
| Relative links and local JSON | Passed for the release source | Covered by `scripts/validate.py`; post-release documentation and evidence require a fresh run |
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
  `oracle/skills` dependencies installed. The fresh post-release founder probe
  passes its narrower discovery check but reuses the signed-in profile for
  authentication and does not install those dependencies in the native session.
- Global-profile lifecycle. The real user profile was intentionally not changed.
- Native discovery and cross-domain navigation for the reviewed Oracle Skills
  dependencies. The real checkout verification and isolated OCI-domain Codex
  lifecycle passed, but `db` was not installed and the existing global OCI
  skill was not isolated from a native session.
- Re-review and repin the workflow action SHAs and runner image deliberately as
  their upstream support windows change. The current workflow uses official
  Node.js 24 action lines and `ubuntu-24.04`; every later source revision still
  needs its own successful remote run.
- Remote CI for follow-up commits on `main`. The immutable `v0.1.0` release
  commit passed run 35375372149; that result does not cover later revisions.
- Formal Codex Q3 and full native replay of the behavioral prompt fixtures on
  the current skill across Codex, Cursor, and Claude Code, with deny shims,
  transcript/tool-trace binding, and independent semantic grading. The older
  24-case index is bound to the former skill fingerprint, and the targeted
  three-case `0.1.0` assessment is not a native natural-language replay.
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
- Marketplace or registry publication. Distribution signing/SBOM policy and
  hardened artifact provenance remain promotion gates for a stable release;
  the documented compatibility and lifecycle boundaries for the `v0.1.0`
  GitHub coordinate describe a public preview only.
- The under-60-minute endpoint target.
- Broader usability evidence for conciseness and progressive disclosure. The
  `0.1.1` native comparison and focused/full-plan evaluations address the earlier
  verbosity finding, but one native comparison and two content-forward cases
  do not establish full-suite coverage or founder completion targets.

## Source reconciliation on 2026-09-17

Daniel Gandolfi searched authorized internal Oracle knowledge sources and
reviewed selected current materials read-only as an individual accuracy
cross-check. This was not an Oracle review, endorsement, or approval. A follow-up review on
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

## Stable-release gate

The public source preview is usable under UPL-1.0 now, but do not describe it as
generally available, Oracle-supported, production-qualified, or cross-host
certified. A stable release requires native install/runtime tests on Codex,
Cursor, and Claude Code; native cross-host replay of the behavioral suite; and,
for executable paths, the apply/verify/idempotency/rollback/teardown quality
gate in
[`PRODUCT.md`](PRODUCT.md). Follow the Q0–Q4 evidence contract in
[`HOST-QUALIFICATION.md`](HOST-QUALIFICATION.md). Do not treat the preview's
local receipt files as signed deployment attestations.
