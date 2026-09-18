# OCI Founder Toolkit

> Plan your backend's path to OCI with the coding agent you already use.

OCI Founder Toolkit is an agent-native, backend-first path for technical founders and developers who know AWS, Google Cloud, or Azure but are new to Oracle Cloud Infrastructure (OCI).

The toolkit is not another OCI service encyclopedia. It composes official Oracle knowledge into opinionated founder journeys: understand an existing repository, translate familiar cloud concepts, choose a small architecture, establish guardrails, ship, verify, operate, and eventually tear down or graduate.

## Status

This repository publishes a **source evaluation preview**, not a supported
public release. The package and portable skill remain at `0.1.0`; they are not
tagged or promoted until the release gates are met. The repository also contains a separately
versioned [`0.2.0-preview.3` Container API blueprint](blueprints/container-api/README.md).
That preview is executable but sandbox-only, has not been applied in an OCI
tenancy, and is not a supported marketplace package. See [`LICENSE`](LICENSE)
and the [validation record](docs/VALIDATION.md) before using or redistributing it.

The public source preview is available on `main` at
[`danielgandolfi1984/oracle_founder_pack`](https://github.com/danielgandolfi1984/oracle_founder_pack).
It is technically cloneable for an authorized evaluation, but there is no
immutable tag, GitHub release, marketplace entry, registry coordinate, or
package coordinate. Public source access does not grant open-source or broader
redistribution rights under the current restrictive evaluation `LICENSE`, and
does not close legal, OSS, publisher-identity, naming/trademark, support, or
Oracle repository-ownership gates.
Both archives passed project-scoped install/list/remove/reinstall lifecycle
checks in isolated Codex, Cursor, and Claude Code layouts. The lifecycle was
rerun from a copied, verified npm cache with `npm ci --offline`, while retaining
the dependency-lock and package-integrity checks; the summaries bind committed
exact raw receipts by SHA-256. The current archive identities are:

- skill-only: `876fe40dbac703b092110f106f6797fa7eaa753c6bb9b711e61e67f61c2fd315`;
- full toolkit: `62501591cdc53b2e366dd7fbe39c7c87a47a838ff034ff7ad734040d1f96eaa8`,
  with the stable internal root `oci-founder-toolkit/`.

Both renewed package receipts match the current source and installed skill tree
fingerprint
`b984f25dc1462c14dc3153eb307f5953d08821970afdd036022eb3d6cbbf653e`.

The historical Codex runner receipt, bound to former skill tree
`746cc9a3462ce96c067eedd91e848a905f04ed402b8f579836ce126c5b4d703f`,
recorded probe Q2 and Q3 as `PASS`; the current assessment normalizes that
evidence to Q2 `PASS_WITH_RESERVATIONS` and Q3 `PARTIAL`. A separate targeted
assessment passed three content-forward cases against the current skill
fingerprint; it is not host-native evidence. The
hardened runner's 12 unit contracts pass and it can reacquire the reviewed
installer from a verified offline npm cache. A fresh native renewal is blocked
only because a new authenticated model session and its external egress were not
authorized. It started no model session and attempted no cloud mutation. Formal
Q2 and Q3 remain `BLOCKED`, Cursor Agent and Claude Code are unavailable on the
current host, and a supported public release remains `BLOCKED`.

The canonical Oracle-template presentation is maintained locally as
`artifacts/OCI-Founder-Toolkit-Oracle-Template-v11-User-Guide.pptx`. Its
`Confidential: Internal` footer makes it intentionally Git-ignored and outside
the evaluation archives until a separate brand and redistribution decision.

Version `0.1.0` is the product and portability foundation. It includes:

- one portable `oci-founder` planning and routing skill;
- compatibility manifests for Agent Plugins v1, Codex, and Claude Code;
- mental-model translations for AWS, Google Cloud, and Azure developers;
- two proposed MVP golden paths: Container API and Function API;
- cost, identity, secret, Terraform, and mutation guardrails;
- an immutable source-review record for the upstream `oracle/skills` snapshot;
- validation scripts and cross-agent smoke prompts.
- an early Container API field preview with two Terraform authority layers,
  strict plan/receipt/teardown helpers, and a dependency-free sample API.

The Container API preview is present for review and sandbox field testing; a read-only OCI context plugin remains future work. See [the roadmap](docs/ROADMAP.md).

## Why this exists

Cloud-experienced founders usually do not lack backend skills. They lack an OCI mental model at the exact moment they need to make architecture, IAM, networking, and cost decisions. General coding agents often reinforce the AWS/GCP/Azure concepts that dominate public examples.

OCI Founder Toolkit closes that gap with three layers:

1. **Founder journey** — a short path from repository to verified endpoint.
2. **Translation** — explicit mappings and important non-equivalences between clouds.
3. **Oracle source layer** — official documentation and existing [`oracle/skills`](https://github.com/oracle/skills), rather than duplicated service instructions.

## Relationship with `oracle/skills`

[`oracle/skills`](https://github.com/oracle/skills) remains the upstream source for reusable Oracle service expertise. Its OCI domain currently covers Functions, OKE, IoT Platform, and Enterprise AI; its Database domain covers Oracle Database development and operations.

This toolkit owns the founder experience around those skills: orientation, sequencing, cross-cloud translation, golden paths, product-level guardrails, and blueprints.

The lock file is a source-review record; it does not constrain a command that
installs directly from the moving upstream default branch. Upstream reuse is a
verification-first flow: the reviewed full toolkit checkout must provide both
`upstream/oracle-skills.lock.json` and
`scripts/verify_oracle_skills_lock.py`. If either is unavailable, fail closed
at planning level and do not install or operationally route to the upstream
skill.

When the user has requested the environment change, check out the recorded
commit and run the verifier before any install:

```bash
git clone https://github.com/oracle/skills.git /absolute/path/to/oracle-skills-reviewed
git -C /absolute/path/to/oracle-skills-reviewed checkout --detach b0afa3bfd7c7e3547458d7fe52649ab1b59706b7

python3 /absolute/path/to/oci-founder-toolkit/scripts/verify_oracle_skills_lock.py \
  --lock /absolute/path/to/oci-founder-toolkit/upstream/oracle-skills.lock.json \
  --checkout /absolute/path/to/oracle-skills-reviewed
```

Stop unless the verifier returns a passing receipt. Then change to the backend
that will use the skill and run only the domain command required by the task:

```bash
cd /absolute/path/to/target-backend

# OCI domain for Codex
npx --yes skills@1.7.0 add /absolute/path/to/oracle-skills-reviewed/oci \
  -a codex --copy -y

# Oracle Database domain for Codex; run separately and only when needed
npx --yes skills@1.7.0 add /absolute/path/to/oracle-skills-reviewed/db \
  -a codex --copy -y

npx --yes skills@1.7.0 list --json
```

These are project-scoped commands: execute them from the target backend and do
not add `-g`. The example targets Codex. Replace `codex` with exactly one of
`cursor` or `claude-code` for the agent actually in use; every add command must
contain exactly one `-a` flag. Do not run both domain commands unless the task
requires both domains.

This pins the upstream source commit and the top-level installer package, but
not the installer's full transitive dependency graph. Do not describe this
convenience flow as a bit-for-bit reproducible installer replay.

Installing directly from the remote `oracle/skills/oci` or `oracle/skills/db`
source instead resolves current upstream content and must not be described as
matching the reviewed lock. The reviewed commit and dependency scope are
recorded in
[`upstream/oracle-skills.lock.json`](upstream/oracle-skills.lock.json). The
toolkit does not silently copy or modify upstream content.

The verifier checks the locked commit, reviewed trees, clean worktree, and
`LICENSE.txt` without network access or mutation. It has not been run against a
real `oracle/skills` checkout in this workspace, so no successful checkout
receipt is claimed.

## Install this evaluation draft

There is no public package coordinate or immutable release tag yet. For an
authorized evaluation, clone the public source preview and record the exact
commit before installing it project-scoped in the backend being evaluated:

Prerequisites: Git, Python 3.9 or newer for local validation, and Node.js
`>=22.20.0` with `npx` for the pinned Agent Skills CLI.

```bash
git clone https://github.com/danielgandolfi1984/oracle_founder_pack.git oci-founder-toolkit
cd oci-founder-toolkit
git rev-parse HEAD
python3 -B scripts/validate.py
```

Then choose exactly one agent. These commands pin the top-level Agent Skills
CLI package to `skills@1.7.0` for convenience:

```bash
cd /path/to/backend

# Codex
npx --yes skills@1.7.0 add /absolute/path/to/oci-founder-toolkit \
  --skill oci-founder -a codex --copy -y

# Or Cursor
npx --yes skills@1.7.0 add /absolute/path/to/oci-founder-toolkit \
  --skill oci-founder -a cursor --copy -y

# Or Claude Code
npx --yes skills@1.7.0 add /absolute/path/to/oci-founder-toolkit \
  --skill oci-founder -a claude-code --copy -y

npx --yes skills@1.7.0 list --json
```

`npx` can still resolve ranged transitive dependencies differently over time.
These end-user commands therefore are not a bit-for-bit replay of the formal
qualification. The repository's lifecycle runner uses the committed npm lock,
`npm ci --ignore-scripts`, the reviewed package integrity, and reviewed CLI file
hashes before executing the installer.

Run only one of the three add commands. Cursor also reads the Claude and Codex
compatibility directories, so multi-agent copies of the same skill can create
an unresolved duplicate-discovery case. Confirm that `oci-founder` appears for
the selected agent before use. A
standalone skill copy intentionally does not include the top-level executable
blueprints, upstream lock, or upstream verifier. It therefore fails closed for
both the Container API preview and upstream operational routing unless the
reviewed full toolkit dependency is explicitly available. If a user explicitly
requests the Container API preview, provide the reviewed full toolkit checkout
as a readable workspace or use a qualified full plugin package. If upstream
service procedures are required, provide the full toolkit lock and verifier,
verify the exact checkout first, and only then use the project-scoped install
flow above. The included plugin manifests are packaging prototypes, and native
full-plugin installation and publication are not release-qualified yet.

To replace the project-scoped copy with another reviewed local version, update
the checkout, remove the old copy from the same backend project, and install it
again. The local-checkout lifecycle does not use `skills update`:

```bash
npx --yes skills@1.7.0 remove oci-founder -y
npx --yes skills@1.7.0 add /absolute/path/to/oci-founder-toolkit \
  --skill oci-founder -a codex --copy -y
```

The reinstall example uses Codex. The remove command intentionally omits `-a`:
with `skills@1.7.0`, an agent-filtered removal can report success while leaving
the universal `.agents` copy used by Codex or Cursor. This is safe for the
recommended one-agent installation; it removes every copy of the named
`oci-founder` skill in the selected scope. The upstream Oracle domains are
separate dependencies and must be installed, updated, and removed deliberately.

Global installation is a useful eventual workflow because founders use the
skill from many backend repositories, but global-profile lifecycle has not been
release-qualified. It is therefore not the quickstart default.

See the [host qualification playbook](docs/HOST-QUALIFICATION.md) for the exact
installation evidence and remaining native-host gates.

## First use

Ask the `oci-founder` skill for a read-only assessment or a focused decision.
Good prompts include:

```text
I have a FastAPI service in this repository and know AWS, not OCI. Create an OCI founder plan. Do not provision anything.
```

```text
Compare the Container API and Function API paths for this Node backend. Include cost and operational tradeoffs, but use no fixed prices.
```

```text
I currently run on Cloud Run and Cloud SQL. Translate the architecture to OCI and identify every non-equivalent mapping.
```

A full assessment can produce a `founder-plan.md` proposal. A focused question
gets a focused answer and must not trigger a founder plan unless the user asks
for one. Any cloud mutation remains a separate, explicitly approved step.

## Golden paths

| Path | Best fit | Core OCI services | Existing upstream reuse |
|---|---|---|---|
| [Container API preview](blueprints/container-api/README.md) | Existing Dockerized HTTP API without Kubernetes requirements | Container Instances, Container Registry, API Gateway, VCN, explicit log collection, Monitoring | General OCI router; reusable Container Instances procedures remain a proposed upstream contribution |
| Function API | Event-driven or request-driven functions with bursty usage | OCI Functions, Container Registry, API Gateway, VCN, Logging, Monitoring | `oci-functions-deploy` and `oci-functions-troubleshoot` |

OKE is a graduation path, not the default. The official upstream OKE skills already cover cluster design and troubleshooting.

## Design principles

- Journey-first, not service-catalog-first.
- CLI, SDK, and Terraform friendly; the Console is not the primary workflow.
- Read-only discovery before recommendations.
- No OCI write, IAM change, `terraform apply`, or destroy without an explicit preview and approval.
- No fixed price, Free Tier, quota, region, or service-limit claim without current verification.
- One portable skill source, with thin platform manifests around it.
- Service-level knowledge goes upstream; founder-specific composition stays here.

## Repository map

```text
.
├── plugin.json                       # Agent Plugins v1 (Cursor and compatible hosts)
├── .codex-plugin/plugin.json         # Codex compatibility manifest
├── .claude-plugin/plugin.json        # Claude Code manifest
├── skills/oci-founder/               # Portable Agent Skill
├── blueprints/container-api/         # Sandbox-only 0.2 field preview
├── docs/                              # Product, architecture, roadmap, decisions
├── packaging/                         # Archive-specific evaluation readmes
├── schemas/                           # Reviewed Agent Plugins schema snapshot
├── upstream/                          # Oracle Skills provenance and lock
├── scripts/build_release.py           # Deterministic allowlisted package builder
├── scripts/validate.py                # Dependency-free repository checks
├── scripts/qualify_hosts.py           # Read-only host and validator preflight
├── scripts/verify_oracle_skills_lock.py # Offline upstream-lock verifier
├── scripts/probe_codex_native.py       # Explicit opt-in native Codex probe
└── tests/prompts/                     # Cross-agent behavioral smoke cases
```

## Validate

Run the dependency-free checks from this directory:

```bash
python3 scripts/validate.py
python3 scripts/validate_agent_plugin_schema.py
python3 scripts/scan_release_sources.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 -m unittest discover -s blueprints/container-api/tests -v
terraform fmt -check -recursive blueprints/container-api/terraform
python3 scripts/build_release.py check
python3 scripts/qualify_skill_install.py --allow-download
```

The release and repository-source secret scan passes locally. The renewed
read-only host-preflight receipt passes source validation at the current skill
fingerprint and records `release_qualified: false`; it does not close any
native-host or public-release gate.

The native Codex probe is intentionally separate from passive validation: it
acquires only the reviewed installer lock contents, either through an explicit
download or a supplied verified offline npm cache, and starts one authenticated
model session. Acquisition and model execution require explicit opt-in. Use a
fresh temporary receipt path; the runner refuses to overwrite an existing file
by default:

```bash
python3 scripts/probe_codex_native.py \
  --allow-download \
  --allow-model-session \
  --output /private/tmp/oci-founder-codex-native-probe.json
```

Before authorizing those effects, the hardened runner's current unit contracts
can be replayed without a model session:

```bash
python3 -B -m unittest tests.test_probe_codex_native -v
```

The runner installs a project-scoped copy into a disposable Git fixture, invokes
`$oci-founder` with `codex exec --ephemeral` in a read-only sandbox, places deny
shims for `oci`, `terraform`, `fn`, `docker`, and `kubectl` first on `PATH`,
records redacted hashes and effects, removes the copy, and deletes the fixture.
Its dated receipt is historical: it recorded probe Q2/Q3 as `PASS`, while the
current assessment normalizes Q2 to `PASS_WITH_RESERVATIONS` and Q3 to
`PARTIAL`. The hardened runner's 12 unit contracts pass, and reviewed installer
acquisition can use a verified offline npm cache. Its fresh native renewal is
`BLOCKED` only because a new authenticated model session and external model
egress were not authorized. No model session or cloud mutation occurred in that
renewal. Historical native evidence:
[`tests/results/2026-09-18-codex-native-runner-probe.json`](tests/results/2026-09-18-codex-native-runner-probe.json).
Current assessment:
[`tests/results/2026-09-18-codex-native-runner-assessment.json`](tests/results/2026-09-18-codex-native-runner-assessment.json).
Targeted current-skill assessment:
[`tests/results/2026-09-18-skill-revision-assessment.json`](tests/results/2026-09-18-skill-revision-assessment.json).
Formal Q2 and Q3 remain `BLOCKED`.

The installed Codex development validators can be replayed with the pinned
PyYAML wheel hashes documented in [the release procedure](docs/RELEASING.md).
Claude Code's native strict validator can run only when its CLI is present. See
the [platform compatibility matrix](docs/COMPATIBILITY.md).
The preflight procedure and the distinction between app presence and runtime
qualification are in [host qualification](docs/HOST-QUALIFICATION.md).

## Product target

The executable MVP target is measurable: a backend developer new to OCI should
be able to reach a verified OCI endpoint in under 60 minutes using Codex,
Cursor, or Claude Code, without relying on the Console for the main workflow.
Neither package `0.1.0` nor the `0.2.0-preview.3` blueprint has demonstrated this target in a live sandbox tenancy.

Read the full [product brief](docs/PRODUCT.md) and [architecture](docs/ARCHITECTURE.md).
The exact local build and public-release gates are in
[the release procedure](docs/RELEASING.md).

## Source policy

Shipped service claims must be supported by current public Oracle documentation
or a reviewed `oracle/skills` snapshot. Authorized internal Oracle knowledge
sources are also reviewed read-only to detect internal standards, field
lessons, terminology, and missing release gates. Internal
material is validation input, not content to copy into this distributable
repository; internal-only IAM examples, identifiers, retention values, and
organization-specific workflows are excluded. Pricing, Free Tier, regional
availability, quotas, and service behavior are always re-verified against
current public sources and a real target before use.

The latest review and the resulting open gates are recorded in
[`docs/VALIDATION.md`](docs/VALIDATION.md).

## Sources

- [Oracle Skills](https://github.com/oracle/skills)
- [OCI Container Instances](https://docs.oracle.com/en-us/iaas/Content/container-instances/overview-of-container-instances.htm)
- [OCI Functions](https://docs.oracle.com/en-us/iaas/Content/Functions/home.htm)
- [OCI Terraform Provider](https://docs.oracle.com/en-us/iaas/Content/dev/terraform/home.htm)
- [Open Agent Skills specification](https://agentskills.io/specification)
- [Agent Plugins specification](https://agent-plugins.org/specification)
