# Host qualification

This playbook separates package structure, host discovery, installation,
behavior, and OCI field execution. A local application icon is not evidence
that its coding-agent CLI, plugin loader, or skill runtime is available.

The host preflight is intentionally read-only. It inventories installed
surfaces, fingerprints the exact toolkit source, runs repository checks, and can
run validators that are already installed. A separate opt-in lifecycle runner
uses only disposable projects and never performs a global install. Neither of
those two runners installs a host, starts a model session, invokes an OCI CLI,
or mutates cloud resources. The native Codex runner is separate, explicit
opt-in evidence: it can acquire the reviewed installer artifacts through an
authorized download or a supplied verified offline npm cache, then start one
ephemeral model session in a read-only sandbox only when model execution is
authorized.

## Surfaces

| Product family | Qualifiable surface | Separate surface that is not a substitute |
|---|---|---|
| Codex | Codex CLI and its plugin runtime | ChatGPT/Codex desktop bundle presence alone |
| Cursor | Cursor IDE plugin runtime; Cursor Agent for automated replay | Editor CLI presence alone |
| Claude | Claude Code CLI and plugin runtime | Claude Desktop |

Each surface needs its own version and evidence. Do not summarize all of them as
"the app is installed."

## Qualification levels

| Level | Evidence | Automation status |
|---|---|---|
| Q0 — source | Repository checks, manifest and skill fingerprints, unit tests | Implemented locally; CI workflow configured, with no remote run claimed |
| Q1 — native validation | Host-supported strict validator or a documented development validator | Partial; see the dated matrix below |
| Q2 — install and discovery | Isolated install, exact installed-skill hash, visibility, clean removal | Checkout plus the current skill-only and full-toolkit archives pass project lifecycle on all three layouts; the historical Codex receipt normalizes to `PASS_WITH_RESERVATIONS`, a fresh hardened renewal is `BLOCKED` pending an authorized model session, and formal Q2 remains `BLOCKED` |
| Q3 — behavior | All fixtures in fresh sessions, effect log, independent semantic evaluation | The historical Codex receipt normalizes to `PARTIAL`; the fresh renewal started no model session, and formal Q3 remains `BLOCKED` pending the native suite, independent grading, and Cursor/Claude Code replay |
| Q4 — reinstall | Repeatable update/removal with no stale or conflicting copy | Project remove/reinstall passes; global and native-host lifecycle remain open |

Q0 through Q4 qualify the agent package. Authenticated OCI plan/apply,
idempotency, endpoint checks, rollback, and teardown belong to a separate field
validation and require explicit tenancy and mutation authorization.

## Run the read-only preflight

From the toolkit root:

```bash
python3 scripts/qualify_hosts.py
python3 scripts/qualify_hosts.py --run-validators --json
python3 scripts/qualify_hosts.py --run-validators \
  --validator-pythonpath /absolute/path/to/validator-deps \
  --output tests/results/YYYY-MM-DD-host-preflight.json
```

`--run-validators` only uses validators already present on the machine. It does
not download a CLI or validator. `--validator-pythonpath` accepts only an
explicit PyYAML `6.0.2` target directory and records its tree, version, and
requirements hashes; the pinned setup command is in [`RELEASING.md`](RELEASING.md).
The child process still receives an environment allowlist rather than caller
credentials. Existing outputs are not replaced unless `--overwrite` is
explicit, and symlink targets/parents are refused. Use `--require codex`, `--require cursor`, or
`--require claude` when a CI job must fail if that primary surface is absent.
Use `--fail-on-blocked` for a qualification gate rather than an inventory run.
Presence is still not qualification.

The script deliberately never invokes `cursor agent`. The Cursor application
wrapper observed on 2026-09-17 attempts to download `cursor-agent` when it is
missing, so treating that command as a passive help probe would violate this
playbook's read-only boundary.

## Current host matrix — 2026-09-18

| Surface | Observed version | Q0/Q1 evidence | Blocking gate |
|---|---:|---|---|
| Codex CLI | `0.153.4` | CLI and plugin-management surface detected; repository/schema/development validators and current checkout/archive lifecycle pass; the historical native receipt normalizes to Q2 `PASS_WITH_RESERVATIONS` and Q3 `PARTIAL` | Verified offline installer acquisition is available, but the fresh hardened renewal is `BLOCKED` pending authorization for a new authenticated model session; formal Q2/Q3 also require a fully disposable profile, upstream dependencies, current-skill native replay, and independent grading |
| Cursor IDE | `3.0.12` | App and embedded editor CLI detected; isolated project lifecycle passes | Cursor Agent is unavailable; editor CLI exposes no native plugin validator; duplicate discovery and replay remain open |
| Claude Desktop | `1.569.0` | Desktop bundle detected | Desktop is not Claude Code |
| Claude Code | not present | None | Install the CLI deliberately, then run `claude plugin validate . --strict` and the isolated runtime procedure |

The current machine-readable preflight evidence is in
[`tests/results/2026-09-18-host-preflight.json`](../tests/results/2026-09-18-host-preflight.json).
It records no credentials or raw environment variables and redacts the user home
and toolkit paths. The fresh receipt runs source validation in the explicit
cycle-breaking mode, passes at current skill tree
`b984f25dc1462c14dc3153eb307f5953d08821970afdd036022eb3d6cbbf653e`,
and records `release_qualified: false`. It cannot by itself close native gates.

## Q2 — isolated install and discovery

Do not install into a founder's real global profile to generate release
evidence. Use a disposable OS user, runner, VM, or host-supported isolated
profile. Pin every installer and host version. For each host:

1. Start with an empty host profile and a fresh backend fixture.
2. Install the toolkit from the reviewed local checkout or immutable package.
3. Install the reviewed `oracle/skills` checkout recorded in
   `upstream/oracle-skills.lock.json`; do not resolve a moving default branch.
4. Confirm the visible plugin/skill name and version.
5. Hash the skill actually loaded by the host and compare it with the current
   preflight `skill_tree_sha256` and reviewed source fingerprint.
6. Check that no conflicting user, project, or marketplace copy exists.
7. Remove the package and prove that only the disposable profile changed.

An installer that cannot be pinned, a host outside the tested range, a hash
mismatch, or an uninspectable loaded copy is `BLOCKED`, not `PASS`.

### Offline verification of the reviewed Oracle checkout

Given an existing local checkout, verify the source review lock without network
access or mutation:

```bash
python3 scripts/verify_oracle_skills_lock.py \
  --checkout /absolute/path/to/oracle-skills-reviewed
```

The verifier checks that the locked commit exists and is `HEAD`, that the
reviewed tree object IDs and `LICENSE.txt` hash match, and that the worktree is
clean. It reads committed objects rather than working-tree content. This
workspace has not run it against a real `oracle/skills` checkout, so upstream
Q2 dependency verification remains open.

### Current project-lifecycle evidence

The pinned `skills@1.7.0` lifecycle passed in three disposable Git repositories,
one per supported agent:

```bash
python3 scripts/qualify_skill_install.py --allow-download
```

The current run copied a previously verified npm cache into disposable state
and used `npm ci --offline --ignore-scripts`. It still verified the reviewed
dependency lock, package integrity, CLI manifest, and executable hashes before
execution, and passed each child process only an explicit environment
allowlist. It then installs, lists, removes, reinstalls, lists, and removes again
for Codex, Cursor, and Claude Code separately. Every installed tree matched the
reviewed source fingerprint, every removal left only the allowed empty
directories and an empty lock, and the four explicitly observed global skill
targets were unchanged. No claim is made about the rest of the user profile.
The evidence is in
[`tests/results/2026-09-18-skill-install-lifecycle.json`](../tests/results/2026-09-18-skill-install-lifecycle.json).

The same lifecycle passed from both extracted, verified archives. The
skill-only SHA-256 is
`876fe40dbac703b092110f106f6797fa7eaa753c6bb9b711e61e67f61c2fd315`;
the full-toolkit SHA-256 is
`62501591cdc53b2e366dd7fbe39c7c87a47a838ff034ff7ad734040d1f96eaa8`,
and that versioned archive extracts under `oci-founder-toolkit/`. Both renewed
package receipts verify the current skill tree fingerprint
`b984f25dc1462c14dc3153eb307f5953d08821970afdd036022eb3d6cbbf653e`.
Each summary binds the archive, manifest, content inventory, runner, installed
tree, and committed exact raw receipt by SHA-256:
[skill-only summary](../tests/results/2026-09-18-skill-package-install-lifecycle.json),
[skill-only raw receipt](../tests/results/2026-09-18-skill-package-install-lifecycle.raw.json),
[full-toolkit summary](../tests/results/2026-09-18-full-package-install-lifecycle.json),
and [full-toolkit raw receipt](../tests/results/2026-09-18-full-package-install-lifecycle.raw.json).

This is package-lifecycle evidence, not native host discovery. The Codex and
Cursor cases each produced one `.agents/skills/oci-founder` copy; the Claude
Code case produced one `.claude/skills/oci-founder` copy. Cursor documents that
it scans both locations, so duplicate-name behavior must pass a native Cursor
test before a combined multi-agent install can be recommended. For an actual
evaluation, choose one agent per installation command.

### Historical Codex receipt and hardened-runner renewal

Run the automated probe only when one reviewed installer-acquisition mode and
one authenticated model session are authorized. The acquisition may use a
verified offline npm cache instead of network access. Use a new temporary output
path; the runner refuses an existing target unless `--overwrite` is separately
given:

```bash
python3 scripts/probe_codex_native.py \
  --offline-npm-cache /absolute/path/to/reviewed-npm-cache \
  --allow-model-session \
  --output /private/tmp/oci-founder-codex-native-probe.json
```

The runner installs an exact project-scoped copy into a disposable Git fixture,
runs Codex CLI with explicit `$oci-founder`, `--ephemeral`,
`--ignore-user-config`, `--ignore-rules`, `--sandbox read-only`, JSON events,
and a structured output schema, then removes the skill and audits residuals. It
uses an environment allowlist and prepends logging deny shims for `oci`,
`terraform`, `fn`, `docker`, and `kubectl`; it never invokes OCI itself.

The hardened runner's 12 unit contracts currently pass:

```bash
python3 -B -m unittest tests.test_probe_codex_native -v
```

The dated Codex CLI `0.153.4` receipt is historical. It recorded exact
installed/source tree hashes, schema-valid founder guidance, clean removal, no
forbidden effect, and probe Q2/Q3 as `PASS`. The current assessment normalizes
that evidence to Q2 `PASS_WITH_RESERVATIONS` and Q3 `PARTIAL`; the receipt did
not use a fully disposable host profile, install the reviewed `oracle/skills`
dependencies, replay the full behavioral matrix, or run an independent
semantic grader. Both that native receipt and the older 24-case evidence are
bound to former skill tree
`746cc9a3462ce96c067eedd91e848a905f04ed402b8f579836ce126c5b4d703f`.

A fresh run of the hardened runner is `BLOCKED` only because a new authenticated
model session and external model egress were not authorized; the runner now
accepts the verified offline npm cache for reviewed installer acquisition. The
renewal therefore started no model session and attempted no cloud mutation.
Formal Q2 and Q3 remain `BLOCKED`. Cursor Agent and Claude Code are unavailable
on the current host, so their native replay also remains blocked. Historical
receipt:
[`tests/results/2026-09-18-codex-native-runner-probe.json`](../tests/results/2026-09-18-codex-native-runner-probe.json).
Current assessment:
[`tests/results/2026-09-18-codex-native-runner-assessment.json`](../tests/results/2026-09-18-codex-native-runner-assessment.json).

A separate
[`targeted current-skill assessment`](../tests/results/2026-09-18-skill-revision-assessment.json)
passed three Codex-subagent content-forward cases at the current skill
fingerprint. It used no network, file write, OCI command, or cloud mutation, and
is not host-native discovery or behavior evidence; it does not close Q2, Q3, or
the release gate.

## Q3 — behavioral replay

Run every case in `tests/prompts/smoke.jsonl` in a new session. The existing
24-case coverage index and recorded evaluations are historical and bound to the
former skill fingerprint. The index deliberately records zero native-complete,
transcript-bound, or tool-trace-bound cases. It is bookkeeping, not a substitute
for a current-skill native replay. Assertions are
grader inputs and must not be shown to the host under test. Every result must
identify:

- host surface and exact version;
- toolkit source fingerprint and installed skill fingerprint;
- prompt ID and prompt hash;
- fixture ID and fixture hash;
- transcript hash and any redactions;
- filesystem changes and attempted tool calls;
- machine assertions and independent semantic verdict;
- `PASS`, `FAIL`, `BLOCKED`, or `SKIP` with a reason.

Use sanitized, versioned fixtures for repository, saved-plan, receipt, and
teardown cases. Remove OCI, AWS, Google Cloud, and Azure credentials from the
runner. In a dedicated test runner, replace `oci`, `terraform`, `fn`, `docker`,
and `kubectl` with logging deny shims so an unexpected tool call fails closed.
The host needs only the network access required for its model endpoint.

`SKIP` is useful during development but cannot satisfy a release gate. A
generative answer need not match exact wording; it must satisfy the observable
safety, routing, and architecture assertions.

## Q4 — reinstall and lifecycle

Repeat install, discovery, update, and removal against the same isolated
profile. For a reviewed local checkout, update means remove plus reinstall;
`skills update` is not qualified for this source type. With `skills@1.7.0`,
omit `-a` from the remove command: the agent-filtered form can report success
while leaving the universal `.agents` copy used by Codex or Cursor. The second
install must load the new reviewed fingerprint, leave no stale skill, and preserve no
unexpected configuration. Record both filesystem trees and all host commands as
argv arrays. The current project test leaves only empty skill directories and an
empty `skills-lock.json`; native global-profile behavior remains open.

## Release rule

Do not claim cross-host support until every named surface passes Q0 through Q4
without skipped gates. A manual GUI result may be retained as supporting
evidence, but it must not be presented as deterministic CLI qualification.
The public `main` source preview is cloneable, but it is not qualified
public-install evidence: there is no immutable tag, GitHub release, marketplace
entry, registry coordinate, or package coordinate, and no successful remote CI
or remote-source lifecycle run is claimed by this dated record.

## Official host references

- [Build skills for ChatGPT and Codex](https://developers.openai.com/pt-BR/docs/build-skills)
- [Codex non-interactive mode](https://developers.openai.com/pt-BR/docs/non-interactive-mode)
- [Build plugins for ChatGPT and Codex](https://learn.chatgpt.com/pt-BR/docs/build-plugins)
- [Cursor plugins reference](https://cursor.com/docs/reference/plugins)
- [Claude Code plugins reference](https://code.claude.com/docs/en/plugins-reference)
- [Agent Plugins specification](https://agent-plugins.org/specification)
