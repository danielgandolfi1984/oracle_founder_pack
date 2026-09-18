# Validation results

This directory records dated behavioral evaluations and machine-readable host
preflight evidence.

A fixture is not considered passing merely because it appears in the JSONL file.
Each result must record the prompt ID, environment, mutations attempted, outcome,
reservations, and reviewer. Never include credentials, private OCIDs, customer
identifiers, or secret values.

## Current and historical records

- [`2026-09-17-orient-fastapi-gcp.md`](2026-09-17-orient-fastapi-gcp.md):
  orientation and Cloud Run non-equivalence.
- [`2026-09-17-behavioral-contracts.md`](2026-09-17-behavioral-contracts.md):
  the remaining safety, routing, artifact-lineage, and preview-boundary cases.
- [`2026-09-17-host-preflight.json`](2026-09-17-host-preflight.json): read-only
  historical pre-hardening host inventory retained for comparison.
- [`2026-09-18-host-preflight.json`](2026-09-18-host-preflight.json): current
  read-only host inventory, source and validator-runtime fingerprints,
  environment-allowlist policy, passing development validators, and explicit
  no-install/no-model/no-cloud-mutation evidence. The fresh receipt passes source
  validation through the explicit cycle-breaking mode at current skill tree
  `b984f25dc1462c14dc3153eb307f5953d08821970afdd036022eb3d6cbbf653e`
  and retains `release_qualified: false`.
- [`2026-09-18-skill-install-lifecycle.json`](2026-09-18-skill-install-lifecycle.json):
  pinned, one-project-per-agent install/list/remove/reinstall evidence with
  reviewed npm lock and CLI hashes, exact destination/tree matching, residual
  allowlists, and unchanged observed global skill targets. The renewed run uses
  a copied verified npm cache with `npm ci --offline` while retaining lock and
  package-integrity checks. An empty OpenCode config-directory fixture inside
  the isolated `XDG_CONFIG_HOME` makes the shared universal `.agents` removal
  probe deterministic without starting an OpenCode session.
- [`2026-09-18-skill-package-install-lifecycle.json`](2026-09-18-skill-package-install-lifecycle.json):
  skill-only archive summary for project-scoped lifecycle across Codex, Cursor,
  and Claude Code layouts. It records archive SHA-256
  `876fe40dbac703b092110f106f6797fa7eaa753c6bb9b711e61e67f61c2fd315`,
  verifies skill tree
  `b984f25dc1462c14dc3153eb307f5953d08821970afdd036022eb3d6cbbf653e`,
  and binds the committed exact raw receipt by SHA-256.
- [`2026-09-18-skill-package-install-lifecycle.raw.json`](2026-09-18-skill-package-install-lifecycle.raw.json):
  exact redacted skill-only archive lifecycle receipt retained by the summary.
- [`2026-09-18-full-package-install-lifecycle.json`](2026-09-18-full-package-install-lifecycle.json):
  verified full-toolkit archive summary for project-scoped lifecycle across all
  three layouts. It records archive SHA-256
  `62501591cdc53b2e366dd7fbe39c7c87a47a838ff034ff7ad734040d1f96eaa8`,
  internal root `oci-founder-toolkit/`, and the same current skill tree, and
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
  results. The current assessment supersedes those raw classifications.
- [`2026-09-18-codex-native-runner-assessment.json`](2026-09-18-codex-native-runner-assessment.json):
  current assessment of the historical receipt and hardened runner. It records
  12 passing unit contracts, normalizes the historical result to Q2
  `PASS_WITH_RESERVATIONS` and Q3 `PARTIAL`, and records the fresh native
  renewal as `BLOCKED` only because a new authenticated model session and
  external model egress were not authorized. The runner accepts the verified
  offline npm cache for reviewed installer acquisition. That renewal started no
  model session and attempted no cloud mutation; formal Q2/Q3 and release
  qualification remain `BLOCKED`.
- [`2026-09-18-skill-revision-assessment.json`](2026-09-18-skill-revision-assessment.json):
  targeted assessment of three content-forward cases against current skill tree
  `b984f25dc1462c14dc3153eb307f5953d08821970afdd036022eb3d6cbbf653e`.
  All three ran in Codex subagent sessions and passed without file writes,
  network calls, OCI commands, or cloud mutations. This is not host-native
  evidence; formal native and release gates remain `BLOCKED`.
- [`2026-09-18-behavioral-case-index.json`](2026-09-18-behavioral-case-index.json):
  historical 24-case prompt hashes, contracts, evaluators, and evidence paths,
  bound to former skill tree
  `746cc9a3462ce96c067eedd91e848a905f04ed402b8f579836ce126c5b4d703f`.
  It records zero native-complete/transcript/tool-trace-bound cases, so the
  formal native gate remains blocked.

The repository-source secret scan passes locally, but it does not create a
result file in this directory. Likewise, no checkout-bound result is claimed
for `verify_oracle_skills_lock.py`: the offline verifier has not been run
against a real `oracle/skills` checkout in this workspace.

These are local evaluation records committed with the public source preview.
Their presence is not a claim of a successful remote CI run, native
qualification, tagged release, marketplace publication, registry coordinate,
or package coordinate.
