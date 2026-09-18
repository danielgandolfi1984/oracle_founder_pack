# Behavioral prompt cases

`smoke.jsonl` contains host-neutral requests used to evaluate discovery, routing, translation, and safety behavior.

`progressive-disclosure.jsonl` adds a focused recommendation and an explicitly
requested full plan for the 0.1.1 development revision. These two content-forward
tests complement, but do not replace or qualify, the 24-case native host matrix.
Evaluation uses meaning, necessary safety information, reference selection, and
response scope; the skill's approximate length guidance is not a rigid limit.

Each case has:

- `id`: stable case identifier;
- `selection`: `implicit` or explicit `$oci-founder` invocation;
- `mode`: answer, assess, generate, execute, diagnose, or teardown;
- `journey`: orient, bootstrap, ship, verify, operate, teardown, or graduate;
- `expected_route`: the skill that should retain or receive the task;
- `mutation_ceiling`: the maximum permitted effect during replay;
- `prompt`: representative user request;
- `assertions`: observable outcome requirements, not exact wording.

Run the same cases in a fresh Codex, Cursor, and Claude Code session with the plugin installed. Evaluate meaning rather than snapshotting prose.

At minimum, releases must test:

- implicit and explicit skill selection;
- a safe read-only founder plan;
- a cross-cloud non-equivalence;
- routing into an official upstream Oracle skill;
- refusal to mutate without a preview and explicit approval;
- precise destructive-operation scoping;
- sandbox-preview versus production boundaries;
- saved-plan, bootstrap-receipt, and smoke-endpoint lineage;
- ordered runtime-before-bootstrap teardown;
- a nearby out-of-scope request that should route elsewhere.

The replay suite is intentionally non-mutating. A case with `mode: execute` or
`mode: teardown` tests the approval boundary; it does not grant a live OCI
write or destructive action. Fixtures under `tests/fixtures/` contain no
credentials and must be copied into an isolated workspace for native host
qualification.
