# OCI Founder Toolkit contributor instructions

## Mission

Help backend-first founders move from an existing repository to a secure, observable, cost-aware OCI deployment while using the coding agent they already know.

## Content ownership

- Treat `oracle/skills` as the upstream source for reusable Oracle service procedures.
- Keep this repository focused on end-to-end founder journeys, cross-cloud translation, guardrails, blueprints, and agent adapters.
- Do not copy an upstream skill merely to change its wording. Fix reusable gaps upstream and update the lock after review.
- A temporary local service-level gap must be explicitly labeled `temporary-upstream-gap` and must name an upstream issue or proposed contribution before release.

## Source policy

- Use official Oracle documentation for OCI behavior, IAM verbs, CLI/API syntax, availability, service limits, and pricing inputs.
- Treat pricing, Free Tier eligibility, regional availability, service limits, and product names as time-sensitive. Verify them at task time.
- Preserve direct source links near consequential claims.
- Never invent defaults, environment variables, OCIDs, CLI flags, or IAM policy syntax.

## Safety

- Read-only inspection and planning are the default.
- Show a plan or diff before any OCI mutation.
- Require explicit user approval immediately before IAM changes, resource creation/update, `terraform apply`, or any destructive operation.
- Never store credentials, private keys, auth tokens, database passwords, Terraform state, or generated secrets in the repository.
- Scope teardown to resources identified by state and a deployment receipt. Never use broad tenancy-, compartment-, or account-wide deletion.
- Redact secrets and user-sensitive identifiers from examples, logs, fixtures, and test output.
- Budgets are alerts, not hard spending caps. Pair them with quotas and architecture limits where enforcement is required.

## Portability

- Keep portable skills as immediate children of `skills/`, each with exactly one `SKILL.md`.
- Use only portable Agent Skills frontmatter in shared skills. Put host-specific behavior in thin adapters or manifests.
- Keep `.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`, and root `plugin.json` consistent in name and version.
- Do not duplicate the canonical skill into `.agents/skills`, `.claude/skills`, or `.cursor/skills` in source control.
- Do not put host-specific invocation syntax inside shared skill instructions.

## Quality bar

- Every golden path must define prerequisites, architecture decisions, validation, observability, rollback, and teardown.
- Terraform assets must pass formatting and validation, be idempotent, and avoid secrets in state where practical.
- Stable IAM examples must follow least privilege and must not grant `manage all-resources`.
- Keep `SKILL.md` concise and route conditional detail to `references/`.
- Add or update behavioral prompt cases when changing routing or safety behavior.
- Run `python3 scripts/validate.py` and the relevant host-native validators before release.

## Language

Use English for canonical repository content so it can serve a global founder audience. Translations may be added as maintained, clearly versioned views; do not let them silently diverge from the canonical safety rules.
