# Public-preview and release procedure

This repository is an independent personal project published by Daniel
Gandolfi under the Universal Permissive License 1.0 (`UPL-1.0`). Daniel works at
Oracle, but publishes this toolkit in his personal capacity. It is not an
Oracle product and is not sponsored, endorsed, maintained, or supported by
Oracle. The project has no Oracle Support coverage, warranty, service-level
agreement, or production-readiness commitment.

The UPL authorizes public use, modification, and redistribution under its
terms. It does not qualify a host, architecture, package coordinate, or OCI
deployment, and it does not authorize Oracle logos or imply Oracle sponsorship.
Technical claims remain bounded by the evidence in this procedure.

The source is published from `main` at
[`danielgandolfi1984/oracle_founder_pack`](https://github.com/danielgandolfi1984/oracle_founder_pack).
The published [`v0.1.1` GitHub prerelease](https://github.com/danielgandolfi1984/oracle_founder_pack/releases/tag/v0.1.1)
is fixed at commit `8765266e3ef77110b30827d5c89da7cf1b15ee08`. That revision
passed [CI run 35385557348](https://github.com/danielgandolfi1984/oracle_founder_pack/actions/runs/35385557348),
and its public tag passed project-scoped Codex install/list/remove/reinstall
and final cleanup with the released skill hash. All six release assets were
downloaded again and verified, including both archives against their manifests
and checksums. The [publication receipt](../tests/results/2026-09-18-v0.1.1-publication.json)
and [tag lifecycle receipt](../tests/results/2026-09-18-v0.1.1-public-tag-lifecycle.json)
retain the evidence. This is an immutable
public-preview coordinate; it does not claim marketplace, registry, stable, or
cross-host qualification.

The prepublication `0.1.1` assessments remain candidate-at-capture records.
The earlier `v0.1.0` tag remains at `6cf08bf30febc434cefed228f53c43a1f8802ec2`;
neither its tag nor its assets were replaced. Later source changes require
their own CI and, for packaged changes, a new release coordinate.

The
[license and publisher decision](decisions/0003-public-license-and-publisher.md)
records the independent-project classification, Daniel Gandolfi as publisher,
and the distinction between an installable personal public preview and an
Oracle-supported product.

## Candidate types

| Candidate | Contents | Intended use |
|---|---|---|
| Skill-only | `skills/oci-founder`, preview README, license, security/support guidance, notices | Public planning, translation, and routing preview |
| Full toolkit | Portable skill, three manifests, Container API preview, upstream review lock, license, security/support guidance, notices | Personal public preview with the sandbox-only executable path present |

Neither archive contains presentations. The canonical Oracle-template deck is
maintained locally at `artifacts/OCI-Founder-Toolkit-Oracle-Template-v11-User-Guide.pptx`.
It is marked `Confidential: Internal`, remains Git-ignored, is outside the
public UPL distribution, and must not be published. Any future distribution of
that deck requires a separate Oracle content, confidentiality, and brand
decision.

## Local release gate

Run from a reviewed checkout:

```bash
python3 scripts/validate_agent_plugin_schema.py
python3 scripts/scan_release_sources.py
python3 scripts/validate.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 -m unittest discover -s blueprints/container-api/tests -v
python3 scripts/build_release.py check
python3 scripts/qualify_skill_install.py --allow-download
terraform fmt -check -recursive blueprints/container-api/terraform
terraform -chdir=blueprints/container-api/terraform/bootstrap init \
  -backend=false -input=false -lockfile=readonly
terraform -chdir=blueprints/container-api/terraform/bootstrap validate -no-color
terraform -chdir=blueprints/container-api/terraform/runtime init \
  -backend=false -input=false -lockfile=readonly
terraform -chdir=blueprints/container-api/terraform/runtime validate -no-color
```

The installer lifecycle downloads only the reviewed lock contents, runs npm
with lifecycle scripts disabled, verifies the package manifest and executable
hashes before use, and operates in disposable project repositories. It does not
qualify a global user profile or native host discovery.

The `0.1.1` source and local package lifecycle evidence was produced by copying a
verified npm cache into disposable state and running `npm ci --offline`.
Dependency-lock, package-integrity, manifest, and executable-hash checks
remained active. Source plus both preview packages passed project-scoped
install/list/remove/reinstall lifecycle across all three supported layouts.
The local secret scan covers both release allowlists and the repository source
tree.

To verify an already-present reviewed Oracle Skills checkout without network or
mutation, run:

```bash
python3 scripts/verify_oracle_skills_lock.py \
  --checkout /absolute/path/to/oracle-skills-reviewed
```

This verifies the locked commit, reviewed trees, clean worktree, and
`LICENSE.txt`. The real locked checkout
[passed verification](../tests/results/2026-09-18-oracle-skills-verified.json)
before and after its OCI domain passed an isolated Codex
[project installation lifecycle](../tests/results/2026-09-18-oracle-skills-verified-codex-lifecycle.json).
Native upstream discovery, sibling Database navigation, and full-profile
isolation remain separate gates. Reverify the checkout used for each release.

Native Codex probing is a separately authorized evidence step, not a passive
local check. The runner can acquire the reviewed installer through an explicit
download or a supplied verified offline npm cache, then starts one authenticated
model session. Use a fresh temporary receipt path and do not add `--overwrite`
unless replacing that exact local artifact is intentional. The verified-cache
path is:

```bash
python3 scripts/probe_codex_native.py \
  --offline-npm-cache /absolute/path/to/reviewed-npm-cache \
  --allow-model-session \
  --output /private/tmp/oci-founder-codex-native-probe.json
```

The hardened runner's current unit contracts can be checked without those
effects:

```bash
python3 -B -m unittest tests.test_probe_codex_native -v
```

The runner uses a disposable Git fixture, project-scoped copied skill,
environment allowlist, `codex exec --ephemeral`, a read-only sandbox, structured
output, event capture, and deny shims for cloud/deployment CLIs. The existing
receipt is historical and bound to former skill tree
`746cc9a3462ce96c067eedd91e848a905f04ed402b8f579836ce126c5b4d703f`:
it recorded probe Q2/Q3 as `PASS`, while the prepublication assessment normalizes Q2
to `PASS_WITH_RESERVATIONS` and Q3 to `PARTIAL`.

The earlier prepublication renewal stopped before model execution because
authorization had not yet been given. That restriction was superseded for the
post-release checks. The first new run exposed parser and schema defects; its
failed receipt was retained. After regression tests and harness fixes, the
[fresh native probe](../tests/results/2026-09-18-codex-native-postrelease.json)
passed with reservations against the unchanged release skill: valid structured
output, all four machine assertions passed, exact installed-skill binding,
clean removal, and no observed project edits, unreviewed commands, OCI commands,
or cloud mutations. Its probe Q2 is `PASS` and Q3 is `PARTIAL`.

The `0.1.0` [post-release assessment](../tests/results/2026-09-18-codex-native-postrelease-assessment.json)
includes independent semantic review and the remaining limits: one explicit
prompt, shared authentication profile, no upstream dependencies in that native
session, and no 24-case replay. The response was safe but longer than needed;
conciseness and progressive disclosure prompted the separate `0.1.1`
[prepublication assessment](../tests/results/2026-09-18-v0.1.1-assessment.json).
The current runner binds version assertions to source `metadata.version` and
records the expected version, while the prompt, output schema, and fixture
remain the same for comparison. The
[`0.1.1` native receipt](../tests/results/2026-09-18-v0.1.1-codex-native.json)
passed with reservations: 185 words versus 1,489 for the same prompt, two
reference reads instead of four, all recorded effects false, and clean removal.
This single comparison does not qualify the full suite. Formal Q2/Q3 remain
`BLOCKED`. Historical receipt:
[`tests/results/2026-09-18-codex-native-runner-probe.json`](../tests/results/2026-09-18-codex-native-runner-probe.json).
Prepublication assessment:
[`tests/results/2026-09-18-codex-native-runner-assessment.json`](../tests/results/2026-09-18-codex-native-runner-assessment.json).
The separate
[`targeted 0.1.0 assessment`](../tests/results/2026-09-18-skill-revision-assessment.json)
passes three content-forward cases at published skill tree
`c9ca7081b818f85a248836a53d12b94b6c995da9825696346a1075bf42c2dd37`.
It is not a native replay and does not close either formal gate.

For the installed Skill Creator and Plugin Creator development validators,
prepare an isolated dependency directory with the reviewed wheel hashes:

```bash
python3 -m pip install --require-hashes --only-binary=:all: --no-deps \
  --target /absolute/path/to/validator-deps \
  -r requirements-validation.txt

python3 scripts/qualify_hosts.py --run-validators \
  --validator-pythonpath /absolute/path/to/validator-deps
```

The dependency lock currently supports the reviewed macOS arm64/Python 3.9 and
Linux x86_64/Python 3.12 validator environments. Add and review a wheel hash
before claiming another platform.

## Build and verify archives

```bash
python3 scripts/build_release.py build --output-dir dist
python3 scripts/build_release.py verify --output-dir dist
```

The build refuses to overwrite an existing output unless `--overwrite` is
explicit. The `check` command builds twice in separate temporary directories,
verifies both sets, and requires byte-for-byte equality. Each archive has a
`.sha256` file and a `.manifest.json` inventory containing every member's path,
source path, mode, size, and SHA-256 digest.

The current public-preview package names are
`oci-founder-skill-0.1.1-preview.tar.gz` and
`oci-founder-toolkit-0.1.1-preview.tar.gz`. Local qualification precedes
published-asset verification.
The full toolkit extracts into the
stable `oci-founder-toolkit/` root that matches the plugin manifest name.
Extract it into a clean parent directory so files from an older candidate
cannot remain in that stable root.

The current skill-only archive SHA-256 is
`6167f1ca7da9a06204e8e0d028622c490b727581532c15ec1d5d78629b2aa8ff`.
The current full-toolkit archive SHA-256 is
`7296477c39da42f830edd4e5dee6713288cdef695da0957145f79057cd17218b`.
The renewed
[skill-only summary](../tests/results/2026-09-18-v0.1.1-skill-package-install-lifecycle.json),
[skill-only raw receipt](../tests/results/2026-09-18-v0.1.1-skill-package-install-lifecycle.raw.json),
[full-toolkit summary](../tests/results/2026-09-18-v0.1.1-full-package-install-lifecycle.json)
and [full-toolkit raw receipt](../tests/results/2026-09-18-v0.1.1-full-package-install-lifecycle.raw.json)
bind these `-preview` archives, their manifests and inventories, and current
skill fingerprint
`dba58d1984513e44aa77a5729a20b16e23186dac00e0de17ef1db01ddd0bda49`.

To qualify an extracted full-toolkit archive rather than the development tree:

```bash
python3 scripts/qualify_skill_install.py --allow-download \
  --source /absolute/path/to/extracted/oci-founder-toolkit
```

Do not publish an ad hoc local `dist/` directory. Publish only artifacts built
from the immutable preview revision, verified against their manifests and
checksums, and attached to the matching tag or release coordinate.

The current read-only host-preflight receipt passes source validation through
the explicit cycle-breaking mode and passes the available development
validators at the current skill fingerprint. It records
`release_qualified: false`. Archive lifecycle and preflight evidence do not
replace native-host or OCI field gates. The public-coordinate check for
`v0.1.1` passed separately as recorded above.

## Public-preview and qualification gates

The UPL makes the source public and reusable; the word `public` is not itself a
technical qualification claim. Before publishing an immutable public-preview
package, items 1–2, the pre-tag portion of item 5, and item 6a below need
durable evidence. The remote-coordinate portion of item 5 is necessarily run
after the tag exists and before the GitHub prerelease is completed. Items 3–4,
6b, 7, and 8 govern narrower native-host, hardened-distribution, OCI field, and
usability claims that are not made by this preview. None of these gates creates
Oracle Support or an SLA.

1. Canonical UPL-1.0 license, Daniel Gandolfi publisher identity, independent
   project disclaimer, community support boundary, confidential security
   intake, and lifecycle/deprecation policy.
2. Reviewed toolkit content in the dedicated Git repository, immutable
   commit/tag, CI run bound to that revision, and archive checksums bound to the
   same revision.
3. Native Q0–Q4 qualification on current Codex, Cursor Agent, and Claude Code,
   including Cursor same-name deduplication and a fully disposable profile.
4. Twenty-four of twenty-four behavioral fixtures in fresh sessions with
   redacted transcript/tool-trace hashes, machine assertions, deny shims, and
   independent semantic verdicts.
5. Project-scoped installation, removal, and reinstall from the exact local
   source and deterministic archives before tagging, followed by one
   project-scoped install/remove check from the immutable public tag before the
   first prerelease is finalized. Marketplace qualification is separate.
6. Distribution assurance:
   - **6a — public-preview minimum:** high-confidence source secret scan;
     repository/schema/unit/IaC checks applicable to the shipped source;
     deterministic package inventories, manifests, SHA-256 sidecars, and
     archive lifecycle evidence; no unresolved critical/high finding in those
     executed checks.
   - **6b — hardened/stable promotion:** dependency and built-container-image
     vulnerability scans where those artifacts are distributed, plus a
     reviewed SBOM, provenance, and signing policy. The preview distributes
     source and archives, not a built runtime image, and does not claim this
     promotion gate.
7. For executable paths, a separately authorized OCI sandbox run covering
   plan, exact-target approval, apply, verification, second-plan idempotency,
   rollback, exact-ID teardown, and retained-resource reconciliation.
8. Founder usability evidence for the completion and time-to-endpoint targets.

If a gate required for a specific claim is absent, report that claim as
`BLOCKED`; do not substitute a local static check for host-native,
public-coordinate, or tenancy evidence. A blocked qualification claim does not
revoke the UPL or turn the personal source project into an Oracle product.
Formal Q2/Q3, native Cursor and Claude Code replay, global-profile lifecycle,
and live OCI field validation remain `BLOCKED` or open as described above.
