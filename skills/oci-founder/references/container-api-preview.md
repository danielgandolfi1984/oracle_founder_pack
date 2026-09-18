# Container API preview routing

The `oci-founder` skill can be copied and installed without the rest of OCI
Founder Toolkit. That standalone package does **not** contain the executable
Container API blueprint.

Before proposing any blueprint command or accepting a plan, receipt, smoke, or
teardown artifact:

1. Resolve `../../../blueprints/container-api/README.md` relative to this file.
2. Confirm that the file and its sibling `VERSION` exist in the same reviewed
   full-toolkit checkout or installed full plugin.
3. Read that README completely and follow its exact versioned contract.
4. Keep every plan, target, state, receipt, endpoint, and destroy-lineage gate in
   force. The blueprint's presence does not authorize an OCI command or change.

If either file is absent, treat this as a standalone skill installation. State
that the executable preview is unavailable in this package, do not reconstruct
its commands from memory, and continue only with the plan-level Container API
decision contract in `golden-paths.md`. The user can provide a reviewed full
toolkit checkout for a later executable-preview task.

Never fetch a moving branch or silently substitute another copy of the
blueprint to satisfy this check.
