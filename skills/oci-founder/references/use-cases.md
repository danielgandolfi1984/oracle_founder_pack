# Founder and developer use cases

Use this reference to determine what the user is trying to accomplish, what the
smallest useful deliverable is, and what observable result finishes the current
phase. These are journey contracts, not permission to provision OCI resources.

## Choose the request mode first

| User intent | Mode | Smallest useful response |
|---|---|---|
| “Explain this OCI concept” or “what is the OCI equivalent?” | Answer | Direct explanation, semantic differences, evidence status, and one next step |
| “What should this repository use?” | Assess | Read-only repository evidence, one primary recommendation, alternatives only when decision-relevant, and a founder plan if requested |
| “Create the files/configuration” | Generate | Requested local artifacts plus validation results; no OCI mutation |
| “Deploy/change this in OCI” | Execute | Exact target, preview, risks, costs, and a separate approval gate immediately before mutation |
| “Why is this failing?” | Diagnose | Evidence, classification, confidence, and the next confirming check; fixes remain separate |
| “Remove the environment” | Teardown | Exact state/receipt scope, retained-data review, destroy preview, and a separate destructive approval |

If one prompt contains several modes, complete the safe earlier mode and make
the next gate explicit. For example, “design and deploy” authorizes producing a
design and preparing a preview; it does not authorize an unseen `terraform
apply` or broad IAM policy.

## UC1 — Start a first backend on OCI

**Founder says:** “I have an API idea and want to start on OCI, but there is no
repository yet.”

**Do:** Capture the runtime preference, request/event model, state, audience,
region or residency constraint, availability tolerance, and budget sensitivity.
Recommend the smallest reversible runtime path and a stateless first milestone.
Label every architecture input that is still an assumption.

**Done when:** The founder has one provisional path, the few unknowns that can
change it, a first deliverable, and a clear read-only or generate next action.
A repository, tenancy access, or detailed traffic forecast is not required to
finish orientation.

## UC2 — Assess an existing backend

**Developer says:** “Inspect this repo and tell me how to run it on OCI.”

**Do:** Use `discovery.md`. Derive the runtime and workload contract from files,
separate observed facts from assumptions, recommend one primary path, and cite
the repository evidence that drove the choice.

**Done when:** The decision snapshot and, when requested, `founder-plan.md`
identify the path, rejected alternatives, risks, verification, teardown, and
the next authorization gate. No repository or cloud change occurs in Assess
mode.

## UC3 — Translate or migrate from AWS, Google Cloud, or Azure

**Developer says:** “Move my Cloud Run/Fargate/App Runner/Lambda setup to OCI.”

**Do:** Inventory the workload contract before naming a target service. Use
`service-map.md`, mark mappings as close, approximate, or without a direct
equivalent, and identify source-cloud behavior the OCI design must preserve or
intentionally change. Treat data migration as a separate compatibility and
cutover problem.

**Done when:** The user can see what remains the same, what changes, which
requirements block a simple mapping, and whether the next step is a proof of
concept, migration plan, or requirements decision. Do not call a smoke-test
architecture a production migration.

## UC4 — Choose the runtime without defaulting to Kubernetes

**Founder says:** “Should I use Container Instances, Functions, Compute, or
OKE?”

**Do:** Apply `golden-paths.md` to the process model, scaling model, protocol,
duration, state, packaging, availability, and operational capacity. Prefer the
smallest adequate surface. Route real Kubernetes requirements to the installed
OKE skill; familiarity alone is not a Kubernetes requirement.

**Done when:** One runtime is recommended, each rejected option has a concrete
condition that would reverse the decision, and any time-sensitive availability
or limit claim is either verified or marked provisional.

## UC5 — Establish the Founder Baseline

**Founder says:** “Set up the minimum safe OCI foundation for this project.”

**Do:** Propose the project compartment, human and workload identities, tags,
budget alerts, applicable quotas, secret handling, audit/log access, and
Terraform state strategy. Use `guardrails.md`. Distinguish an early-stage
Founder Baseline from an enterprise landing zone.

**Done when:** The proposal identifies ownership, access boundaries, cost
visibility, state protection, and the exact changes requiring approval. A
budget is described as an alert, never as a spending cap.

## UC6 — Generate, deploy, and verify the first workload

**Developer says:** “Create the IaC and get this endpoint running.”

**Do:** Separate Generate from Execute. Generate only the requested artifacts,
validate locally, and summarize the diff. Before any cloud write, identify the
principal/profile, tenancy, region, compartment name and OCID, environment,
exact plan, public exposure, IAM changes, replacements/deletes, and cost
drivers. After separately approved execution, verify the designed endpoint,
telemetry, alarms, tags, budget target, identity, and exposure; then create a
credential-free receipt.

**Done when:** Generate mode ends with validated local artifacts. Execute mode
ends only with a target-bound deployment plus matching verification evidence
and rollback/teardown instructions. An unexecuted plan is not a deployment.

For the repository Container API sandbox, first follow
`container-api-preview.md`. For Functions, route deployment and troubleshooting
to the installed official Functions skills.

## UC7 — Add data, storage, or AI capability

**Founder says:** “Now I need PostgreSQL/MySQL/Oracle, object storage, vector
search, RAG, or an agent.”

**Do:** Preserve the application's engine, extensions, driver, query, data,
latency, backup, recovery, migration, and network requirements before choosing
a service. Do not select a database merely because it carries the Oracle name.
Route Oracle Database implementation to the installed `db` skill and OCI
Generative AI or governed agent workflows to the installed `enterprise-ai`
skill. Use current official documentation for uncovered services.

**Done when:** Compatibility, connectivity, migration, backup/restore, identity,
cost drivers, and rollback are explicit, and the selected service is justified
by workload requirements rather than product branding.

## UC8 — Understand and control cost

**Founder says:** “What will this cost, and how do I prevent a surprise bill?”

**Do:** Explain directional cost drivers first. Verify current prices,
promotions, region availability, and units before calculating a current
estimate. Cover ownership tags, budget alerts, log retention, idle resources,
image/backups, egress, and quotas where supported. Never promise that a budget
or Free Tier label caps spend.

**Done when:** The founder has an assumption-based estimate or a clearly stated
reason one cannot yet be calculated, the variables that change it, alerting and
attribution steps, and any enforceable limit that has been verified for the
target service.

## UC9 — Diagnose an unhealthy workload

**Developer says:** “The endpoint, deploy, image pull, database connection, or
function invocation is failing.”

**Do:** Start with read-only work requests, resource state, logs, metrics,
events, limits, configuration, and recent changes. Separate observations,
hypotheses, and next checks. Route OKE, Functions, Enterprise AI, and Oracle
Database incidents to the corresponding installed official skills.

**Done when:** The failure is classified to the narrowest evidence-supported
layer and the next confirming check is clear. Diagnosis does not itself
authorize a configuration change or remediation.

## UC10 — Tear down safely

**Founder says:** “Delete the environment so it stops costing money.”

**Do:** Resolve the exact Terraform state and deployment receipt, preview the
destroy graph, review persistent data and retained resources, and require a
separate destructive approval. Never select targets only by compartment, name
prefix, wildcard, tag query, or unresolved variable.

**Done when:** Exact managed resources are absent, intentionally retained
resources are listed with cost drivers, persistent data disposition is
recorded, and no unexpected billable resource remains within the verified
scope.

## UC11 — Graduate beyond the founder baseline

**Founder or first platform hire says:** “We now need production environments,
stronger availability, compliance controls, or a platform for several teams.”

**Do:** Reassess requirements instead of treating graduation as a service
upgrade. Consider stronger environment isolation, CI/CD controls, protected
remote state or a tested Resource Manager path, Core Landing Zone, OKE,
multi-region recovery, centralized security, and policy-as-code only when their
requirements are real.

**Done when:** The trigger for each added operational surface is explicit, the
current preview or baseline is not misrepresented as production-certified, and
the migration can be phased with rollback and ownership.

## Response quality bar

Across all use cases:

1. Put the recommendation or finding before the service glossary.
2. Separate observed, user-provided, verified-current, and assumed inputs.
3. Give one primary next action and name its authorization level.
4. Prefer one justified path over a catalog of OCI services.
5. Route reusable service procedures to reviewed `oracle/skills` when present.
6. Say what is unverified; never fill a documentation or target-evidence gap by inference.
