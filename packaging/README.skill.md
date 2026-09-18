# OCI Founder skill — evaluation package

This archive contains the portable `oci-founder` planning and routing skill for
local evaluation. It is not a public release and grants no public-use or
redistribution rights. Read `LICENSE` before using or sharing it.

The public source evaluation preview is
`https://github.com/danielgandolfi1984/oracle_founder_pack`. Public source
access does not make this archive an approved release; use only a reviewed
commit whose identity you recorded before installation.

The package is intentionally planning-only. It does not contain the executable
Container API blueprint, upstream Oracle service skills, the full toolkit's
`upstream/oracle-skills.lock.json`, or its
`scripts/verify_oracle_skills_lock.py`. Those last two paths are explicit
external dependencies; the provenance values disclosed inside the skill are
not a substitute for running the verifier. The skill-only package therefore
fails closed at planning level for OCI Functions, OKE, Enterprise AI, Oracle
Database, and other upstream operational procedures unless the reviewed full
toolkit lock and verifier are available and the exact upstream checkout passes
verification. Do not silently follow a path into a separate checkout or claim
that verification succeeded when it was not run.

## Install from this extracted package

From the backend project where the skill should be visible, choose exactly one
agent and use the absolute path to this extracted directory:

Prerequisite: Node.js `>=22.20.0` with `npx`.

```bash
# Codex (project-scoped evaluation)
npx --yes skills@1.7.0 add /absolute/path/to/oci-founder-skill-0.1.0-evaluation \
  --skill oci-founder -a codex --copy -y

npx --yes skills@1.7.0 list --json
```

Replace `codex` with `cursor` or `claude-code` for the one agent being tested.
Run exactly one add command for exactly one agent, from the target backend, and
do not add `-g`. Project-scoped installation is the qualified default. Global
installation and native runtime behavior across all three hosts remain release
gates.

To remove the project-scoped copy, run the command from the same backend
project and omit an agent filter:

```bash
npx --yes skills@1.7.0 remove oci-founder -y
```

The top-level CLI package is pinned for convenience, but this short end-user
command is not a bit-for-bit installer replay. The source repository contains a
locked lifecycle qualification runner for formal package evidence.

## First use

```text
Use $oci-founder. Inspect this backend read-only and propose the smallest safe
OCI path. Do not provision or change anything.
```

For a focused question, ask for the decision directly; the skill should return
that focused answer without generating or imposing a `founder-plan.md`.

Any OCI mutation, IAM change, apply, or destructive operation requires a
separate preview and explicit approval immediately before the action.
