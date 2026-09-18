# Evaluation and release procedure

This procedure can produce a locally verified evaluation candidate. It cannot
authorize a tagged or supported public release. The public source preview
remains under the restrictive evaluation `LICENSE`; packages, marketplace
publication, and broader use or redistribution rights remain blocked until
Oracle legal, OSS, naming, trademark, security, support, and repository
ownership gates are resolved.

A source evaluation preview is published from `main` at
[`danielgandolfi1984/oracle_founder_pack`](https://github.com/danielgandolfi1984/oracle_founder_pack),
but no immutable tag, GitHub release, marketplace entry, registry coordinate,
or package coordinate exists. Public source access is not an open-source
license or a supported-release approval and does not close legal, OSS,
publisher, support, or Oracle repository-ownership gates.

The proposed
[public-license and publisher decision](decisions/0003-public-license-and-publisher.md)
defines the approval packet, compares UPL-1.0 with Apache-2.0, and separates
public source, installable public preview, and Oracle-supported release. It is
decision preparation only; it does not change the current license.

## Candidate types

| Candidate | Contents | Intended use |
|---|---|---|
| Skill-only | `skills/oci-founder`, evaluation README, license, notices | Planning, translation, and routing evaluation |
| Full toolkit | Portable skill, three manifests, Container API preview, upstream review lock, license, notices | Reviewed sandbox evaluation with the executable preview present |

Neither archive contains presentations. The canonical Oracle-template deck is
maintained locally at `artifacts/OCI-Founder-Toolkit-Oracle-Template-v11-User-Guide.pptx`.
It is marked `Confidential: Internal`, remains Git-ignored, and requires an
explicit redistribution/brand decision before public distribution.

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

The current lifecycle evidence was renewed by copying a verified npm cache into
disposable state and running `npm ci --offline`. Dependency-lock, package
integrity, manifest, and executable-hash checks remained active. The local
secret scan covers both release allowlists and the repository source tree, and
passes.

To verify an already-present reviewed Oracle Skills checkout without network or
mutation, run:

```bash
python3 scripts/verify_oracle_skills_lock.py \
  --checkout /absolute/path/to/oracle-skills-reviewed
```

This verifies the locked commit, reviewed trees, clean worktree, and
`LICENSE.txt`. It has not been run against a real checkout in this workspace;
do not treat the verifier's presence as completed upstream qualification.

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
effects; all 12 pass in the dated assessment:

```bash
python3 -B -m unittest tests.test_probe_codex_native -v
```

The runner uses a disposable Git fixture, project-scoped copied skill,
environment allowlist, `codex exec --ephemeral`, a read-only sandbox, structured
output, event capture, and deny shims for cloud/deployment CLIs. The existing
receipt is historical and bound to former skill tree
`746cc9a3462ce96c067eedd91e848a905f04ed402b8f579836ce126c5b4d703f`:
it recorded probe Q2/Q3 as `PASS`, while the current assessment normalizes Q2
to `PASS_WITH_RESERVATIONS` and Q3 to `PARTIAL`.

A fresh hardened rerun is `BLOCKED` only because a new authenticated model
session and external model egress were not authorized; verified offline-cache
installer acquisition is available. It started no model session and attempted
no cloud mutation. Formal Q2 and Q3 remain `BLOCKED`; the historical result
does not replace the fully disposable profile, cross-host, or native behavioral
gates. Historical receipt:
[`tests/results/2026-09-18-codex-native-runner-probe.json`](../tests/results/2026-09-18-codex-native-runner-probe.json).
Current assessment:
[`tests/results/2026-09-18-codex-native-runner-assessment.json`](../tests/results/2026-09-18-codex-native-runner-assessment.json).
The separate
[`targeted current-skill assessment`](../tests/results/2026-09-18-skill-revision-assessment.json)
passes three content-forward cases at skill tree
`b984f25dc1462c14dc3153eb307f5953d08821970afdd036022eb3d6cbbf653e`;
it is not a native replay and does not close either formal gate.

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

The full-toolkit artifact remains versioned as
`oci-founder-toolkit-0.1.0-evaluation.tar.gz`, but extracts into the stable
`oci-founder-toolkit/` root that matches the plugin manifest name. Extract it
into a clean parent directory so files from an older candidate cannot remain in
that stable root.

The current skill-only archive SHA-256 is
`1e41859b5ac86522356aa922f177189c3f95a1deaba8dae77d6a95e1cd64ab23`.
The current full-toolkit archive SHA-256 is
`aa332c7555ad88e17f86f99dbd1e33e0f211f48e6e40b980eedb8992c1333790`.
The renewed
[skill-only summary](../tests/results/2026-09-18-skill-package-install-lifecycle.json),
[skill-only raw receipt](../tests/results/2026-09-18-skill-package-install-lifecycle.raw.json),
[full-toolkit summary](../tests/results/2026-09-18-full-package-install-lifecycle.json)
and [full-toolkit raw receipt](../tests/results/2026-09-18-full-package-install-lifecycle.raw.json)
are current and bind these archives, their manifests and inventories, and the
installed skill tree to the current source fingerprint.

To qualify an extracted full-toolkit archive rather than the development tree:

```bash
python3 scripts/qualify_skill_install.py --allow-download \
  --source /absolute/path/to/extracted/oci-founder-toolkit
```

Do not publish `dist/`. These files are evaluation artifacts under the current
license.

The renewed read-only host-preflight receipt passes source validation through
the explicit cycle-breaking mode at the current skill fingerprint and still
records `release_qualified: false`. Archive lifecycle and preflight renewal do
not replace native host, public-coordinate, license, or OCI field gates.

## Public-release gates

Every item below must have durable evidence before the word "public" or
"generally available" is used:

1. Approved license and SPDX identifier, Oracle publisher identity, product
   name/trademark review, approval and ownership of the provisional repository,
   support contact, security contact, and lifecycle/deprecation policy.
2. Approved toolkit content in the dedicated Git repository, immutable
   commit/tag, CI run bound to that revision, and archive checksums bound to the
   same revision.
3. Native Q0–Q4 qualification on current Codex, Cursor Agent, and Claude Code,
   including Cursor same-name deduplication and a fully disposable profile.
4. Twenty-four of twenty-four behavioral fixtures in fresh sessions with
   redacted transcript/tool-trace hashes, machine assertions, deny shims, and
   independent semantic verdicts.
5. Public-coordinate installation, removal, and reinstall from the immutable
   tag or marketplace entry.
6. Security, dependency, IaC, container, and package scans with no unresolved
   critical/high finding; reviewed standard SBOM/provenance and signing policy.
7. For executable paths, a separately authorized OCI sandbox run covering
   plan, exact-target approval, apply, verification, second-plan idempotency,
   rollback, exact-ID teardown, and retained-resource reconciliation.
8. Founder usability evidence for the completion and time-to-endpoint targets.

If any gate is absent, report it as `BLOCKED`; do not substitute a local static
check for host-native, public-install, or tenancy evidence.
