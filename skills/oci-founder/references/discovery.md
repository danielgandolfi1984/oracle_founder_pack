# Founder discovery and plan contract

Use this reference to inspect an existing backend and create the first OCI proposal. Discovery is read-only.

## Inspect before asking

Look for evidence in the repository before asking the user:

- languages, framework, runtime versions, and package managers;
- Dockerfile, compose files, Procfile, buildpacks, or existing cloud manifests;
- listening ports, health endpoints, startup command, shutdown behavior, and filesystem writes;
- HTTP, WebSocket, streaming, scheduled, queue, and background-worker behavior;
- databases, caches, object/blob storage, queues, email, and third-party APIs;
- environment-variable names and secret references, but never secret values;
- migration commands, seed data, backup assumptions, and connection pooling;
- CI/CD, Terraform, Pulumi, CloudFormation, CDK, Bicep, or Kubernetes files;
- availability, latency, data residency, compliance, and expected traffic clues;
- source-cloud dependencies that have no direct OCI equivalent.

Do not run the application, install dependencies, contact external systems, access credentials, or write generated artifacts merely to complete orientation unless the user requested it and the action is safe. A request for a plan does not authorize repository edits.

## Material questions

Ask only what materially changes the architecture and cannot be inferred safely:

1. Is this a new project, a migration, or a dual-cloud deployment?
2. Which region or data-residency constraints apply?
3. Is the workload public, partner-only, private, or event-driven?
4. What is the smallest acceptable availability target for the current stage?
5. What traffic pattern matters: steady, bursty, scheduled, or unknown?
6. Which stateful dependencies must remain engine-compatible?
7. Is Kubernetes a real requirement or only the team's current packaging method?
8. Is the user asking for a plan, generated IaC, or an approved deployment?

Do not force the user to invent forecasts. Unknown traffic is a valid input and should lead to reversible choices plus observability.

## `founder-plan.md` contract

Start with a short decision snapshot: the provisional recommendation, why it is
the smallest adequate option, the mutation level authorized, and no more than
five unanswered questions that can change the decision. A founder should not
need to read the full plan before learning what to do next.

Return the plan in this order:

### 1. Goal and constraints

State the user goal, stage, source-cloud background, region constraints, runtime, data needs, and mutation authorization.

### 2. Repository evidence

Separate observed facts from assumptions and unknowns. Cite file paths when a recommendation depends on repository evidence.

### 3. Recommended path

Name one primary path and explain why it is the smallest adequate option. Name at most two alternatives and the condition that would make each preferable.

### 4. Architecture

For every OCI service, state:

- its responsibility;
- whether it is public or private;
- the identity it uses;
- the data it stores;
- its main cost driver;
- how it is observed;
- how it is removed or migrated.

### 5. Cross-cloud translation

Map the user's familiar concepts, then call out semantic differences. Never describe an approximate mapping as a drop-in equivalent.

### 6. Founder Baseline

Cover compartment, identity, workload authentication, tags, budget alerts, quotas, Terraform state, secrets, and audit/logging.

### 7. Delivery phases

Use explicit gates:

1. read-only discovery;
2. generated artifacts and local validation;
3. Terraform plan or equivalent preview;
4. user approval;
5. apply/deploy;
6. verification and receipt;
7. rollback or teardown rehearsal.

### 8. Verification

Define an observable success condition: endpoint response, function invocation, log entry, metric, alarm path, and cost attribution.

### 9. Risks and decisions

List service limits, availability assumptions, lock-in points, unknown costs, and decisions that require current documentation checks.

### 10. Sources and skill routing

Link current official Oracle pages and name the exact installed upstream skill to use next, if any.

## Sources

- https://docs.oracle.com/en-us/iaas/Content/GSG/Concepts/concepts-account.htm
- https://docs.oracle.com/en-us/iaas/Content/Identity/compartments/Working_with_Compartments.htm
- https://docs.oracle.com/en-us/iaas/Content/Security/Tasks/securing_your_tenancy.htm
- https://github.com/oracle/skills
