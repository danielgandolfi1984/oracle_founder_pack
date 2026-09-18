# Founder Toolkit for OCI validation results

Founder Toolkit for OCI is a personal, independent public-preview project
created and maintained by Daniel Gandolfi, an Oracle employee publishing in his
personal capacity. The views expressed here are his own and do not represent
Oracle. This is not an Oracle product and is not sponsored, endorsed,
maintained, or supported by Oracle.

The project's original public content is licensed under the Universal
Permissive License 1.0 (`UPL-1.0`); see [`LICENSE`](../../LICENSE). The internal
Oracle-template presentation remains confidential, is excluded from the public
repository and every public distribution, and is outside this license grant.
These records document public-preview evidence; they do not establish Oracle
qualification, production readiness, or Oracle Support coverage.

This directory records dated behavioral evaluations and machine-readable host
preflight evidence.

A fixture is not considered passing merely because it appears in the JSONL file.
Each result must record the prompt ID, environment, mutations attempted, outcome,
reservations, and reviewer. Never include credentials, private OCIDs, customer
identifiers, or secret values.

## `0.1.1` prepublication records

These `0.1.1` checks were captured before publication. Exact-revision CI,
public-tag installation, and published-asset verification are recorded
separately. The `v0.1.0` tag, assets, and version-bound receipts are unchanged.

- [`2026-09-18-v0.1.1-assessment.json`](2026-09-18-v0.1.1-assessment.json):
  prepublication assessment of focused guidance, an explicitly requested full
  plan, and the native comparison. The current skill tree is
  `dba58d1984513e44aa77a5729a20b16e23186dac00e0de17ef1db01ddd0bda49`;
  formal Q2/Q3 remain blocked.
- [`2026-09-18-v0.1.1-codex-native.json`](2026-09-18-v0.1.1-codex-native.json):
  native comparison using the same prompt, schema, fixture, and binary as the
  `0.1.0` baseline. It passed with reservations: 185 words versus 1,489, two
  reference reads instead of four, all recorded effects false, and clean
  removal. It records expected version `0.1.1`; this is one probe, not the full
  24-case suite.
- [`2026-09-18-v0.1.1-focused-forward.md`](2026-09-18-v0.1.1-focused-forward.md)
  and [`2026-09-18-v0.1.1-full-plan-forward.md`](2026-09-18-v0.1.1-full-plan-forward.md):
  fresh content-forward responses preserving focused guidance (224 words) and
  an explicitly requested ten-section plan (1,890 words), with no file,
  network, or cloud effects.
- [`2026-09-18-host-preflight.json`](2026-09-18-host-preflight.json):
  renewable current source/validator fingerprint and read-only host inventory.
  It records the source identity and skill hash assessed; it is not native
  cross-host qualification.
- [`2026-09-18-v0.1.1-skill-install-lifecycle.json`](2026-09-18-v0.1.1-skill-install-lifecycle.json):
  passing current-source project install/list/remove/reinstall/list/remove in
  separate Codex, Cursor, and Claude Code layouts.
- [`2026-09-18-v0.1.1-skill-package-install-lifecycle.json`](2026-09-18-v0.1.1-skill-package-install-lifecycle.json)
  and [raw receipt](2026-09-18-v0.1.1-skill-package-install-lifecycle.raw.json):
  passing three-layout lifecycle for local skill archive SHA-256
  `6167f1ca7da9a06204e8e0d028622c490b727581532c15ec1d5d78629b2aa8ff`.
- [`2026-09-18-v0.1.1-full-package-install-lifecycle.json`](2026-09-18-v0.1.1-full-package-install-lifecycle.json)
  and [raw receipt](2026-09-18-v0.1.1-full-package-install-lifecycle.raw.json):
  passing three-layout lifecycle for local full-toolkit archive SHA-256
  `7296477c39da42f830edd4e5dee6713288cdef695da0957145f79057cd17218b`.

## Published `0.1.0`, historical, and shared records

- [`2026-09-18-codex-native-postrelease-initial.json`](2026-09-18-codex-native-postrelease-initial.json):
  the initial authorized post-release native Codex probe, retained as `fail`.
  A quoted `rg` pattern exposed a command-parser defect, and the semantic
  assertion required an invocation label absent from the output schema.
  The native response stayed planning-only without cloud mutation. Harness
  fixes were verified in the separate fresh run below; this receipt stays failed.
- [`2026-09-18-codex-native-postrelease.json`](2026-09-18-codex-native-postrelease.json):
  the fresh authorized native Codex `0.153.4` probe after harness fixes. It
  passed with reservations at the unchanged released skill hash, loaded the
  skill and references, returned valid structured output, passed all four
  machine assertions, and removed its project copy cleanly. No project edits,
  unreviewed commands, OCI commands, or cloud mutations were observed. Probe Q2
  is `PASS` and Q3 is `PARTIAL`; formal Q2/Q3 remain `BLOCKED`.
- [`2026-09-18-codex-native-postrelease-assessment.json`](2026-09-18-codex-native-postrelease-assessment.json):
  separate assessment of the failed initial run, harness fixes, fresh probe,
  and independent semantic review. The fresh response passed that review with
  reservations about excessive length and unnecessary reference loading.
  It covers one explicit prompt and reuses the signed-in authentication
  profile; upstream dependencies and the 24-case suite were not part of the
  native session. No formal cross-host qualification is claimed.

- [`2026-09-18-oracle-skills-verified.json`](2026-09-18-oracle-skills-verified.json):
  passing offline verifier receipt for a real checkout of locked upstream
  commit `b0afa3bfd7c7e3547458d7fe52649ab1b59706b7`, including exact HEAD,
  clean worktree, all three reviewed tree IDs, and the `LICENSE.txt` hash.
- [`2026-09-18-oracle-skills-verified-codex-lifecycle.json`](2026-09-18-oracle-skills-verified-codex-lifecycle.json):
  passing isolated OCI-domain Codex install/list/remove/reinstall/list/remove
  with source and installed SHA-256
  `1d339b2826f1d5e5b10df72f2b5b931bb0ea0ec1dc7ed3c81a02e46ef344bb80`.
  All nine domain `SKILL.md` files were retained, both upstream verifier runs
  passed, and four named global OCI targets were unchanged. No model session,
  OCI command, or cloud mutation occurred. The Database domain was verified
  but not installed; sibling references, native discovery, and the whole user
  profile remain outside this result.

- [`2026-09-17-orient-fastapi-gcp.md`](2026-09-17-orient-fastapi-gcp.md):
  orientation and Cloud Run non-equivalence.
- [`2026-09-17-behavioral-contracts.md`](2026-09-17-behavioral-contracts.md):
  the remaining safety, routing, artifact-lineage, and preview-boundary cases.
- [`2026-09-17-host-preflight.json`](2026-09-17-host-preflight.json): read-only
  historical pre-hardening host inventory retained for comparison.
- [`2026-09-18-skill-install-lifecycle.json`](2026-09-18-skill-install-lifecycle.json):
  published `0.1.0` pinned, one-project-per-agent install/list/remove/reinstall evidence
  across Codex, Cursor, and Claude Code layouts, with reviewed npm lock and CLI
  hashes, exact destination/tree matching, residual allowlists, and unchanged
  observed global skill targets. The run uses a copied verified npm cache with
  `npm ci --offline` while retaining lock and package-integrity checks. An empty
  OpenCode config-directory fixture inside the isolated `XDG_CONFIG_HOME` makes
  the shared universal `.agents` removal probe deterministic without starting
  an OpenCode session.
- [`2026-09-18-skill-package-install-lifecycle.json`](2026-09-18-skill-package-install-lifecycle.json):
  skill-only archive summary for project-scoped lifecycle across Codex, Cursor,
  and Claude Code layouts. It records archive SHA-256
  `517c4f6d4d29b35d085d4cf534656608e6c1d7315526563ee632ee5ae9fe7954`,
  verifies skill tree
  `c9ca7081b818f85a248836a53d12b94b6c995da9825696346a1075bf42c2dd37`,
  and binds the committed exact raw receipt by SHA-256.
- [`2026-09-18-skill-package-install-lifecycle.raw.json`](2026-09-18-skill-package-install-lifecycle.raw.json):
  exact redacted skill-only archive lifecycle receipt retained by the summary.
- [`2026-09-18-full-package-install-lifecycle.json`](2026-09-18-full-package-install-lifecycle.json):
  verified full-toolkit archive summary for project-scoped lifecycle across all
  three layouts. It records archive SHA-256
  `33037edf2783895c03a5e40bb03a0f18468a26945dc7fce8a9e251ea7e75ca80`,
  internal root `oci-founder-toolkit/`, and the same `0.1.0` skill tree, and
  binds the committed exact raw receipt by SHA-256.
- [`2026-09-18-full-package-install-lifecycle.raw.json`](2026-09-18-full-package-install-lifecycle.raw.json):
  exact redacted full-toolkit archive lifecycle receipt retained by the
  summary.
- [`2026-09-18-codex-native-probe.json`](2026-09-18-codex-native-probe.json):
  initial manually orchestrated native Codex `0.153.4` project-scoped discovery
  evidence, retained for provenance.
- [`2026-09-18-codex-native-output.json`](2026-09-18-codex-native-output.json):
  schema-valid output produced by that initial probe. Its content hash excluding
  the repository newline is bound by the initial receipt.
- [`2026-09-18-codex-native-runner-probe.json`](2026-09-18-codex-native-runner-probe.json):
  historical automated opt-in native Codex evidence: reviewed installer lock,
  exact copied skill hash, explicit invocation, ephemeral read-only model
  session, structured result, redacted transcript/effect hashes, active
  cloud/deployment deny shims, clean removal, and recorded probe Q2/Q3 `PASS`
  results. The prepublication assessment supersedes those raw classifications.
- [`2026-09-18-codex-native-runner-assessment.json`](2026-09-18-codex-native-runner-assessment.json):
  prepublication assessment of the historical receipt and hardened runner. It records
  12 passing unit contracts, normalizes the historical result to Q2
  `PASS_WITH_RESERVATIONS` and Q3 `PARTIAL`, and records that earlier native
  renewal as `BLOCKED` only because a new authenticated model session and
  external model egress were not authorized. The runner accepts the verified
  offline npm cache for reviewed installer acquisition. That renewal started no
  model session and attempted no cloud mutation; formal Q2/Q3 and release
  qualification remained `BLOCKED`. The post-release native checks were
  subsequently authorized and are assessed separately.
- [`2026-09-18-skill-revision-assessment.json`](2026-09-18-skill-revision-assessment.json):
  targeted assessment of three content-forward cases against `0.1.0` skill tree
  `c9ca7081b818f85a248836a53d12b94b6c995da9825696346a1075bf42c2dd37`.
  All three ran in Codex subagent sessions and passed without file writes,
  network calls, OCI commands, or cloud mutations. This is not host-native
  evidence; formal Q2/Q3, global-profile lifecycle, native Cursor and Claude
  Code qualification, live OCI validation, and release qualification remain
  `BLOCKED`.
- [`2026-09-18-behavioral-case-index.json`](2026-09-18-behavioral-case-index.json):
  historical 24-case prompt hashes, contracts, evaluators, and evidence paths,
  bound to former skill tree
  `746cc9a3462ce96c067eedd91e848a905f04ed402b8f579836ce126c5b4d703f`.
  It records zero native-complete/transcript/tool-trace-bound cases, so the
  formal native gate remains blocked.

The repository-source secret scan passes locally, but it does not create a
result file in this directory. The real-checkout Oracle Skills verification
and its separate installer lifecycle are recorded above.

The published [`v0.1.0` release](https://github.com/danielgandolfi1984/oracle_founder_pack/releases/tag/v0.1.0)
is fixed at commit `6cf08bf30febc434cefed228f53c43a1f8802ec2`, which passed
[GitHub Actions run 35375372149](https://github.com/danielgandolfi1984/oracle_founder_pack/actions/runs/35375372149).
Its public tag passed project-scoped Codex install/list/remove with published
skill tree `c9ca7081b818f85a248836a53d12b94b6c995da9825696346a1075bf42c2dd37`,
and all published assets were downloaded again and verified. Follow-up evidence
on `main` does not alter that tag or its assets. These results establish the
public-preview coordinate; they do not claim native cross-host qualification,
marketplace publication, a registry coordinate, or production readiness.
