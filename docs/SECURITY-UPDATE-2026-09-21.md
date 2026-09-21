# Security update — 21 September 2026

[Português](i18n/pt-BR/SECURITY-UPDATE-2026-09-21.md)

Use Container API **`0.2.0-preview.4`** or later for the corrected offline
security gates. This remains a sandbox-only personal preview, not a live OCI
security assessment or production certification.

## What changes for a founder or developer?

- **Planning skills:** `oci-founder`, `oci-founder-start` and
  `oci-founder-migrate` are unchanged. Installing a planning skill does not run
  the affected helper or install the test fixture's dependencies.
- **Container API blueprint:** update the complete reviewed checkout/bundle,
  including its helper and version, before generating or reviewing new plans,
  receipts or teardown audits. Do not use old gate results as security proof.
- **Old packages:** the full-toolkit archives attached to `v0.1.0` and `v0.1.1`
  retain their original bytes and vulnerable gate implementations. Do not use
  those helpers to validate infrastructure. The replacement full bundle has
  the distinct coordinate `container-api-v0.2.0-preview.4` and the filename
  `oci-founder-toolkit-0.1.1-container-api-0.2.0-preview.4.tar.gz`. Its unchanged
  planning-skill/plugin version is `0.1.1`, not a new skill release.
- **Existing OCI resources:** updating local files does not repair, change or
  delete cloud resources. Any account inspection needs an explicitly scoped
  user request; actual remediation needs a separately reviewed plan and approval.

## Corrected issues

| Issue | Impact and prerequisite | Correction |
|---|---|---|
| SEC-01, medium | Altered plan/state could contain extra routes that were skipped by the comparator, making an unexpected HTTP surface appear compliant | Require the exact route count, unique expected paths, GET-only methods and complete backend contract; reject invalid/unknown entries |
| SEC-02, medium | Altered plan/state could contain Add=ALL alongside Drop=ALL, falsely appearing to drop container capabilities | Reject non-empty or unknown add-capabilities while accepting valid empty provider values |
| DEP-01, dependency advisories | The non-deployed FastAPI assessment fixture resolved Starlette 0.47.3, which matched six known advisories; exploitation through the existing JSON handlers was not demonstrated | Update compatible framework/dependency versions, pin the closure with reviewed binary hashes and repeat the app/dependency checks |

The two gates were reproduced using synthetic plans and state, not an OCI
deployment. No anonymous route creation, container escape or data exposure was
demonstrated. The Oracle behavior underlying these checks is documented for
[gateway stock responses](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayaddingstockresponses.htm)
and [container capabilities](https://docs.oracle.com/en-us/iaas/Content/container-instances/creating-a-container-instance.htm).

## Continuous checks and evidence boundaries

The first CodeQL run also flagged HTTP response splitting and a URL substring
check. Review found that request IDs already used a strict ASCII allowlist and
the substring check rejected unfilled examples, rather than authorizing network
destinations; no exploit was reproduced. The final bundle adds explicit CR/LF
removal at the response-header boundary and parses placeholder hostnames/email
domains. Tests preserve actual HTTPS/repository restrictions and accepted IDs.
These are defensive clarifications, not two additional confirmed exploits.

The security workflow audits active dependency manifests through OSV and runs
CodeQL for Python. Dependabot proposes updates; changes are not automatically
merged. Exact versions, compatibility and hashes still require review. Query
failures must not be reported as a clean dependency audit.

Regression tests cover both plan and applied-state rejection, valid provider
defaults and the original bypasses. The repository's source/privacy checks and
unit tests remain required. No scan proves absence of every vulnerability.

The fixture now pins FastAPI `0.141.1` and Starlette `1.6.0` in a 15-package
closure. Hash-verified macOS arm64 installation, Linux x86_64/arm64 wheel
resolution/download and five in-process ASGI checks passed; no Linux container
was executed. The [final full-bundle assessment](../tests/results/2026-09-21-security-final-full-package-assessment.json)
binds the archive hash and fresh install/remove/reinstall receipts for Codex,
Cursor and Claude Code installation layouts, not native model behavior.
The [initial candidate assessment](../tests/results/2026-09-21-security-full-package-assessment.json)
is retained as historical evidence, before the CodeQL-driven hardening; its
archive hash is not the final published bundle's hash.

The [post-fix OSV receipt](../tests/results/2026-09-21-security-dependencies.json)
records 28 successfully checked package/version coordinates and no known
advisories returned at capture time. This does not cover OS/image layers,
Terraform binaries or dependencies not declared in the active manifests.

Historical release checksums, installation receipts and native-agent outputs
remain unchanged. The [fixture lineage record](../tests/results/2026-09-21-fixture-lineage.json)
preserves the old fixture hash rather than rewriting model-run evidence after
updating dependencies. No new native-agent comparison or live cloud test is
implied by this correction. Current CI results are available in
[Validate toolkit](https://github.com/danielgandolfi1984/oracle_founder_pack/actions/workflows/validate.yml)
and [Security](https://github.com/danielgandolfi1984/oracle_founder_pack/actions/workflows/security.yml).

Use [private vulnerability reporting](../SECURITY.md) for new issues. Never
include credentials, private keys, customer data or raw Terraform state in a
public report. Tokens previously exposed outside the repository must be
revoked separately; a clean repository scan does not revoke them.
