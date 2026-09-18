# Changelog

All notable changes to the OCI Founder Toolkit evaluation are recorded here.
The project publishes a public source preview but has not published a tagged or
supported public release.

## Unreleased — `0.1.0` evaluation

### Added

- Portable `oci-founder` skill for backend-first orientation, cross-cloud
  translation, golden-path selection, guardrails, and routing into reviewed
  Oracle service skills.
- Agent Plugins v1, Codex, and Claude Code manifests.
- AWS, Google Cloud, and Azure founder mental models plus a 24-case behavioral
  matrix whose recorded results remain historical and bound to the former skill
  fingerprint.
- Container API `0.2.0-preview.3`, kept separately versioned and sandbox-only.
- Locked `skills@1.7.0` project-scoped install/list/remove/reinstall lifecycle
  across Codex, Cursor, and Claude Code layouts for the checkout, skill-only
  archive, and full-toolkit archive. The archive runs use a copied verified npm
  cache with `npm ci --offline`; exact raw receipts are committed and bound by
  their summaries.
- Historical native Codex `0.153.4` discovery and one explicit, read-only
  behavior-probe receipt. Its recorded Q2/Q3 `PASS` results are normalized by
  the current assessment to Q2 `PASS_WITH_RESERVATIONS` and Q3 `PARTIAL`.
- Targeted current-skill assessment covering three content-forward cases at
  skill tree
  `b984f25dc1462c14dc3153eb307f5953d08821970afdd036022eb3d6cbbf653e`;
  the assessment remains non-native and does not close Q2 or Q3.
- Hardened native Codex runner with 12 passing unit contracts, verified offline
  npm-cache acquisition, and a dated renewal assessment.
- Canonical Oracle-template founder guide presentation, v11, kept local and
  Git-ignored because it is marked `Confidential: Internal`, and excluded from
  the evaluation archives.
- Vendored Agent Plugins `1.0.0` schema snapshot with provenance and a
  dependency-free validator.
- Deterministic, allowlisted skill-only and full-toolkit evaluation archives,
  each with a SHA-256 checksum and per-file content manifest. Current archive
  SHA-256 values are `1e41859b5ac86522356aa922f177189c3f95a1deaba8dae77d6a95e1cd64ab23`
  for skill-only and
  `aa332c7555ad88e17f86f99dbd1e33e0f211f48e6e40b980eedb8992c1333790`
  for full-toolkit. The versioned full archive extracts under the stable
  `oci-founder-toolkit/` root, and both package lifecycle receipts were renewed
  for these artifacts.
- High-confidence secret scan over the exact package allowlists and repository
  source tree.
- Offline, read-only `oracle/skills` lock verifier for the locked commit,
  reviewed trees, clean worktree, and `LICENSE.txt`.
- Public source-evaluation repository,
  [`danielgandolfi1984/oracle_founder_pack`](https://github.com/danielgandolfi1984/oracle_founder_pack),
  published on `main` under the restrictive evaluation license, without a tag,
  GitHub release, marketplace entry, registry coordinate, or package coordinate.
- Pinned CI action revisions and CI gates for schema validation, package
  determinism, installation lifecycle, unit contracts, and Terraform checks.

### Safety

- OCI writes, IAM changes, Terraform apply, and destructive operations remain
  behind exact preview, target, lineage, and explicit-approval gates.
- Host preflight subprocesses now receive an environment allowlist instead of
  the caller's full environment.
- Host-preflight evidence uses atomic writes, refuses symlink targets/parents,
  and requires explicit overwrite.
- Host-preflight renewal breaks its validation cycle explicitly; the fresh
  read-only receipt passes at the current skill fingerprint while retaining
  `release_qualified: false`.
- Package builds exclude editor output, presentations, credentials, local
  environment files, Terraform state/plans, generated receipts, caches, and
  symlinks.

### Known release blockers

- No approved open-source/public-use license, publisher identity,
  support/security contact, or completed Oracle repository-ownership, naming,
  and trademark decision. The source preview remains under restrictive
  evaluation terms.
- Cursor Agent and Claude Code are unavailable on the current host; Cursor
  duplicate discovery is not qualified.
- A fresh hardened native Codex rerun is `BLOCKED` only because a new
  authenticated model session and external model egress were not authorized;
  reviewed installer acquisition can use the verified offline npm cache. No
  model session or cloud mutation occurred in that renewal.
- Formal Codex Q2 and Q3 remain `BLOCKED`; they still require a fully
  disposable host profile, reviewed upstream dependencies, native replay of
  the historical behavioral matrix against the current skill, deny shims, and
  independent semantic grading.
- The offline `oracle/skills` verifier has not been run against a real checkout
  in this workspace.
- No authenticated OCI sandbox plan/apply/idempotency/rollback/teardown run has
  occurred.
- A supported public release remains `BLOCKED`; the public source preview has no
  immutable tag, GitHub release, marketplace entry, registry coordinate, or
  package coordinate.
