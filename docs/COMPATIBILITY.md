# Agent compatibility

The toolkit keeps one skill implementation and multiple thin manifests.

## Packaging matrix

| Host | Package mechanism | Included artifact | Validation status |
|---|---|---|---|
| Codex CLI | Codex compatibility manifest and portable skill | `.codex-plugin/plugin.json` | CLI `0.153.4`; current project-scoped package lifecycle passes; the historical native receipt recorded Q2/Q3 `PASS`, normalized to Q2 `PASS_WITH_RESERVATIONS` and Q3 `PARTIAL`; a targeted current-skill assessment passes but is non-native; a fresh hardened renewal and formal Q2/Q3 remain `BLOCKED` |
| Cursor IDE / Agent | Agent Plugins v1 and portable skill | `plugin.json` | IDE `3.0.12` detected and project-scoped package lifecycle passes, but Cursor Agent is unavailable; duplicate discovery and native runtime validation remain unqualified |
| Claude Code | Claude plugin manifest and portable skill | `.claude-plugin/plugin.json` | Project-scoped package lifecycle passes, but Claude Code is unavailable on the dated host; strict validation and runtime discovery remain unqualified |

All three adapters point to `skills/oci-founder/SKILL.md`. This table describes
packaging intent, not a production-support claim. See [`VALIDATION.md`](VALIDATION.md)
for exact evidence and open gates. Public release remains `BLOCKED`.

The public source evaluation on `main` at
[`danielgandolfi1984/oracle_founder_pack`](https://github.com/danielgandolfi1984/oracle_founder_pack)
is technically cloneable for an authorized evaluation, but it is not a
qualified immutable install coordinate. No tag, GitHub release, marketplace
entry, registry coordinate, or package coordinate has been published, and the
restrictive evaluation license plus legal, OSS, publisher, support, and Oracle
repository-ownership gates still apply.

Both the skill-only and full-toolkit evaluation archives have passed
project-scoped install/list/remove/reinstall in separate Codex, Cursor, and
Claude Code layouts. These are filesystem-layout and package-lifecycle results,
not native Cursor Agent or Claude Code runtime qualification. The current
skill-only SHA-256 is
`876fe40dbac703b092110f106f6797fa7eaa753c6bb9b711e61e67f61c2fd315`;
the current full-toolkit SHA-256 is
`62501591cdc53b2e366dd7fbe39c7c87a47a838ff034ff7ad734040d1f96eaa8`,
with internal root `oci-founder-toolkit/`. Their renewed exact raw receipts are
committed and SHA-256-bound by the current summaries linked from
[`VALIDATION.md`](VALIDATION.md).

The root Agent Plugins manifest intentionally does not declare a `skills` field. Agent Plugins v1 discovers immediate child skills in `skills/`. Claude Code also discovers that standard directory automatically.

## Repository instructions

- Codex and Cursor can use `AGENTS.md` while this repository is the open
  project. It is not a component of the portable Agent Plugins package.
- Claude Code does not use `AGENTS.md` as its native project-instruction file,
  so this repository's `CLAUDE.md` imports `@AGENTS.md`. A packaged Claude
  plugin does not load its root `CLAUDE.md`; runtime safety therefore remains
  in the shared skill.
- Host-specific rules must stay thin and must not change the shared mutation or secret-handling policy.

## Invocation

Invocation syntax varies by host and surface. Keep it in user documentation, not inside the shared skill:

- Codex CLI/IDE supports skill selection through `/skills` and `$` mentions.
- Claude Code exposes installed plugin skills as slash shortcuts and can also invoke them implicitly.
- Cursor discovers Agent Skills and can select them based on the skill description or explicit user selection.

## Evaluation installation

From the target backend, install from an absolute path for the one agent you
intend to use. This project-scoped convenience command pins the top-level Agent
Skills CLI package to the version exercised by the lifecycle test:

```bash
npx --yes skills@1.7.0 add /absolute/path/to/oci-founder-toolkit \
  --skill oci-founder -a codex --copy -y
npx --yes skills@1.7.0 list --json
```

The command is not a bit-for-bit replay of the formal qualification because
`npx` may resolve ranged transitive dependencies differently. The automated
lifecycle test instead uses the committed full npm lock plus reviewed package
integrity and CLI file hashes before execution.

Replace `codex` with `cursor` or `claude-code`. Do not target all three in one
user profile yet: Cursor intentionally discovers skills from its own, universal,
Claude, and Codex directories, and duplicate-name precedence has not been
qualified.

This is the plan/orient/routing evaluation path until host-native full packages
are published and qualified. A standalone skill install does not copy the
top-level executable blueprints. Update by removing and reinstalling the
reviewed local version from the same backend project; remove with
`npx --yes skills@1.7.0 remove oci-founder -y`. The missing `-a` is
intentional: in `skills@1.7.0`, agent-filtered removal can leave the universal
`.agents` copy used by Codex or Cursor. Because the supported workflow installs
this named skill for only one agent, scope-wide removal of `oci-founder` is the
recommended cleanup command within that project. Global installation remains
an open gate and is not the quickstart default. Do not use `skills update` for
this local source.

For project-only use, run from the target backend, pass an absolute path to the
reviewed toolkit checkout, omit `-g`, and select one agent. The automated
project lifecycle test uses a different disposable repository for each agent,
verifies the exact expected destination, and compares the installed tree with
the reviewed source without touching a global installation target.

## Local validation

Run repository-level checks first:

```bash
python3 scripts/validate.py
python3 scripts/validate_agent_plugin_schema.py
python3 scripts/scan_release_sources.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/build_release.py check
python3 scripts/qualify_hosts.py --run-validators
python3 scripts/qualify_skill_install.py --allow-download
python3 -B -m unittest tests.test_probe_codex_native -v
```

The skill-install qualification command uses the committed dependency lock,
`npm ci --ignore-scripts`, an environment allowlist, and reviewed CLI file
hashes. The latest evidence was renewed from a copied verified npm cache with
`npm ci --offline`, while the lock and package-integrity checks remained
enabled. The native-runner unit command checks the hardened
runner without downloading or starting a model session; all 12 contracts pass
in the current assessment.

For an already-present Oracle Skills checkout, the separate verifier is offline
and read-only:

```bash
python3 scripts/verify_oracle_skills_lock.py \
  --checkout /absolute/path/to/oracle-skills-reviewed
```

It checks the locked commit, trees, clean worktree, and `LICENSE.txt`. No real
checkout-bound run has been completed in this workspace.

When the relevant host CLI is installed, also run its native validator. Claude Code documents:

```bash
claude plugin validate . --strict
```

The root manifest is validated locally against the reviewed Agent Plugins
`1.0.0` schema snapshot and the same check is configured in the CI workflow; no
remote CI run is claimed. The Codex compatibility manifest and skill
also pass their installed development validators when the reviewed PyYAML
runtime is provided; the exact dependency procedure is in
[`RELEASING.md`](RELEASING.md). The read-only preflight records the exact
surfaces present without installing anything; see
[`HOST-QUALIFICATION.md`](HOST-QUALIFICATION.md). Cursor native runtime and
Claude strict validation remain release gates rather than completed claims.
The renewed host-preflight receipt passes source validation in the explicit
cycle-breaking mode at the current skill fingerprint and records
`release_qualified: false`.
The historical Codex receipt and its normalized assessment are linked from
[`VALIDATION.md`](VALIDATION.md); a fresh hardened native rerun is `BLOCKED`
before model execution only because a new authenticated model session and
external model egress were not authorized. The runner accepts a verified
offline npm cache for reviewed installer acquisition. No model session or cloud
mutation occurred in that renewal. The targeted current-skill assessment is
also linked from [`VALIDATION.md`](VALIDATION.md), but it does not replace
native discovery or replay.

## Portability constraints

- Shared skill frontmatter uses the common Agent Skills subset only.
- Skills are immediate children of `skills/`; do not depend on recursive discovery.
- Do not depend on Claude-only hooks, command interpolation, subagents, or frontmatter in the core.
- Do not depend on Cursor-only rules, variables, or MCP path substitutions in the core.
- Do not depend on Codex-only UI metadata for workflow correctness.
- MCP credential and path behavior is not fully portable; future MCP adapters require separate tests.
- User-home skills may not appear in remote/cloud agent environments. Prefer plugin or repository distribution.
- A standalone copied skill must not require a relative file outside its own
  directory. The Container API adapter detects the full package and fails
  closed when the blueprint is absent.

## Official references

- [Codex skills](https://developers.openai.com/docs/build-skills)
- [Codex plugins](https://developers.openai.com/plugins/build/plugins)
- [Claude Code plugins reference](https://code.claude.com/docs/en/plugins-reference)
- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [Cursor plugins reference](https://cursor.com/docs/reference/plugins)
- [Cursor Agent Skills](https://cursor.com/docs/skills)
- [Agent Skills specification](https://agentskills.io/specification)
- [Agent Plugins specification](https://agent-plugins.org/specification)
