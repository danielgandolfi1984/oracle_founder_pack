# Founder Toolkit for OCI

[![Validation](https://github.com/danielgandolfi1984/oracle_founder_pack/actions/workflows/validate.yml/badge.svg?branch=main)](https://github.com/danielgandolfi1984/oracle_founder_pack/actions/workflows/validate.yml)

> Plan your backend's path to OCI with the coding agent you already use.

Founder Toolkit for OCI helps technical founders and backend developers who
know AWS, Google Cloud, or Azure plan their first steps on Oracle Cloud
Infrastructure (OCI). Use the `oci-founder` skill to assess an existing backend,
understand important differences between clouds, and choose a small OCI
architecture with one practical next step.

This is an independent personal project created and maintained by
[Daniel Gandolfi](https://github.com/danielgandolfi1984), who works at Oracle
and publishes here in his personal capacity. The views expressed here are his
own and do not represent Oracle. This is not an Oracle product and is not
sponsored, endorsed, maintained, or supported by Oracle.

Start by installing the skill in one backend repository for Codex, Cursor, or
Claude Code using the quickstart below. Your first request is a read-only
backend assessment; no OCI tenancy or credentials are needed. Native behavior
across all three agents remains under validation.

## Start here: first OCI recommendation in about 10 minutes

The [`v0.1.1` planning skill](https://github.com/danielgandolfi1984/oracle_founder_pack/releases/tag/v0.1.1)
is a public preview under [UPL-1.0](LICENSE). You need Git, Node.js
`>=22.20.0` with `npx`, and an installed, authenticated coding agent. Install it
in one backend repository; no OCI tenancy, OCI CLI, or OCI credentials are
needed:

```bash
cd /absolute/path/to/your-backend
npx --yes skills@1.7.0 add \
  'https://github.com/danielgandolfi1984/oracle_founder_pack#v0.1.1' \
  --skill oci-founder -a codex --copy -y
npx --yes skills@1.7.0 list -a codex --json
```

Use `cursor` or `claude-code` instead of `codex` for exactly one selected
agent. The selected coding agent must already be installed and authenticated;
the installer only copies the skill. Then use the exact invocation for that
host:

| Host | First request |
|---|---|
| Codex | `Use $oci-founder. Inspect this backend read-only. I know AWS, not OCI. Recommend the smallest safe OCI path and one next step. Do not provision or change anything.` |
| Cursor | `/oci-founder Inspect this backend read-only. I know AWS, not OCI. Recommend the smallest safe OCI path and one next step. Do not provision or change anything.` |
| Claude Code | `/oci-founder Inspect this backend read-only. I know AWS, not OCI. Recommend the smallest safe OCI path and one next step. Do not provision or change anything.` |

The skill should lead with one recommendation, distinguish repository evidence
from assumptions, explain important cloud non-equivalences, and keep every OCI
mutation behind a separate preview and approval. Follow the
**[guided quickstart](docs/QUICKSTART.md)** for Cursor and Claude Code commands,
expected output, use-case prompts, updating, removal, and troubleshooting.

## Help and security status

- **[Get help](SUPPORT.md):** use GitHub Issues for best-effort community help.
  There is no SLA or Oracle Support coverage.
- **[Report a vulnerability](SECURITY.md):** use GitHub private vulnerability
  reporting. Never disclose vulnerability details, credentials, private OCIDs,
  Terraform state, or exploit evidence in a public issue.

## Status

This repository publishes an independent **public preview**, not an
Oracle-supported or production-qualified product. Skill `0.1.1` provides
shorter focused answers and full founder plans when requested, under UPL-1.0.
The published `v0.1.1` tag is fixed at commit
`8765266e3ef77110b30827d5c89da7cf1b15ee08`, which passed
[CI run 35385557348](https://github.com/danielgandolfi1984/oracle_founder_pack/actions/runs/35385557348).
Public-tag Codex installation, removal, and reinstall passed, and all six
release assets were downloaded again and verified. See the
[publication record](tests/results/2026-09-18-v0.1.1-publication.json).
The separately versioned
[`0.2.0-preview.3` Container API blueprint](blueprints/container-api/README.md)
is sandbox-only and has not been applied in an OCI tenancy.

The preceding [`v0.1.0` release](https://github.com/danielgandolfi1984/oracle_founder_pack/releases/tag/v0.1.0)
is fixed at commit
[`6cf08bf30febc434cefed228f53c43a1f8802ec2`](https://github.com/danielgandolfi1984/oracle_founder_pack/commit/6cf08bf30febc434cefed228f53c43a1f8802ec2),
which passed the complete workflow in
[run 35375372149](https://github.com/danielgandolfi1984/oracle_founder_pack/actions/runs/35375372149).
The public tag passed project-scoped Codex install/list/remove with the reviewed
skill hash, and all published assets were downloaded again and verified.
Version `0.1.1` does not replace that immutable release. Its source and package
lifecycles passed all three installer layouts;
its [prepublication assessment](tests/results/2026-09-18-v0.1.1-assessment.json)
records the separate behavior checks. Native Cursor/Claude qualification, cross-host behavioral replay, and
live OCI field validation remain open.
See the [validation record](docs/VALIDATION.md) for hashes, receipts, Q0–Q4
status, and remaining gates.

There is no marketplace or registry coordinate. Public use, modification, and
redistribution are governed by UPL-1.0; technical limitations and the no-SLA
support boundary still apply.

## What works today

| Founder need | Current capability | Dependency | Important boundary |
|---|---|---|---|
| Understand OCI, translate another cloud, assess a backend, or create a founder plan | Available in the portable `oci-founder` skill | One project-scoped skill copy | Native behavior is not yet qualified across all three hosts |
| Review or generate the Container API sandbox path | Available in the full source checkout | Explicit request plus `blueprints/container-api` | No live OCI plan/apply/rollback/destroy evidence; not production-ready |
| Plan a Function API and route an operational procedure | Planning available | Reviewed `oracle/skills` checkout and verified Functions skills for execution | The portable skill alone fails closed at planning level |
| Plan OKE, Enterprise AI, or Oracle Database work | Orientation and routing available | Separately verified official Oracle domain skill | This toolkit does not duplicate the service procedure |
| Claim a supported production deployment | Not available | Native host, operational support, security, and live field gates | A green CI run or generated Terraform is not production evidence |

## Guided founder documentation

| If you need to… | Start here |
|---|---|
| Install, verify discovery, make the first request, update, or remove the skill | [10-minute quickstart](docs/QUICKSTART.md) |
| Pick a concrete founder/developer job and copy a safe prompt | [Use-case recipes](docs/USE-CASES.md) |
| Decode tenancy, compartments, VCNs, OCIDs, identities, budgets, quotas, and other OCI terms | [OCI glossary](docs/GLOSSARY.md) |
| Establish the minimum identity, network, cost, observability, delivery, and teardown guardrails | [Founder Baseline](docs/FOUNDER-BASELINE.md) |
| Check exact evidence, open gates, or release status | [Validation record](docs/VALIDATION.md) and [compatibility matrix](docs/COMPATIBILITY.md) |
| Review the personal publisher, license, support, and brand decision | [Accepted license and publisher ADR](docs/decisions/0003-public-license-and-publisher.md) |

## Why this exists

Cloud-experienced founders usually do not lack backend skills. They lack an OCI mental model at the exact moment they need to make architecture, IAM, networking, and cost decisions. General coding agents often reinforce the AWS/GCP/Azure concepts that dominate public examples.

Founder Toolkit for OCI closes that gap with three layers:

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

npx --yes skills@1.7.0 list -a codex --json
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
`LICENSE.txt` without network access or mutation. The real locked checkout
[passed verification](tests/results/2026-09-18-oracle-skills-verified.json),
and the OCI domain passed an isolated Codex
[project installation lifecycle](tests/results/2026-09-18-oracle-skills-verified-codex-lifecycle.json)
with an exact source/installed hash match. That check retained all nine domain
`SKILL.md` files, but did not exercise native discovery, sibling Database
references, or cloud operations. Verify your own checkout before installation.

## Install the public preview

Use the `v0.1.1` source tag directly, or clone that tag when you want
to inspect and validate the complete toolkit before installation:

Prerequisites: Git, Python 3.9 or newer for local validation, Node.js
`>=22.20.0` with `npx` for the pinned Agent Skills CLI, and the selected coding
agent already installed and authenticated.

```bash
git clone --branch v0.1.1 --depth 1 \
  https://github.com/danielgandolfi1984/oracle_founder_pack.git \
  oci-founder-toolkit
cd oci-founder-toolkit
git rev-parse HEAD
python3 -B scripts/validate.py
```

Record the printed commit with your installation notes and compare it with the
[`v0.1.1` release](https://github.com/danielgandolfi1984/oracle_founder_pack/releases/tag/v0.1.1).
The earlier `v0.1.0` tag and assets remain unchanged.

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

npx --yes skills@1.7.0 list -a codex --json
```

The final line verifies the Codex example. Replace `codex` there with the same
agent selected by the add command.

Alternatively, install directly from the immutable tag by replacing the local
path in exactly one command with
`https://github.com/danielgandolfi1984/oracle_founder_pack#v0.1.1`.

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
Use an explicit invocation for the first smoke test:

| Host | Explicit first use |
|---|---|
| Codex | `Use $oci-founder. Inspect this backend read-only and recommend the smallest safe OCI path. Do not provision anything.` |
| Cursor | `/oci-founder Inspect this backend read-only and recommend the smallest safe OCI path. Do not provision anything.` |
| Claude Code | `/oci-founder Inspect this backend read-only and recommend the smallest safe OCI path. Do not provision anything.` |

Reload the Cursor workspace after installation. Restart Claude Code if its
session began before `.claude/skills` existed; restart Codex only if the skill
is not discovered. Further prompts can include:

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
├── docs/QUICKSTART.md                 # Founder/developer guided installation and first use
├── docs/GLOSSARY.md                   # OCI terms, cross-cloud models, and traps
├── docs/USE-CASES.md                  # Copyable founder/developer recipes
├── docs/FOUNDER-BASELINE.md           # Minimum governance, cost, and safety baseline
├── docs/                              # Product, architecture, roadmap, decisions
├── packaging/                         # Archive-specific public-preview readmes
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
fingerprint and records `release_qualified: false`; that field means the
toolkit is not qualified as a supported cross-host or production release. It
does not prohibit the clearly scoped UPL-licensed public preview.

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

The `0.1.1` [prepublication native Codex probe](tests/results/2026-09-18-v0.1.1-codex-native.json)
passed with reservations against the candidate skill. It loaded the
skill and references, passed all four machine assertions, returned valid
structured output, and removed the installed copy. No project edits, unreviewed
commands, OCI commands, or cloud mutations were observed. The probe records Q2
`PASS` and Q3 `PARTIAL`: it covers one explicit prompt, reuses the signed-in
profile for authentication, and does not install upstream dependencies or
replay the 24-case suite. Formal Q2/Q3 remain `BLOCKED`.

In this single comparison with the same prompt, schema, and fixture, the
recommendation fell from 1,489 to 185 words and read two references instead of
four. Independent semantic review passed; this is not a general
performance or quality guarantee. A separate requested full plan retained all
ten sections.

The initial failed run, harness fixes, independent review, and separate `0.1.1`
prepublication evidence are retained in [the validation record](docs/VALIDATION.md). The runner's
unit contracts pass, and installer acquisition can use a verified offline npm
cache.

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
Neither preview `0.1.0`, preview `0.1.1`, nor the `0.2.0-preview.3`
blueprint has demonstrated this target in a live sandbox tenancy.

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

## License and trademarks

Copyright (c) 2026 Daniel Gandolfi. Licensed under the
[Universal Permissive License 1.0](LICENSE).

Oracle, Java, MySQL, and NetSuite are registered trademarks of Oracle and/or
its affiliates. Other names may be trademarks of their respective owners.
Oracle and OCI names are used descriptively to identify the platform this
independent toolkit works with; no sponsorship or endorsement is implied.
