# Agent compatibility

Founder Toolkit for OCI keeps one skill implementation and multiple thin
manifests. It is an independent personal project by Daniel Gandolfi with
best-effort community support and no Oracle or project support SLA.

## Packaging matrix

| Host | Package mechanism | Included artifact | Validation status |
|---|---|---|---|
| Codex CLI | Codex compatibility manifest and portable skill | `.codex-plugin/plugin.json` | CLI `0.153.4`; the current source and public-preview packages passed project-scoped lifecycle; the current host preflight passed repository, plugin, and skill validation; the current targeted three-case assessment passed but was non-native; the historical native receipt remains normalized to Q2 `PASS_WITH_RESERVATIONS` and Q3 `PARTIAL`, and formal Q2/Q3 remain `BLOCKED` |
| Cursor IDE / Agent | Agent Plugins v1 and portable skill | `plugin.json` | IDE `3.0.12` was detected; the current source and public-preview packages passed project-scoped lifecycle, but Cursor Agent is unavailable; duplicate discovery and native runtime validation remain unqualified |
| Claude Code | Claude plugin manifest and portable skill | `.claude-plugin/plugin.json` | The current source and public-preview packages passed project-scoped lifecycle, but Claude Code is unavailable on the dated host; strict validation and native runtime discovery remain unqualified |

All three adapters point to `skills/oci-founder/SKILL.md`. This table describes
packaging intent, not a production-support claim. See [`VALIDATION.md`](VALIDATION.md)
for exact evidence and open gates. Public source use is authorized by UPL-1.0;
a tagged, cross-host-qualified stable release remains `BLOCKED`.

The public source preview on `main` at
[`danielgandolfi1984/oracle_founder_pack`](https://github.com/danielgandolfi1984/oracle_founder_pack)
is licensed under UPL-1.0 and may be cloned, installed, modified, and
redistributed subject to that license. It is not a qualified immutable install
coordinate for a stable release: `v0.1.0` is the GitHub public-preview tag and
prerelease, while no marketplace or registry coordinate is claimed. It is not
an Oracle product and carries no Oracle or project support SLA.

The current source, skill-only archive, and full-toolkit archive passed
project-scoped install/list/remove/reinstall in separate Codex, Cursor, and
Claude Code layouts. The current skill tree SHA-256 is
`c9ca7081b818f85a248836a53d12b94b6c995da9825696346a1075bf42c2dd37`.
The current skill-only archive SHA-256 is
`517c4f6d4d29b35d085d4cf534656608e6c1d7315526563ee632ee5ae9fe7954`;
the current full-toolkit archive SHA-256 is
`33037edf2783895c03a5e40bb03a0f18468a26945dc7fce8a9e251ea7e75ca80`,
with internal root `oci-founder-toolkit/`. These lifecycle results establish
filesystem-layout and package behavior, not native Cursor Agent or Claude Code
runtime qualification.

For historical comparison, the pre-transition evaluation archives also passed
the same project-scoped lifecycle. Their skill-only SHA-256 was
`1e41859b5ac86522356aa922f177189c3f95a1deaba8dae77d6a95e1cd64ab23`;
their full-toolkit SHA-256 was
`aa332c7555ad88e17f86f99dbd1e33e0f211f48e6e40b980eedb8992c1333790`,
and their skill tree was
`b984f25dc1462c14dc3153eb307f5953d08821970afdd036022eb3d6cbbf653e`.
The historical receipts remain linked from [`VALIDATION.md`](VALIDATION.md).

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
- Claude Code discovers this project skill in `.claude/skills`; invoke it as
  `/oci-founder` or let Claude select it implicitly.
- Cursor discovers Agent Skills; explicitly invoke this one as `/oci-founder`
  for the first smoke test, or allow later selection from its description.

## Public-preview installation

From the target backend, install from an absolute path for the one agent you
intend to use. This project-scoped convenience command pins the top-level Agent
Skills CLI package to the version exercised by the lifecycle test. The selected
host must already be installed and authenticated; this command only copies the
skill files:

```bash
npx --yes skills@1.7.0 add /absolute/path/to/oci-founder-toolkit \
  --skill oci-founder -a codex --copy -y
npx --yes skills@1.7.0 list -a codex --json
```

The command is not a bit-for-bit replay of the formal qualification because
`npx` may resolve ranged transitive dependencies differently. The automated
lifecycle test instead uses the committed full npm lock plus reviewed package
integrity and CLI file hashes before execution.

Replace `codex` with `cursor` or `claude-code`. Do not target all three in one
user profile yet: Cursor intentionally discovers skills from its own, universal,
Claude, and Codex directories, and duplicate-name precedence has not been
qualified.

This is the public-preview plan/orient/routing path until host-native full
packages are published and qualified. A standalone skill install does not copy the
top-level executable blueprints. Update by removing and reinstalling the
reviewed local version from the same backend project; remove with
`npx --yes skills@1.7.0 remove oci-founder -y`. The missing `-a` is
intentional: in `skills@1.7.0`, agent-filtered removal can leave the universal
`.agents` copy used by Codex or Cursor. Because the recommended workflow installs
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
hashes. The current source and public-preview package evidence used a copied
verified npm cache with `npm ci --offline`, while the lock and
package-integrity checks remained enabled, and passed the project-scoped
lifecycle in the Codex, Cursor, and Claude Code layouts. The native-runner unit
command checks the hardened runner without downloading or starting a model
session; all 12 contracts pass in the current assessment.

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
`1.0.0` schema snapshot. The same check passed in the first complete public CI
baseline at `bf5ebb3` in
[run 35355021483](https://github.com/danielgandolfi1984/oracle_founder_pack/actions/runs/35355021483)
and in the updated founder-onboarding baseline at `deb13d8` in
[run 35359228279](https://github.com/danielgandolfi1984/oracle_founder_pack/actions/runs/35359228279).
The Codex compatibility manifest and skill
also pass their installed development validators when the reviewed PyYAML
runtime is provided; the exact dependency procedure is in
[`RELEASING.md`](RELEASING.md). The read-only preflight records the exact
surfaces present without installing anything; see
[`HOST-QUALIFICATION.md`](HOST-QUALIFICATION.md). Cursor native runtime and
Claude strict validation remain stable-release gates rather than completed
claims. The current host-preflight receipt passed repository, plugin, and skill
validation against skill tree
`c9ca7081b818f85a248836a53d12b94b6c995da9825696346a1075bf42c2dd37`.
The historical Codex receipt and its normalized assessment are linked from
[`VALIDATION.md`](VALIDATION.md); a fresh hardened native rerun is `BLOCKED`
before model execution only because a new authenticated model session and
external model egress were not authorized. The runner accepts a verified
offline npm cache for reviewed installer acquisition. No model session or cloud
mutation occurred in that renewal. The current targeted three-case assessment
passed against the same skill tree without file writes, network calls, OCI
commands, or cloud mutations. It is non-native and does not replace native
discovery or replay. Formal Q2/Q3, global-profile lifecycle, native Cursor and
Claude Code qualification, and live OCI validation remain open.

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

- [Codex skills](https://developers.openai.com/codex/skills/)
- [Codex plugins](https://developers.openai.com/plugins/build/plugins)
- [Claude Code plugins reference](https://code.claude.com/docs/en/plugins-reference)
- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [Cursor plugins reference](https://cursor.com/docs/reference/plugins)
- [Cursor Agent Skills](https://cursor.com/docs/skills)
- [Agent Skills specification](https://agentskills.io/specification)
- [Agent Plugins specification](https://agent-plugins.org/specification)
