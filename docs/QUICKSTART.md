# Founder Toolkit for OCI quickstart

Use this guide to give Codex, Cursor, or Claude Code the `oci-founder` skill in
one backend repository and get a planning-only OCI recommendation. The install
and first prompt do not require an OCI tenancy, OCI CLI, or OCI credentials.
The installer writes project-scoped skill metadata; the read-only first prompt
does not modify application source or provision cloud resources.

This repository publishes an independent **public preview** under
[UPL-1.0](../LICENSE). It is a personal project by Daniel Gandolfi, not an
Oracle product, and has no Oracle Support coverage or SLA. Use the immutable
`v0.1.0` tag and keep the installation project-scoped.

## 1. Check the prerequisites

You need:

- Git;
- Python 3.9 or newer to validate the checkout;
- Node.js `>=22.20.0` with `npx` for the pinned Agent Skills CLI; and
- the selected Codex, Cursor, or Claude Code host already installed and
  authenticated; and
- the backend repository where you want the skill to be available.

Do not paste OCI API keys, auth tokens, private keys, passwords, or Terraform
state into an agent prompt. None are needed for this quickstart.

## 2. Clone and validate the exact source

```bash
git clone --branch v0.1.0 --depth 1 \
  https://github.com/danielgandolfi1984/oracle_founder_pack.git \
  oci-founder-toolkit
cd oci-founder-toolkit
git rev-parse HEAD
python3 -B scripts/validate.py
```

Save the commit printed by `git rev-parse HEAD` with your notes. Do not continue
if validation fails. The tag is the readable release coordinate; the printed
40-character commit is the immutable source identity.

## 3. Install in one backend and for one agent

Change to the backend that should use the skill. Replace the toolkit path below
with the absolute path to the checkout from step 2, then run exactly one add
command.

```bash
cd /absolute/path/to/your-backend

# Codex
npx --yes skills@1.7.0 add /absolute/path/to/oci-founder-toolkit \
  --skill oci-founder -a codex --copy -y

# OR Cursor
npx --yes skills@1.7.0 add /absolute/path/to/oci-founder-toolkit \
  --skill oci-founder -a cursor --copy -y

# OR Claude Code
npx --yes skills@1.7.0 add /absolute/path/to/oci-founder-toolkit \
  --skill oci-founder -a claude-code --copy -y
```

The command copies the skill into the current backend. It does not install it
globally. Do not run all three commands in the same project: Cursor can discover
several compatible skill directories, and duplicate-name precedence has not
been qualified.

To skip the local checkout, replace `/absolute/path/to/oci-founder-toolkit` in
exactly one add command with the immutable source coordinate:

```text
https://github.com/danielgandolfi1984/oracle_founder_pack#v0.1.0
```

Pinning `skills@1.7.0` fixes the top-level installer version, but `npx` can
resolve ranged transitive dependencies differently over time. This convenience
command is not the bit-for-bit installer replay used by the repository's formal
lifecycle runner.

Confirm the selected installation. Replace `codex` with the same agent name you
used above:

```bash
npx --yes skills@1.7.0 list -a codex --json
```

The JSON result should contain a project-scoped skill named `oci-founder`. The
qualified destination for Codex and Cursor is `.agents/skills/oci-founder`; for
Claude Code it is `.claude/skills/oci-founder`.

## 4. Make the first request

Open the target backend in the selected agent and use the host's explicit
invocation for the first smoke test:

| Host | Invocation | Refresh after install |
|---|---|---|
| Codex | `Use $oci-founder. ...` or select it through `/skills` | Restart only if the skill is not discovered |
| Cursor | `/oci-founder ...` | Reopen or reload the target workspace |
| Claude Code | `/oci-founder ...` | Restart if the session began before `.claude/skills` existed |

For Codex, use:

```text
Use $oci-founder. Inspect this backend read-only. I know AWS, not OCI.
Recommend the smallest safe OCI path, translate the important service concepts,
list assumptions and cost drivers, and give me one next step. Do not provision
or change anything.
```

For Cursor or Claude Code, replace the first sentence with `/oci-founder` and
keep the remainder of the request unchanged.

A useful first response should include:

- one primary recommendation rather than a catalog of services;
- evidence from the repository, separated from assumptions;
- important AWS, Google Cloud, or Azure non-equivalences;
- identity, network, secret, cost, observability, and teardown guardrails;
- what is still unverified; and
- one next action with its authorization level.

It should not create OCI resources, change IAM, run `terraform apply`, expose a
secret, or claim an unverified fixed price.

## 5. Pick the next founder job

Use a focused prompt when you need one decision:

### Translate an existing architecture

```text
Use the oci-founder skill. My current backend uses Cloud Run and Cloud SQL.
Translate it to OCI, mark every mapping as close, approximate, or without a
direct equivalent, and tell me which workload facts could change the decision.
Planning only.
```

### Choose a runtime

```text
Use the oci-founder skill. Compare OCI Container Instances and OCI Functions
for this repository. Recommend one, explain what would reverse the decision,
and do not default to Kubernetes.
```

### Define the minimum safe foundation

```text
Use the oci-founder skill. Propose a Founder Baseline for this project: project
compartment, human and workload identity, tags, budget alerts, secrets, logs,
Terraform state, and teardown. Do not change OCI.
```

### Understand cost before deployment

```text
Use the oci-founder skill. Identify the directional OCI cost drivers for the
recommended architecture and the inputs needed for a current estimate. Do not
use fixed prices or imply that a budget alert caps spending.
```

For a full repository assessment, ask for a `founder-plan.md`. A focused
question should stay focused and should not force that artifact.

## 6. Know the approval boundary

| Request | What the skill may do by default | What still needs a separate gate |
|---|---|---|
| Explain or compare | Answer from the minimum necessary evidence | Current OCI facts that are time-sensitive must be verified |
| Assess a backend | Inspect read-only and propose a path | Repository edits, dependency installation, and cloud access |
| Generate files | Create only the requested local artifacts and validate them | Any OCI write or credential use |
| Deploy or change OCI | Prepare the exact target, plan, risks, and cost drivers | Explicit approval immediately before mutation |
| Diagnose | Collect and classify read-only evidence | Applying a fix |
| Tear down | Resolve exact state and preview the destroy | Separate destructive approval |

Installation grants no cloud authority. A prompt to design and deploy can
prepare a design and preview, but it must not turn an unseen plan into an
automatic apply.

## 7. Update or remove the local copy

Review and validate a newer release tag before replacing the skill. Replace
`v0.1.0` below with the new tag you intend to adopt:

```bash
git -C /absolute/path/to/oci-founder-toolkit fetch --tags origin
git -C /absolute/path/to/oci-founder-toolkit checkout --detach v0.1.0
python3 -B /absolute/path/to/oci-founder-toolkit/scripts/validate.py
```

Then, from the same backend project used for installation, remove and reinstall
the reviewed local copy:

```bash
npx --yes skills@1.7.0 remove oci-founder -y
npx --yes skills@1.7.0 add /absolute/path/to/oci-founder-toolkit \
  --skill oci-founder -a codex --copy -y
```

Replace `codex` with the one selected agent. The remove command intentionally
has no `-a` filter because the qualified installer version can otherwise leave
the universal project copy in place.

To uninstall without replacing it, run only the remove command from that same
backend project and confirm with
`npx --yes skills@1.7.0 list -a codex --json`, replacing `codex` with the agent
whose copy you removed.

## Troubleshooting

### `oci-founder` is not listed

- Confirm you ran the command from the target backend, not from the toolkit
  checkout.
- Confirm the toolkit argument is an absolute path.
- Check `node --version` and `npx --version`.
- Use the same agent value for add and list.
- Reload the project or start a new agent session after installation.

### The skill appears more than once

From the affected backend, run
`npx --yes skills@1.7.0 remove oci-founder -y`, then install it again for exactly
one agent. Do not combine Codex, Cursor, and Claude Code copies in one project
until duplicate discovery is qualified.

### The skill will plan but will not run a service-specific procedure

That is intentional when only the portable skill copy is available. It does
not contain the top-level Container API blueprint or a verified checkout of the
upstream [`oracle/skills`](https://github.com/oracle/skills) domains. Keep the
reviewed full toolkit checkout available for the blueprint, or follow the
verified upstream flow in the main [`README`](../README.md) before operational
routing.

### You expected a marketplace install

No marketplace or registry coordinate exists yet. Use the immutable GitHub tag
directly or download the archive, checksum, and manifest from the `v0.1.0`
GitHub release. Native full-plugin marketplace installation remains unqualified.

## Continue from here

- Read the [founder and developer use cases](../skills/oci-founder/references/use-cases.md).
- Choose a copyable [founder/developer recipe](USE-CASES.md).
- Use the [OCI glossary](GLOSSARY.md) when a service or governance term is new.
- Review the [Founder Baseline](FOUNDER-BASELINE.md) before generating or
  applying infrastructure.
- Use the [cross-cloud service map](../skills/oci-founder/references/service-map.md).
- Compare the [golden paths](../skills/oci-founder/references/golden-paths.md).
- Review the [security, cost, and mutation guardrails](../skills/oci-founder/references/guardrails.md).
- Check [agent compatibility and open qualification gates](COMPATIBILITY.md).
- Read the [Container API preview](../blueprints/container-api/README.md) only
  when you explicitly want the sandbox implementation path.
