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

npx --yes skills@1.7.0 list --json
```

Replace `codex` with `cursor` or `claude-code` for the one agent being tested.
Project-scoped installation is the qualified default. Global installation,
native full-plugin installation, and public marketplace installation remain
release gates.

The top-level CLI package is pinned for convenience, but `npx` may resolve
ranged transitive dependencies differently over time. This short end-user
command is therefore not a bit-for-bit installer replay. The source repository
contains a locked lifecycle qualification runner for formal package evidence.

To remove the project-scoped copy, run the command from the same backend
project and omit an agent filter:

```bash
npx --yes skills@1.7.0 remove oci-founder -y
```

## Container API boundary

The included Container API path is an executable field preview for an OCI
sandbox. Read `blueprints/container-api/README.md` completely before using it.
It has not been planned or applied in a real OCI tenancy and must not be
presented as production-ready, highly available, or zero-downtime.

Any OCI mutation, IAM change, apply, or destructive operation requires the
blueprint's exact preview, target, lineage, receipt, and approval gates.
