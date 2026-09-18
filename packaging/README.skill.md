# Founder Toolkit for OCI — skill public preview

This public-preview archive contains the portable `oci-founder` planning and
routing skill. It is licensed under UPL-1.0 and may be used, modified, and
redistributed under that license. Read `LICENSE` before using or sharing it.

This is an independent personal project by Daniel Gandolfi. It is not an Oracle
product and is not sponsored, endorsed, maintained, or supported by Oracle. It
has no SLA or Oracle Support coverage. Source and releases:
`https://github.com/danielgandolfi1984/oracle_founder_pack`.

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
# Codex (project-scoped preview)
npx --yes skills@1.7.0 add /absolute/path/to/oci-founder-skill-0.1.0-preview \
  --skill oci-founder -a codex --copy -y

npx --yes skills@1.7.0 list -a codex --json
```

Replace `codex` with `cursor` or `claude-code` for the one agent being tested.
Use the same agent value in both the `add` and `list` commands. Run exactly one
add command for exactly one agent, from the target backend, and do not add `-g`.
Project-scoped installation is the qualified default. Global installation and
native runtime behavior across all three hosts remain release gates. The JSON
result should contain a project-scoped skill named `oci-founder`.

To remove the project-scoped copy, run the command from the same backend
project and omit an agent filter:

```bash
npx --yes skills@1.7.0 remove oci-founder -y
```

The top-level CLI package is pinned for convenience, but this short end-user
command is not a bit-for-bit installer replay. The source repository contains a
locked lifecycle qualification runner for formal package evidence.

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

For a focused question, ask for the decision directly; the skill should return
that focused answer without generating or imposing a `founder-plan.md`.

Any OCI mutation, IAM change, apply, or destructive operation requires a
separate preview and explicit approval immediately before the action.

## Troubleshooting

### `oci-founder` is not listed

- Confirm that both commands ran from the target backend rather than from the
  extracted package.
- Confirm that the package argument is an absolute path and that
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

### The skill stops at planning

That is the intended boundary of this skill-only package. It excludes the
Container API blueprint, the upstream Oracle service skills, and the full
toolkit verifier. Their absence must not be bypassed with an unreviewed checkout.

## Help and security status

- **Get help:** read the current
  [support status](https://github.com/danielgandolfi1984/oracle_founder_pack/blob/main/SUPPORT.md).
  Community support is best effort and has no SLA or Oracle Support coverage.
- **Report a vulnerability:** read the current
  [security status](https://github.com/danielgandolfi1984/oracle_founder_pack/blob/main/SECURITY.md).
  Use GitHub private vulnerability reporting. Do not disclose vulnerability
  details, credentials, private OCIDs, Terraform state, or exploit evidence in
  a public GitHub issue.
