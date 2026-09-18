# OCI Founder Toolkit — full evaluation package

This archive contains the portable `oci-founder` skill plus the sandbox-only
Container API blueprint. It is not a public release, marketplace package, or
production-supported deployment path. It grants no public-use or redistribution
rights. Read `LICENSE` before using or sharing it.

The public source evaluation preview is
`https://github.com/danielgandolfi1984/oracle_founder_pack`. Public source
access does not make this archive an approved release; use only a reviewed
commit whose identity you recorded before installation.

## Package contents

- root Agent Plugins v1 manifest;
- Codex and Claude Code compatibility manifests;
- portable `skills/oci-founder` planning and routing skill;
- `blueprints/container-api` version `0.2.0-preview.3`;
- immutable `oracle/skills` source-review record and offline, read-only verifier;
- license and third-party notices.

The archive excludes presentations, editor build files, tests, development
tools, credentials, Terraform state and plans, generated receipts, caches, and
local environment files.

## Install the skill from this extracted package

From the backend project where the skill should be visible, choose exactly one
agent and use the absolute path to this extracted directory:

Prerequisite: Node.js `>=22.20.0` with `npx`.

```bash
# Codex (project-scoped evaluation)
npx --yes skills@1.7.0 add /absolute/path/to/oci-founder-toolkit \
  --skill oci-founder -a codex --copy -y

npx --yes skills@1.7.0 list -a codex --json
```

Replace `codex` with `cursor` or `claude-code` for the one agent being tested.
Use the same agent value in both the `add` and `list` commands. Run the commands
from the target backend and install for exactly one agent. Project-scoped
installation is the qualified default. Global installation, native full-plugin
installation, and public marketplace installation remain release gates. The
JSON result should contain a project-scoped skill named `oci-founder`.

The top-level CLI package is pinned for convenience, but `npx` may resolve
ranged transitive dependencies differently over time. This short end-user
command is therefore not a bit-for-bit installer replay. The source repository
contains a locked lifecycle qualification runner for formal package evidence.

To remove the project-scoped copy, run the command from the same backend
project and omit an agent filter:

```bash
npx --yes skills@1.7.0 remove oci-founder -y
```

## First use

Open the target backend in the same agent selected during installation. Use the
host's exact invocation for the first smoke test:

| Host | Exact first request | Refresh after installation |
|---|---|---|
| Codex | `Use $oci-founder. Inspect this backend read-only and propose the smallest safe OCI path. Do not provision or change anything.` | Restart only if the skill is not discovered |
| Cursor | `/oci-founder Inspect this backend read-only and propose the smallest safe OCI path. Do not provision or change anything.` | Reopen or reload the target workspace |
| Claude Code | `/oci-founder Inspect this backend read-only and propose the smallest safe OCI path. Do not provision or change anything.` | Restart if the session began before `.claude/skills` existed |

An expected first response leads with one recommendation, separates repository
evidence from assumptions, explains important cloud non-equivalences, identifies
identity, network, secret, cost, observability, and teardown guardrails, states
what remains unverified, and ends with one next action. It must not create OCI
resources, change IAM, run `terraform apply`, expose a secret, or claim an
unverified fixed price.

The full package makes the sandbox-only Container API blueprint and the upstream
lock verifier readable. Their presence does not authorize use of credentials,
installation of upstream skills, an OCI command, or a cloud mutation.

## Container API boundary

The included Container API path is an executable field preview for an OCI
sandbox. Read `blueprints/container-api/README.md` completely before using it.
It has not been planned or applied in a real OCI tenancy and must not be
presented as production-ready, highly available, or zero-downtime.

Any OCI mutation, IAM change, apply, or destructive operation requires the
blueprint's exact preview, target, lineage, receipt, and approval gates.

## Troubleshooting

### `oci-founder` is not listed

- Confirm that both commands ran from the target backend rather than from the
  extracted toolkit.
- Confirm that the toolkit argument is an absolute path and that
  `node --version` reports `22.20.0` or newer.
- Use the same `-a codex`, `-a cursor`, or `-a claude-code` value for `add` and
  `list`.
- Remove the project copy with `npx --yes skills@1.7.0 remove oci-founder -y`,
  then reinstall it for exactly one agent if duplicate copies are present.

### The skill is listed but the host does not invoke it

Apply the host-specific refresh in the table above, reopen the target backend,
and use the explicit `$oci-founder` or `/oci-founder` request again. Do not copy
the same skill into multiple compatible agent directories in one project;
duplicate discovery is not qualified.

### A service procedure remains unavailable

The archive records the reviewed `oracle/skills` commit and includes its offline
verifier, but it does not bundle or silently install upstream service skills.
Keep the response at planning level unless an exact upstream checkout has been
obtained deliberately and passes the included verifier.

## Help and security status

- **Get help:** read the current
  [support status](https://github.com/danielgandolfi1984/oracle_founder_pack/blob/main/SUPPORT.md).
  This evaluation has no approved public support channel or SLA.
- **Report a vulnerability:** read the current
  [security status](https://github.com/danielgandolfi1984/oracle_founder_pack/blob/main/SECURITY.md).
  Do not disclose vulnerability details, credentials, private OCIDs, Terraform
  state, or exploit evidence in a public GitHub issue. No public confidential
  intake has been approved yet.
