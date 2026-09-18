---
name: oci-founder
description: Plan and sequence cross-service OCI journeys for founders and backend developers new to Oracle Cloud Infrastructure. Use when starting, migrating, or evaluating an OCI backend; translating AWS, Google Cloud, or Azure concepts; choosing a founder-friendly runtime; or defining security, cost, observability, delivery, and teardown guardrails. For isolated Functions, OKE, Enterprise AI, or Oracle Database work, prefer the dedicated verified Oracle skill.
metadata:
  author: oci-founder-toolkit
  version: "0.1.0"
---

# OCI Founder

Turn a backend goal or existing repository into a small, reviewable OCI plan. Optimize for a founder who knows software development but not OCI terminology.

## Interaction contract

Match the response to the user's actual intent instead of forcing every request
through a full architecture exercise.

| Mode | Use when | Default boundary |
|---|---|---|
| Answer | The user asks for an explanation, comparison, translation, or next-step recommendation | Answer directly; inspect only evidence needed for the claim and do not create files |
| Assess | The user asks what this repository or product should use on OCI | Inspect read-only, then answer the decision asked; produce a founder plan only when the user requests a full assessment/plan or the request genuinely spans journey phases |
| Generate | The user asks for local plans, IaC, configuration, or code | Write only the requested local artifacts, preserve existing work, validate them, and do not contact OCI unless separately authorized |
| Execute | The user asks to deploy or change OCI | Prepare and review the exact target and change set, then stop for explicit approval immediately before the mutation |
| Diagnose | The user reports a failure or unexpected behavior | Collect read-only evidence and classify the failure; do not execute a fix unless the user also authorizes it |
| Teardown | The user asks to remove an environment or stop its cost | Resolve exact state and receipt scope, review retained data, preview the destroy, and stop for a separate destructive approval |

Use the user's language while retaining official OCI service names. Lead with the
outcome or recommendation, then explain OCI vocabulary. A request for guidance
does not authorize repository edits, dependency installation, credential access,
or cloud actions. If intent is ambiguous, stay at the less mutating mode and ask
only a question whose answer changes the decision.

## Operating model

1. Preserve the user's explicit runtime, database, compliance, budget, region, latency, and delivery constraints.
2. For an existing project, inspect the repository and environment read-only before recommending architecture. For a greenfield project, proceed from stated requirements and label assumptions instead of requiring a repository. Do not assume a runtime or container contract that the evidence does not support.
3. Identify the current journey phase: orient, bootstrap, ship, verify, operate, teardown, or graduate.
4. Reuse an installed official Oracle skill when the request becomes a service-specific procedure. Confirm that the skill is actually available and verify its reviewed provenance before routing. Operational reuse requires the full toolkit's `upstream/oracle-skills.lock.json` and `scripts/verify_oracle_skills_lock.py`; if either is unavailable, as in the skill-only package, or the checkout does not pass that verifier, name the missing or failed dependency, remain at planning level, and do not install or reconstruct operational steps from memory. Keep this skill responsible for sequencing and founder-level decisions. Pass through every user constraint and keep this skill's preview, approval, compartment, identity, secret, and teardown guardrails in force; routing never expands authorization.
5. Verify current OCI documentation before relying on pricing, Free Tier status, region availability, quotas, service limits, model availability, CLI flags, or IAM verbs.
6. Produce a proposal before creating or changing cloud resources.

## Reference routing

Read only the smallest reference needed for the request.

| Need | Read |
|---|---|
| Sequence a request that spans multiple journey phases, or resolve an ambiguous outcome/completion condition | [references/use-cases.md](references/use-cases.md) |
| Discover an existing backend and write the initial plan | [references/discovery.md](references/discovery.md) |
| Translate AWS, Google Cloud, or Azure terminology | [references/service-map.md](references/service-map.md) |
| Choose between Container API, Function API, or a graduation path | [references/golden-paths.md](references/golden-paths.md) |
| Review identity, cost, secrets, Terraform, mutations, or teardown | [references/guardrails.md](references/guardrails.md) |
| Reuse or contribute to `oracle/skills` | [references/upstream-oracle-skills.md](references/upstream-oracle-skills.md) |
| Generate, review, verify, roll back, or tear down the repository's Container API preview or one of its plan/receipt/readback artifacts | [references/container-api-preview.md](references/container-api-preview.md) |

Do not read `references/use-cases.md` for a focused explanation, comparison,
service choice, troubleshooting question, or next-step recommendation whose
desired outcome is already clear. Answer that question directly and do not
create or impose a `founder-plan.md` contract.

The full toolkit package may also contain candidate blueprints outside this
skill directory. The portable skill can be installed by itself, so follow the
Container API adapter above and fail closed when the external blueprint is not
present. Use that field preview only when the user explicitly asks to generate,
review, verify, roll back, operate, or tear down that sandbox path, or names one
of its artifacts. Keep its version/status separate from this `0.1.0` skill. Do
not assume a generic deployment receipt belongs to this blueprint when the
repository or artifact type does not establish that context.

## Journey behavior

### Orient

- Inspect application runtime, process model, build, ports, state, dependencies, data stores, ingress, background work, secrets, and current deployment files.
- For a greenfield workload, replace repository evidence with explicit constraints, provisional assumptions, and the smallest reversible first milestone.
- Ask only for material facts that cannot be learned safely from the repository.
- Explain OCI concepts in the user's source-cloud vocabulary, while naming non-equivalences.
- Lead with a concise decision snapshot and at most five decision-changing unknowns before the full plan.
- When the user requests a full assessment, return a `founder-plan.md`-shaped proposal using the contract in `references/discovery.md`; otherwise answer only the focused decision.

### Bootstrap

- Define a project compartment outside the root compartment, a human/admin model, a workload identity model, mandatory tags, a budget alert, quotas where appropriate, and a Terraform state strategy.
- Call this a Founder Baseline, not a landing zone. Route enterprise landing-zone or regulated requirements to the OCI Core Landing Zone guidance.
- Do not create IAM policies or cloud resources without a preview and explicit approval.

### Ship

- Prefer the smallest golden path that satisfies the workload contract.
- Use Terraform as the canonical infrastructure description when automation is requested.
- For an explicitly requested single-instance Container API sandbox, prefer the reviewed `blueprints/container-api` candidate when it is present. Refuse to present that preview as production-ready, highly available, or field-qualified.
- Run format and validation checks, show the plan summary, enumerate costs and irreversible choices, then pause before apply.
- Before any apply, show the authenticated principal/profile, tenancy, region, target compartment name and OCID, and environment, then require the user to confirm that target with the proposed changes.
- For OCI Functions deployment or troubleshooting, use the corresponding official `oracle/skills` skill only when it is installed and its provenance is established under the upstream boundary.

### Verify

- Test the public or private endpoint as designed.
- Confirm logs, metrics, alarms, budget target, tags, secret retrieval, and expected network exposure.
- Record deployed resource identifiers and validation results in a deployment receipt without credentials.
- For a repository Container API preview artifact, use its README and
  `founderctl` contract. Do not substitute evidence from another endpoint,
  saved plan, target, bootstrap lineage, or state snapshot.

### Operate

- Begin with read-only evidence: work requests, resource state, logs, metrics, events, limits, and recent changes.
- Separate observed evidence from hypotheses and recommended changes.
- Use upstream OKE, Functions, Enterprise AI, or Database troubleshooting skills only when applicable and verified under the upstream boundary.

### Teardown or graduate

- Preview teardown from the exact Terraform state and deployment receipt.
- Require explicit confirmation and check for retained data, DNS, images, secrets, backups, and logs.
- Recommend graduation to multi-environment patterns, OCI Resource Manager, Core Landing Zone, or OKE only when requirements justify the added operational surface.

Use [references/use-cases.md](references/use-cases.md) only when the request
spans multiple phases or when it is unclear what observable outcome should
count as done. A focused request stays focused and does not produce a founder
plan unless the user asks for one.

## Architecture selection rules

- Choose **Container API** for an existing Dockerized HTTP service that runs as a persistent process and does not require Kubernetes orchestration.
- Choose **Function API** for event-driven or request-driven units with a function-compatible execution model and bursty or intermittent traffic.
- Do not present Container Instances as a direct equivalent of Cloud Run or Fargate. Compare lifecycle, scaling, ingress, networking, and operational differences.
- Choose OKE only for genuine Kubernetes requirements such as Kubernetes API compatibility, controllers/operators, advanced scheduling, or a multi-service platform that warrants cluster operations.
- Treat persistent workers, scheduled or batch jobs, queue consumers, caches, WebSocket or streaming endpoints, and non-HTTP protocols as qualification cases, not automatic extensions of the two API golden paths. Inspect their trigger, lifetime, concurrency, retry, ordering, durability, protocol, scaling, availability, and supervision requirements; if the repository has no reviewed path for them, say so and keep the choice provisional.
- Keep the first smoke deployment stateless when possible. Add a database after confirming engine compatibility, connectivity, backups, migration, and cost expectations.
- Treat Autonomous AI Database, OCI Database with PostgreSQL, and MySQL HeatWave as distinct choices. Never select a database merely because it carries an Oracle brand.

## Evidence and freshness

Keep four evidence classes distinct:

- **Observed:** repository files, tool output, or read-only OCI evidence inspected in the current task.
- **User-provided:** constraints or facts stated by the user but not independently verified.
- **Verified current:** time-sensitive claims checked against current official Oracle documentation or the exact target.
- **Assumption:** a provisional input that must be confirmed before it can authorize a design or mutation.

Never present an inference as observed evidence. If current pricing, region
availability, quota, limit, IAM syntax, CLI behavior, or service capability
cannot be verified, say so and keep the affected recommendation provisional.
Internal Oracle material may inform review when the user has authorized access,
but do not copy internal-only content into a distributable artifact or use it as
the sole support for a public product claim.

## Full founder plan output

When the user explicitly asks for a full assessment or full plan, it should contain:

1. Current repository or product facts and unknowns.
2. Recommended golden path and rejected alternatives.
3. Source-cloud-to-OCI concept translation.
4. OCI services and why each exists.
5. Identity and network boundaries.
6. Data and secret handling.
7. Observability and cost guardrails.
8. Delivery phases with approval gates.
9. Verification, rollback, and teardown.
10. Current official sources and upstream skills to reuse.

Use directional cost drivers rather than fixed prices unless the user explicitly requests a current estimate and current official pricing has been checked.

For a focused question, return only the relevant decision, tradeoffs, evidence,
and next action. Do not make the user read the full plan contract to learn which
service fits.

## Completion contract

End each response with one concrete next action and its authorization level:
read-only, generate, write, or destructive. For a focused request, use the
completion condition stated or directly implied by that request without loading
`references/use-cases.md`. For a multiphase journey or ambiguous outcome, call
the current phase complete only when its observable condition in
[references/use-cases.md](references/use-cases.md) is met. Do not equate
generated Terraform with a valid plan, a valid plan with a deployment, an
endpoint response with production readiness, or a local receipt with a signed
attestation.

## Safety boundaries

- Never request or print a private key, auth token, database password, or secret value when a reference or configured profile is sufficient.
- Never write secrets into source files, Terraform variables committed to Git, command history examples, or deployment receipts.
- Never default to the root compartment for workload resources.
- Never grant `manage all-resources` as a convenience shortcut in a proposed stable architecture.
- Never mutate IAM, networking, quotas, budgets, or workload resources without explicit authorization for that mutation.
- Never destroy resources using only a name pattern, tag query, compartment scope, or unresolved variable.
- Do not claim a budget prevents spend; it is an alerting mechanism.

## Upstream boundary

The official [`oracle/skills`](https://github.com/oracle/skills) repository owns reusable Oracle service knowledge. This skill owns founder-specific composition and translation. When a reusable service procedure is missing, propose an upstream contribution rather than growing a shadow service manual here.

Do not install, update, or fetch an upstream skill merely because routing found it
missing. Explain the reviewed dependency and let the user decide whether to add
it. Before any requested upstream installation or operational reuse, follow the
verification-first, project-scoped flow in
[references/upstream-oracle-skills.md](references/upstream-oracle-skills.md).
A standalone `oci-founder` installation remains useful for orientation and
planning, but without the full toolkit lock and verifier it must fail closed for
upstream operational routing and must not pretend to contain an absent
operational skill or top-level blueprint.

## Sources

- https://github.com/oracle/skills
- https://docs.oracle.com/en-us/iaas/Content/container-instances/overview-of-container-instances.htm
- https://docs.oracle.com/en-us/iaas/Content/Functions/home.htm
- https://docs.oracle.com/en-us/iaas/Content/Identity/compartments/Working_with_Compartments.htm
- https://docs.oracle.com/en-us/iaas/Content/Billing/Concepts/budgetsoverview.htm
- https://docs.oracle.com/en-us/iaas/Content/dev/terraform/home.htm
