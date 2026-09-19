# Founder Toolkit for OCI: founder and developer recipes

Founder Toolkit for OCI is a personal, independent public-preview project
created and maintained by Daniel Gandolfi, an Oracle employee publishing in his
personal capacity. The views expressed here are his own and do not represent
Oracle. This is not an Oracle product and is not sponsored, endorsed,
maintained, or supported by Oracle.

The project's original public content is licensed under the Universal
Permissive License 1.0 (`UPL-1.0`); see [`LICENSE`](../LICENSE). The internal
Oracle-template presentation remains confidential, is excluded from the public
repository and every public distribution, and is outside this license grant.

Use these recipes after installing the `oci-founder` skill. Open your backend
repository when you want to evaluate an existing application; the foundational
recipes also work before you have an application. They are written for
founders and developers who want a concrete first step on OCI, including those
coming from AWS, Google Cloud, or Azure.

The prompts below are content-portable: paste the same prompt into Codex,
Cursor, or Claude Code after selecting the skill through that host's normal
interface. This does not claim that every host has completed native runtime
qualification; see [COMPATIBILITY.md](COMPATIBILITY.md) for the current evidence.

The standalone `oci-founder` v0.1.1 skill can explain, plan, and review. It does
not supply account access or a verified operational VM/VCN dependency. Without
the full toolkit's lock, verifier, and verified service dependencies,
operational routing stays at planning level. The new [account setup](ACCOUNT-SETUP.md)
and [first VM](FIRST-VM.md) guides are manual user workflows, not a change to
that execution contract.

Every recipe is safe by default:

- **Answer** and **Assess** explain or inspect without changing the repository
  or OCI.
- **Generate** can create requested local artifacts, but cannot apply them.
- **Diagnose** collects read-only evidence; it does not authorize a fix.
- **Teardown** first resolves exact scope and produces a preview. Deletion is a
  separate **Destructive** action that requires confirmation immediately before
  it runs.

A request to plan, migrate, diagnose, or reduce cost never grants permission to
provision, update, or delete cloud resources. Before relying on prices, limits,
availability, IAM syntax, or service behavior that can change, the agent must
check current official Oracle documentation and identify what remains
unverified.

## Choose by objective

| Your objective | Start with | Starting mode | What finishes this step |
|---|---|---|---|
| Understand what the agent needs from your OCI account | [Prepare account context](#foundation-a-prepare-account-context) | Answer | A safe context checklist and a reviewed local authentication choice |
| Learn VCNs, subnets, and VMs through a small lab | [Review a first VM lab](#foundation-b-review-a-first-vm-lab) | Answer or Assess | A reviewed manual Console plan, validation checks, and explicit cleanup scope |
| Bring an existing FastAPI or Node.js container from Cloud Run, App Runner, or Fargate | [Assess an existing containerized API](#1-assess-an-existing-containerized-api) | Assess | One evidence-backed OCI path, its non-equivalences, and one next action |
| Choose a runtime for a new API | [Choose a greenfield API runtime](#2-choose-a-greenfield-api-runtime) | Answer | One provisional runtime and the few assumptions that could change it |
| Translate Lambda, Cloud Functions, or Azure Functions | [Assess a function migration](#3-assess-a-function-migration) | Assess | A compatibility map and a proof-of-concept or requirements decision |
| Keep PostgreSQL or MySQL semantics intact | [Preserve the existing database engine](#4-preserve-the-existing-database-engine) | Assess | A compatibility and cutover plan that does not force an engine change |
| Understand likely spend and prevent surprises | [Understand and control cost](#5-understand-and-control-cost) | Answer or Assess | Verified inputs, cost drivers, alerts, attribution, and open unknowns |
| Find why an endpoint is unhealthy | [Diagnose an endpoint](#6-diagnose-an-endpoint) | Diagnose | The narrowest evidence-supported failure layer and next confirming check |
| Remove an environment safely | [Prepare and perform a safe teardown](#7-prepare-and-perform-a-safe-teardown) | Teardown | A scoped preview first; after separate approval, verified absence plus retained resources |

In every response, evidence should be labeled as one of:

- **Observed** — a repository file, command result, or read-only OCI result the
  agent inspected during this task;
- **User-provided** — a constraint or fact you supplied but the agent did not
  independently verify;
- **Verified current** — a time-sensitive claim checked against the current
  target or official Oracle documentation;
- **Assumption** — a provisional input that must not silently become a design
  fact or mutation target.

## Foundation A. Prepare account context

**Scenario**

You can sign in to the OCI Console, but do not know which identifiers,
credentials, and permissions a local coding agent would need.

**Prerequisites and guide**

Read [Account setup](ACCOUNT-SETUP.md) for Console locations and the manual CLI
tests. You need an OCI account and an authorized project compartment for those
tests; neither is required just to ask the planning question below. Never
paste private keys, session tokens, auth tokens, passwords, or complete
credential files into the conversation.

**Copyable prompt**

```text
Use the oci-founder skill. Explain how I can prepare OCI account context for
local agent-assisted development. I use [operating system and coding host].
My intended region and project compartment are [known values or unknown].

Explain where the Console shows the tenancy, user, and compartment OCIDs,
and how to choose a region. Compare a temporary CLI session with an API
signing-key profile. Distinguish both from SSH keys and an OCIR auth token.
Explain which non-secret context the agent needs and which values stay local.
Review any redacted test result I supply; do not infer permissions from login
alone. Identify the minimum next check and its authorization level.

Stay in planning and interpretation. Do not install tools, read credential
files, start a login, run OCI commands, change IAM, or create resources.
```

**Expected output and completion**

You understand the profile/authentication method, target tenancy, region,
compartment, and intended operation as separate inputs. Unknown IDs remain
unknown rather than being invented. A valid CLI session establishes
authentication, not permission to create a VM. A successful scoped list test
only demonstrates that particular read, not all required deployment access.
See [CLI sessions](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/clitoken.htm)
and [Keys, OCIDs, and required permissions](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/apisigningkey.htm).

**Authorization level:** **Answer / Read-only interpretation.** The user
performs any login and the guide's explicitly chosen CLI tests separately.

## Foundation B. Review a first VM lab

**Scenario**

You want to understand a small Linux VM and its network before asking an agent
to automate an application deployment. This is a learning lab, not a
production architecture or a reviewed VM deployment skill.

**Prerequisites and guide**

Use [First VM lab](FIRST-VM.md) for the manual Console sequence. Before creating
anything, confirm the exact project compartment, region, permissions, allowed
public exposure, image/shape compatibility, and costs. If your account requires
private networking, stop and review that access design instead of bypassing it.

**Copyable prompt**

```text
Use the oci-founder skill. Review my plan for a first OCI Linux VM lab that I
will create manually in the Console. My non-secret choices are: [region,
project compartment, candidate image/shape, network ranges, and SSH source].

Explain the role of the VCN, subnet, VNIC, Internet Gateway, route table,
security list, NSG, public IP, SSH key, and boot volume. Check CIDR overlap,
image/shape architecture, and the full SSH path. Do not assume a narrow NSG
rule cancels a broader security-list allowance. Keep SSH limited to my
approved source; do not add public application ports without a requirement.

Return the review gaps, manual validation and monitoring checks, a rollback
plan, and an exact-resource cleanup checklist that calls out retained disks
and backups. Verify consequential behavior using official Oracle sources.
Do not promise free capacity or zero cost after Stop. Stay in planning and
review: do not access credentials, run commands, create files, or change OCI.
```

**Expected output and completion**

- A reviewable network/VM plan, with assumptions and cost drivers labeled.
- A validation checklist for the exact VM: lifecycle state, expected address,
  narrowly scoped SSH access, and basic instance metrics. An SSH login does
  not qualify application health or production readiness.
- A manual lab inventory of exact OCIDs and dependencies, plus rollback and
  explicit data-retention decisions before termination. Do not substitute
  this manual inventory for Terraform state or invoke a broad compartment
  teardown. Stopping the VM is not proof that all billing has stopped.

Sources: [Creating an instance](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/launchinginstance.htm),
[Security rules](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/securityrules.htm),
[Linux SSH access](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/connect-to-linux-instance.htm),
and [Billing for stopped instances](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/resource-billing-stopped-instances.htm).

**Authorization level:** **Answer or Assess / Read-only interpretation.** This
step finishes when the plan is reviewable, not when a VM is claimed to exist.
Any manual creation or termination is a separate user decision in the Console.

## 1. Assess an existing containerized API

**Scenario**

You have a FastAPI or Node.js HTTP service on Cloud Run, AWS App Runner, or an
ECS/Fargate task. You want to understand the smallest OCI path without treating
OCI Container Instances as a drop-in equivalent.

**Prerequisites and evidence to provide**

- Open the application repository in your coding agent.
- If available, point it to the `Dockerfile`, deployment manifest, health-check
  route, and source-cloud configuration.
- State the source service and any hard requirements for scale-to-zero,
  autoscaling, concurrency, request timeout, streaming or WebSockets,
  background work, revision traffic splitting, availability, and public or
  private ingress.
- Do not paste credentials, secret values, or production data.

**Copyable prompt**

```text
Use the oci-founder skill. Assess this FastAPI or Node.js backend for an OCI
migration from [Cloud Run | AWS App Runner | ECS/Fargate]. Inspect the
repository read-only. Cite the files you inspect and separate Observed,
User-provided, Verified current, and Assumption evidence.

Inventory the process model, startup command, port, health endpoint, state,
filesystem writes, background work, protocol, deployment configuration,
identity, secrets, database dependencies, and current scaling behavior. For
Cloud Run also check minimum/maximum instances, concurrency, CPU allocation,
request timeout, scale-to-zero dependence, streaming or WebSockets, and
revision traffic behavior. Preserve equivalent App Runner or Fargate
requirements when those are the source.

Recommend one smallest adequate OCI path. Mark each source-to-OCI mapping as
close, approximate, or without a direct equivalent, and explain what would
make the recommendation unsafe. Do not create files, install dependencies,
access credentials, run the application, or change OCI. End with one concrete
next action and its authorization level.
```

**Evidence the agent should inspect**

- Runtime and dependency manifests, `Dockerfile`, entry point, exposed port,
  health route, shutdown behavior, and filesystem usage.
- Source-cloud manifests, environment-variable *names*, IAM or service-account
  references, networking, traffic controls, and scaling settings.
- Database, cache, queue, object storage, scheduled work, and outbound network
  dependencies.
- Any availability, traffic, latency, residency, or compliance requirement
  that you supplied.

**Expected output**

- A concise decision snapshot with one primary OCI path.
- A workload contract based on cited repository evidence.
- A mapping that calls out lifecycle, scaling, ingress, networking,
  replacement, availability, and billing differences.
- At most two alternatives, each with the concrete condition that would make it
  preferable.
- A proof-of-concept, requirements decision, or generate step as the next
  action—not a claim that a smoke-test architecture is a production migration.

**Authorization level**

**Assess / Read-only.** Repository edits, dependency installation, credential
access, OCI API calls, and cloud mutations are not authorized.

**Done when**

You can see what stays the same, what changes, what blocks a simple mapping,
and which evidence or decision is needed next. An untested service suggestion
or a generated Terraform file is not a migration.

## 2. Choose a greenfield API runtime

**Scenario**

You have an API idea but no repository yet. You need a reversible OCI starting
point without defaulting to Kubernetes or inventing a traffic forecast.

**Prerequisites and evidence to provide**

- State your preferred language or runtime, if any.
- Describe whether the workload is HTTP, event-driven, scheduled, streaming,
  or a persistent worker; who can reach it; and whether it stores state.
- Share known region or residency constraints, availability tolerance, traffic
  pattern, budget sensitivity, and operational capacity. `Unknown` is a valid
  answer.

**Copyable prompt**

```text
Use the oci-founder skill. Help me choose the first OCI runtime for a new API.
There is no repository yet. My known constraints are:

- language/runtime: [value or unknown]
- request or event model: [value or unknown]
- public, partner-only, private, or event-driven audience: [value]
- state and data dependencies: [value or none yet]
- region or residency: [value or unknown]
- availability tolerance: [value]
- traffic pattern: [steady, bursty, scheduled, or unknown]
- budget sensitivity and team operational capacity: [value]

Recommend the smallest reversible path among a container API, function API,
Compute path, or an OKE graduation path. Do not choose Kubernetes only because
it is familiar. Label assumptions, state which requirement would reverse the
decision, and keep the first milestone stateless where practical. Do not
create a repository or provision OCI. End with one concrete next action and
its authorization level.
```

**Evidence the agent should inspect**

- The constraints in the prompt as **User-provided** evidence.
- Any runtime, protocol, duration, concurrency, persistence, trigger, retry,
  ordering, scaling, and operational requirements you add.
- Current official OCI documentation before making time-sensitive availability
  or limit claims.

**Expected output**

- One provisional runtime recommendation and why it is the smallest adequate
  option.
- The few assumptions or unknowns that can change the decision.
- Concrete reversal conditions for rejected options.
- A stateless first milestone, its observable success condition, and a clear
  next step such as creating a minimal repository contract or generating local
  artifacts.

**Authorization level**

**Answer / Read-only.** There is no permission to create files, install tools,
open an OCI session, or provision resources.

**Done when**

You have one provisional path, no more than the material unresolved questions,
and a first deliverable that can be requested separately. A repository,
tenancy login, or detailed traffic forecast is not required for orientation.

## 3. Assess a function migration

**Scenario**

You run a handler on AWS Lambda, Google Cloud Functions, or Azure Functions and
want to know whether OCI Functions preserves the workload contract.

**Prerequisites and evidence to provide**

- Open the function repository and its source-cloud deployment configuration.
- Identify the source platform and trigger types.
- Provide non-secret examples of event shape and expected result only when they
  are safe to share.

**Copyable prompt**

```text
Use the oci-founder skill. Assess this [AWS Lambda | Google Cloud Functions |
Azure Functions] workload for migration to OCI. Inspect the repository and
deployment configuration read-only, cite the evidence you inspect, and
separate Observed, User-provided, Verified current, and Assumption evidence.

Inventory runtime and packaging, handlers, triggers and event schema, timeout,
memory and concurrency expectations, retries and failure handling, idempotency,
temporary storage, network access, identity, secret references, downstream
services, observability, and public ingress. Translate the source behavior to
OCI Functions as close, approximate, or without a direct equivalent. Verify
current OCI limits and supported behavior from official Oracle documentation
before relying on them.

Recommend whether the next step is a proof of concept, migration plan, or
requirements decision. If an operational Functions procedure is needed, name
the reviewed official Oracle skill dependency, but do not install it, generate
deployment artifacts, invoke a function, or change OCI. End with one concrete
next action and its authorization level.
```

**Evidence the agent should inspect**

- Handler and runtime manifests, build and packaging files, deployment IaC,
  trigger configuration, event contracts, and tests.
- Timeouts, memory, concurrency, retries, dead-letter or failure handling,
  idempotency, local filesystem use, and persistent-connection assumptions.
- Network dependencies, source-cloud identity, secret references, logs,
  metrics, tracing, and gateway configuration.
- Current official OCI Functions documentation for capabilities and limits
  that affect the recommendation.

**Expected output**

- A source-to-OCI function contract with explicit non-equivalences.
- A list of code, event, identity, network, and operations changes.
- One recommended next step: proof of concept, migration plan, or a decision on
  a blocking requirement.
- When applicable, a routing note for the reviewed `oci-functions-deploy` or
  `oci-functions-troubleshoot` skill without pretending it is installed or
  verified when it is not.

**Authorization level**

**Assess / Read-only.** No install, build, invocation, generated deployment
files, credential access, or cloud mutation is authorized.

**Done when**

You know whether the function model fits, which semantics need adaptation, and
which observable test would qualify a proof of concept. A function image or an
unexecuted deployment plan is not a completed migration.

## 4. Preserve the existing database engine

**Scenario**

Your application already depends on PostgreSQL or MySQL. You want an OCI plan
that preserves application semantics rather than switching databases because
of product branding.

**Prerequisites and evidence to provide**

- Open the application repository and migration/schema files.
- State the current engine and version, data size, acceptable downtime,
  recovery objective, and any region or residency constraint you know.
- Provide configuration keys or secret *references*, never passwords,
  connection strings containing credentials, dumps, or production records.

**Copyable prompt**

```text
Use the oci-founder skill. Assess this application's existing [PostgreSQL |
MySQL] dependency for an OCI migration while preserving engine compatibility.
Inspect the repository read-only and cite the files you inspect. Separate
Observed, User-provided, Verified current, and Assumption evidence.

Inventory engine and version, drivers, extensions or plugins, SQL and schema
features, migrations, connection pooling, transaction behavior, collation and
character-set expectations, data size and growth, latency, availability,
backup and restore, recovery objectives, network path, encryption, and
acceptable cutover downtime. Compare the relevant OCI candidate without
forcing an Oracle Database engine change. Treat application deployment, data
migration, and cutover as separate problems.

Verify current region availability, compatibility, backup behavior, limits,
and cost inputs from official Oracle documentation. Produce a compatibility
and cutover plan only. Do not access a database, read secret values, create a
dump, change code, migrate data, or provision OCI. End with one concrete next
action and its authorization level.
```

**Evidence the agent should inspect**

- Dependency manifests, ORM or driver configuration, schema and migration
  files, extension or plugin declarations, SQL-specific tests, and connection
  pool settings.
- Secret reference names without values, current network topology, backup and
  restore assumptions, availability needs, data volume, and cutover tolerance.
- Current official documentation for OCI Database with PostgreSQL or MySQL
  HeatWave Service, limited to the candidate that fits the existing engine.

**Expected output**

- A compatibility matrix that distinguishes confirmed facts, unknowns, and
  tests still required.
- A justified engine-preserving candidate, connectivity model, backup/restore
  expectations, and directional cost drivers.
- Phased proof, migration, validation, cutover, and rollback steps.
- A decision gate before any data access or cloud resource creation.

**Authorization level**

**Assess / Read-only.** Database connections, exports, imports, code changes,
credential access, and OCI provisioning require separate authorization.

**Done when**

Engine compatibility, connectivity, migration method, backup/restore,
identity, cost drivers, verification, and rollback are explicit. Selecting a
service name is not evidence that the application or data will work there.

## 5. Understand and control cost

**Scenario**

You need a founder-level estimate and controls that make ownership visible and
reduce surprise bills. You do not want a stale fixed-price promise or a claim
that a budget stops spending.

**Prerequisites and evidence to provide**

- State the target region, environments, runtime choice, expected active time
  or request pattern, storage and backup needs, log retention, likely egress,
  and database shape when known.
- If a repository or architecture plan exists, open it for read-only review.
- Do not provide billing credentials, payment information, or secret values.

**Copyable prompt**

```text
Use the oci-founder skill. Explain and, where the inputs support it, estimate
the OCI cost of this backend. Inspect the open repository or architecture plan
read-only. Separate Observed, User-provided, Verified current, and Assumption
inputs.

Start with directional cost drivers: active compute, database shape and
storage, gateway requests, logs and retention, egress, retained images,
backups, public networking components, and idle resources. For any numeric
estimate, verify current prices, units, region availability, limits, and
promotion eligibility using official Oracle sources, cite those sources, state
the as-of date, and show the assumptions and calculation. If a required input
cannot be verified, do not invent a number.

Recommend ownership tags, a project compartment budget with useful alert
thresholds and a monitored notification destination, deliberate log retention,
and applicable compartment quotas only where current support is verified.
State clearly that a budget is an alert, not a spending cap. Do not create a
budget, quota, tag, notification, or any OCI resource. End with one concrete
next action and its authorization level.
```

**Evidence the agent should inspect**

- IaC, architecture notes, runtime configuration, resource sizing, environment
  count, logging setup, storage, backups, egress, and lifecycle assumptions.
- Your traffic, availability, retention, and growth inputs.
- Current official Oracle pricing and service documentation for every number,
  promotion, supported quota, and region-dependent assertion used.

**Expected output**

- A cost-driver table with units and ownership.
- An assumption-based calculation only where current inputs are verifiable;
  otherwise, the exact missing variables needed to calculate one.
- Sensitivity factors that explain what can materially increase spend.
- An alerting, attribution, retention, idle-resource, and quota plan that
  distinguishes alerts from enforceable limits.

**Authorization level**

**Answer or Assess / Read-only.** The recipe does not authorize billing access,
budget or quota creation, tag changes, or resource resizing.

**Done when**

You have either a dated, source-backed, assumption-based estimate or a clear
reason one cannot yet be calculated, plus the variables that change it and the
controls that can be requested separately. No fixed price or Free Tier label
is treated as a guarantee or hard cap.

## 6. Diagnose an endpoint

**Scenario**

An endpoint, deployment, image pull, database connection, or function
invocation is failing. You want a diagnosis before anyone changes the system.

**Prerequisites and evidence to provide**

- Open the relevant repository and non-secret deployment artifacts.
- Provide the exact symptom, when it started, the expected behavior, a redacted
  error, and recent known changes.
- If you authorize read-only OCI inspection, identify the intended profile,
  tenancy, region, compartment, environment, and resource without sharing a
  credential value.

**Copyable prompt**

```text
Use the oci-founder skill in Diagnose mode. The symptom is: [symptom]. It
started: [time or unknown]. Expected behavior: [result]. Recent changes:
[changes or none known].

Inspect the repository and available deployment evidence read-only. If an OCI
session is already configured and in scope, first show the authenticated
principal/profile, tenancy, region, compartment, environment, and exact
resource you intend to inspect; do not change them. Review only the minimum
work requests, resource state, logs, metrics, events, limits, configuration,
and recent changes needed to classify the failure. Redact sensitive values.

Separate observations, hypotheses, confidence, and next confirming checks.
Classify the failure to the narrowest supported layer, such as DNS/TLS, front
door, network, identity, image/build, runtime, application, or downstream data
service. Do not restart, redeploy, edit configuration, rotate credentials,
change IAM or networking, install tools, or execute a fix. Route a service-
specific incident to a reviewed official Oracle troubleshooting skill only if
its installation and provenance are established. End with one concrete next
confirming check and its authorization level.
```

**Evidence the agent should inspect**

- The exact symptom, timestamp, request or correlation identifier, expected
  behavior, and recent change history.
- Deployment receipt and revision, endpoint and health-check configuration,
  image digest, work-request status, resource lifecycle state, and limits.
- Redacted ingress, runtime, application, and downstream logs plus relevant
  metrics and alarms, beginning at the failure boundary.
- The actual target context before any authorized OCI read.

**Expected output**

- A chronological evidence summary with secrets removed.
- Observations separated from hypotheses.
- The narrowest evidence-supported failure layer, confidence, and competing
  explanations that remain.
- One minimum next check; any proposed fix is listed separately and remains
  unexecuted.

**Authorization level**

**Diagnose / Read-only.** Reading the scoped repository and explicitly
authorized diagnostic evidence does not authorize remediation or configuration
changes.

**Done when**

The failure is classified as narrowly as the evidence permits and the next
confirming check is clear. Diagnosis is not complete merely because a plausible
fix was suggested, and it never authorizes that fix.

## 7. Prepare and perform a safe teardown

**Scenario**

You want an environment removed so it stops generating avoidable cost, while
protecting persistent data and avoiding broad deletion by name, tag, or
compartment.

**Prerequisites and evidence to provide**

- Open the exact IaC repository used for the deployment.
- Locate the exact Terraform state/backend and deployment receipt for the
  environment. Do not substitute a similarly named environment.
- State which data must be retained, backed up, exported, or explicitly
  abandoned and who owns that decision.

**Copyable prompt**

```text
Use the oci-founder skill in Teardown mode. Prepare a safe teardown preview for
the exact environment represented by this Terraform state/backend and
deployment receipt. Inspect first and do not destroy anything.

Resolve the authenticated principal/profile, tenancy, region, compartment name
and OCID, environment, state lineage, deployment receipt, and managed resource
identifiers. Compare Terraform-managed resources separately from read-only
data sources. Review the destroy graph and identify persistent data, backups,
container images, log groups and retention, buckets and objects, secrets, DNS,
certificates, reserved public IPs, notifications, and the state backend that
would be deleted or retained. Never select deletion targets only by
compartment, name prefix, wildcard, tag query, or unresolved variable.

Return the exact proposed deletion scope, retained resources and their cost
drivers, data disposition decisions still required, verification steps, and
the command or action that would require separate destructive approval. Stop
before every deletion. Do not run terraform destroy or any OCI delete command.
End with one concrete next action and its authorization level.
```

**Evidence the agent should inspect**

- Exact Terraform backend, workspace or state lineage, saved plan where
  applicable, provider target, and deployment receipt.
- Resource identifiers, managed-resource graph, and read-only data sources.
- Data classification, backup or retention requirement, restore evidence, DNS
  and certificate ownership, image retention, secrets, logs, alarms,
  notifications, and ongoing cost drivers.
- Post-destroy inventory checks appropriate to the exact target.

**Expected output**

- A target-bound destroy preview that lists deletes, dependencies, and anything
  it cannot resolve safely.
- A separate retained-resource inventory with owner, reason, expiration or
  review date, and cost driver.
- Recorded data disposition and restore/backup evidence where required.
- A final destructive gate immediately before execution, followed—only after
  explicit approval—by exact-scope verification and a credential-free teardown
  receipt.

**Authorization level**

**Teardown preparation / Read-only.** The prompt explicitly withholds deletion.
`terraform destroy`, OCI delete operations, access revocation, and credential
rotation are **Destructive** and require a separate approval immediately before
execution. Approval for the preview does not approve the destroy.

**Done when**

The preparation phase is done when the exact scope, data decisions, retained
resources, destroy impact, and verification plan are reviewable. The teardown
itself is done only after separately approved execution, when exact managed
resources are verified absent, retained resources and their cost drivers are
recorded, and no unexpected billable resource remains inside the verified
scope.

## What to request next

Once an Assess, Answer, or Diagnose recipe is complete, ask for only the next
authorization level you actually want. For example:

```text
Generate the local founder-plan.md and Terraform proposal described above.
Validate the generated files and show the diff. Do not access OCI and do not
apply anything.
```

Generating local files still does not authorize a cloud write. Before a later
apply, the agent must show the exact principal/profile, tenancy, region,
compartment name and OCID, environment, saved plan, IAM changes, public
exposure, replacements or deletes, and cost drivers, then ask for approval at
that final boundary.

## Source contract

These recipes are the public, task-oriented companion to the skill's reviewed
contracts:

- [`references/use-cases.md`](../skills/oci-founder/references/use-cases.md)
  defines the journey outcomes and completion conditions.
- [`references/discovery.md`](../skills/oci-founder/references/discovery.md)
  defines read-only repository discovery.
- [`references/service-map.md`](../skills/oci-founder/references/service-map.md)
  defines cross-cloud translation and non-equivalence rules.
- [`references/golden-paths.md`](../skills/oci-founder/references/golden-paths.md)
  defines provisional runtime choices.
- [`references/guardrails.md`](../skills/oci-founder/references/guardrails.md)
  defines identity, cost, secret, delivery, mutation, and teardown boundaries.

For the status of the public source evaluation, installation, and host
qualification, use [README.md](../README.md),
[QUICKSTART.md](QUICKSTART.md), and [COMPATIBILITY.md](COMPATIBILITY.md).
