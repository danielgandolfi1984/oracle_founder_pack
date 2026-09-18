# ADR 0001: Compose `oracle/skills`; do not fork it

- Status: accepted
- Date: 2026-09-17

## Context

The official [`oracle/skills`](https://github.com/oracle/skills) repository already provides source-backed Oracle knowledge across OCI, Database, APEX, GraalVM, and other domains. Its OCI domain includes Functions, OKE, IoT Platform, and Enterprise AI.

The Founder Toolkit needs some of that knowledge, but its differentiated job is a cross-service journey for developers new to OCI.

Copying upstream content would create competing sources, delayed security corrections, ambiguous ownership, and needless review work.

## Decision

The Founder Toolkit will compose and route to `oracle/skills` rather than fork it.

- Reusable facts and service procedures belong upstream.
- Founder journeys, translation, guardrails, blueprints, and agent adapters belong here.
- Releases pin the reviewed upstream commit and selected paths.
- The source repository does not edit vendored upstream files.
- A future self-contained release bundle may include allowlisted upstream files with original license and provenance.

## Consequences

Positive:

- one reusable source of Oracle service truth;
- faster adoption of upstream corrections;
- a smaller and more differentiated toolkit;
- clearer contribution paths for Oracle engineers.

Tradeoffs:

- installation or release packaging must resolve upstream dependencies;
- upstream changes require compatibility review;
- journey evaluations must detect when an upstream change alters behavior.

## Rejected alternatives

### Fork all OCI skills

Rejected because it guarantees drift and divides maintainership.

### Vendor an unpinned snapshot in the source tree

Rejected because provenance and update intent become unclear. Release bundling can materialize an immutable allowlist later.

### Depend on the moving `main` branch

Rejected because a toolkit release would no longer be reproducible and could change safety behavior without review.

## Sources

- https://github.com/oracle/skills
- https://github.com/oracle/skills/blob/main/SKILL_AUTHORING_GUIDE.md
