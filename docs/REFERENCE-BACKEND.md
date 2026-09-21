# Reference backend: a small B2B SaaS

**Status: target design with a separate local learning slice; no complete
authenticated application or validated OCI deployment.**
This guide connects infrastructure learning to a founder outcome: a customer
signs in, creates a project, tracks work, and optionally attaches a file.
Use it to scope your next implementation, not as a promise that installing the
skill provisions a complete product. Source review: 2026-09-19.

Start with [account access](ACCOUNT-SETUP.md) and, if networking is new to you,
the [first VM lab](FIRST-VM.md). A working lab VM is not a production backend.

## 1. The customer journey

1. Alice signs in through your chosen identity provider and selects a workspace.
2. She creates a project, adds a work item, and updates its status.
3. A colleague in the same workspace can see the result; another customer's
   user cannot read, modify, enumerate, or attach files to it.
4. If attachments are required, Alice uploads a small permitted file and later
   downloads it through an authorized application request.
5. An operator can trace a failed request without reading tokens or customer
   content, restore an agreed recovery point, and roll back a bad release.

Proposed domain: workspace, membership, project, work item, attachment metadata.
Every customer-owned record belongs to a workspace. Membership and role checks
are server-side; a caller-supplied workspace ID is a selection, not proof of access.
Start with an owner/member role model. Billing, invitations, email, and a frontend
are separate requirements, not features shipped by this repository.

## 2. What exists here, and what must be built

Inspect the [Container API preview](../blueprints/container-api/README.md),
[sample app](../blueprints/container-api/app/app.py), and
[runtime Terraform](../blueprints/container-api/terraform/runtime/).
“Present” below means source exists, not that it has passed a live OCI test.

| Component | Present in the Container API preview | Required for this reference product |
|---|---|---|
| HTTP application | Anonymous `GET /`, `/healthz`, `/readyz`; static readiness response | Business API, validation, persistence, dependency-aware readiness, application tests |
| Authentication and tenant authorization | Neither is implemented | Identity-provider integration, token verification, membership/role checks on every operation |
| Database | No database, driver, schema, or migration assets | Keep the backend's existing PostgreSQL or MySQL; choose connectivity, backups, and migration tooling explicitly |
| Attachments | No bucket or upload implementation | Optional private Object Storage integration and tenant-scoped metadata/access |
| Network and runtime | Sandbox Terraform for a gateway and one private Container Instance | Workload-specific network review; tested availability and capacity design before production |
| HTTPS and domain | Gateway default certificate path for the OC1 sandbox only; private backend HTTP | Owned custom domain/certificate, renewal ownership, and explicit review of backend transport |
| Logs and alerts | App JSON stdout; gateway service-log and CPU/memory alarm Terraform | Centralized app-log ingestion, retention/redaction, business/error signals, tested alert delivery |
| Secrets | No app secret injection; app resource principal disabled | Reviewed secret retrieval and narrowly scoped workload identity, plus rotation tests |
| Delivery and recovery | Image-digest, plan-review, receipt, rollback/teardown tooling | Real sandbox evidence, restore drill, safe schema migration, production operating procedures |

The preview is `0.2.0-preview.4`, sandbox-only, with no live OCI plan/apply
evidence. Its validators intentionally accept a narrow resource graph. This
design is **not** permission to add components to that graph or bypass its
checks: an implementation needs separately reviewed code, contracts, and tests.

### Separate local learning slice

The [local backend lab](../examples/local-backend/README.md) on `main` now
implements a narrow application layer: projects and work items in SQLite,
current workspace/role checks, idempotent creation, persistence after reopening,
and recovery into a new file. It runs through direct Python calls with synthetic
identities, **not real sign-in**. Without an injected verifier, its in-process
business interface rejects access. The optional [HTTP lab](../examples/local-backend/HTTP-LAB.md)
adds a loopback-only listener and fixed-key RS256 verification of locally
issued test tokens. Real identity-provider integration is still missing;
neither the demo's subject map nor its local signing harness is a production
identity provider.

An additional [offline identity contract](../examples/local-backend/IDENTITY-INTEGRATION.md)
checks explicit issuer/audience/client/scope settings, bounded public-key
snapshots and external-subject bindings. A synthetic in-process demo exercises
key rotation and current membership checks. This prepares an integration
boundary; it does not add real login, provider discovery, automatic key refresh,
TLS or verified compatibility with any provider. Snapshot freshness is a
separate signal from the lab's database-only `/readyz`.

Its [tests](../tests/test_local_backend.py) cover the local contract only.
The optional HTTP tests additionally exercise signature/issuer/audience/time
validation, strict local request framing and signed requests through the API.
They do not qualify a production transport or actual user login.
The existing Container API app, Terraform resource graph and released packages
are unchanged. SQLite is a self-contained lesson, not a recommendation to
replace an existing database or deploy this sample unchanged.

## 3. Target architecture and decisions

```text
Client + identity provider -> HTTPS/custom domain -> API Gateway -> private API
                                                                  |-> existing SQL database
                                                                  |-> private Object Storage (optional)
API -> reviewed secret retrieval + redacted centralized application logs
```

Keep one application initially; this is not a requirement to adopt Kubernetes,
microservices, a different database engine, or an AI service.

**Authentication is not tenant authorization.** Keep your existing identity
provider when suitable. OCI API Gateway supports token validation and route
authorization policies, but your application must still enforce workspace
membership and object ownership. The proposed contract is `401` for missing or
invalid authentication and `403` for an authenticated caller denied an operation;
never include another customer's data in the error. Verify issuer, audience,
signature, expiry, and allowed algorithms. Never trust client-supplied identity
headers. [Oracle token-policy documentation](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayusingjwttokens.htm)

**Preserve the database first.** Keep the existing engine, driver, and migration
tool unless a measured requirement justifies change. Decide separately whether
the database stays where it is or moves. Review TLS, private connectivity or
explicit restricted access, connection limits, latency, transfer cost, and
failure behavior. The preview includes no database route or general app internet
egress; existing external services will not become reachable automatically.

**Own the public endpoint.** For a customer-facing service, plan DNS ownership,
a matching TLS certificate, expiry monitoring, and renewal verification.
Oracle recommends custom TLS certificates for public or production API gateways;
its default certificate path is documented for realm OC1 only and is not a
production qualification. Do not extrapolate it to another realm.
[Oracle custom-domain and certificate guide](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewaysettingupcustomdomainscerts.htm)

**Make attachments optional and private.** Prefer an authenticated API-mediated
path for the initial small-file design: authorize the workspace, allocate the
object key server-side, enforce size/type/quota rules, and deny reads until
content checks complete. Validate ownership again on download and deletion.
Do not accept an arbitrary bucket or object key from the caller. A direct-upload
extension needs separate controls: an Object Storage pre-authenticated request
(PAR) URL grants access to whoever holds it; it does not re-check application
membership. Avoid public buckets and never log PAR URLs.
[Oracle PAR access model](https://docs.oracle.com/en-us/iaas/Content/Object/Tasks/usingpreauthenticatedrequests.htm)

**Secrets and observability are application work.** Design narrowly scoped
retrieval from OCI Secret Management or your existing approved secret store;
do not put secret values in Terraform variables/state, images, chat, or logs.
The current app has no such integration. Define rotation and failure behavior
before enabling a workload identity. [Oracle Secret Management overview](https://docs.oracle.com/en-us/iaas/Content/secret-management/overview.htm)
Keep request IDs, normalized route names, status, duration, and release ID;
exclude tokens, bodies, query secrets, and file contents. The preview's gateway
logs do not centralize app stdout; on-demand container log retrieval is not a
retention/alerting pipeline. [Oracle container log retrieval](https://docs.oracle.com/en-us/iaas/Content/container-instances/retrieve-logs.htm)

## 4. Acceptance contract to implement and test

These are acceptance tests for the complete target, **not passing end-to-end
results**. The separate local lab exercises only a subset with synthetic
identities and SQLite. The optional HTTP lab adds signed test-token and loopback
transport checks, not an external provider or production HTTP stack. Neither
lab covers uploads, managed databases or OCI. Run the complete tests against two isolated
test workspaces with synthetic data, then record the exact version and evidence
as described in [Evidence](EVIDENCE.md).

| Test | Required result |
|---|---|
| Sign in; create, list, update a work item; restart the app | Correct result persists; only the caller's authorized workspace appears |
| Missing, expired, wrong-audience, or tampered token on a business/upload route | `401`; no database write or uploaded object |
| Workspace B user reads, edits, lists, or deletes workspace A's records | `403` for direct forbidden operations; lists reveal no foreign records or counts |
| Membership removed or role downgraded while the identity token is still valid | Previously allowed operations become forbidden under current server-side membership/role rules; no stale privilege survives |
| A member attempts an owner-only action within their own workspace | `403`; workspace membership alone does not grant the owner's permissions |
| Workspace B user uploads to, downloads from, or changes A's attachment metadata | `403`; no object write/read and no upload capability issued |
| Valid user exceeds an upload limit or submits a disallowed file | Documented rejection; no downloadable partial/unchecked object |
| Retry a timed-out create/upload completion | No duplicate work item or orphaned billable attachment; documented idempotency contract |
| Database unavailable or secret rotated | Bounded errors/retries; readiness reflects dependency failure; no secret leakage |
| Request fails in sandbox | Correlatable redacted app/gateway evidence and a delivered alert where configured |
| Restore and release rollback drill | Measured data loss/recovery time meets agreed targets; previous app still reads compatible data |

If direct PAR uploads are added later, test object/action scope, expiry, and
revocation separately. A copied, still-valid PAR may work for another holder;
do not describe it as enforcing per-request tenant membership.

## 5. Advance through evidence gates

1. **Local product slice:** implement the business API in the founder's repository;
   use synthetic data and a local/test database. Pass the authentication,
   isolation, persistence, and optional upload tests. No OCI credentials needed
   for the planning phase.
2. **Approved sandbox:** select the region and exact resources, estimate cost with
   [Cost scenarios](COST-SCENARIOS.md), review the plan, and obtain approval before
   any mutation. Use a separately reviewed implementation for the new components.
   Verify endpoint, identity/network boundaries, image digest, logs, alerts,
   second-plan behavior, recovery, and scoped cleanup. Record failures too.
3. **Production gate:** agree on availability, expected/peak load, recovery time
   and recovery point targets; qualify runtime capacity and failure handling.
   Require tenant-isolation/security review, restore evidence, domain/certificate
   ownership, secret rotation, on-call ownership, cost alerts, and a cutover plan.
   Passing a local check or a health endpoint does not satisfy this gate.

## 6. Migration, rollback, and exit

- **Migration:** inventory dependencies and data ownership first. Rehearse with
  sanitized data; measure counts, integrity, downtime, and latency. Define a
  cutover checkpoint and a single write authority so old and new systems do not
  silently diverge. Keep the old path until acceptance criteria pass.
- **Backups:** choose database-appropriate backups and attachment retention,
  protect recovery credentials separately, and restore into an isolated target.
  A successful backup job is not a demonstrated recovery. Record actual recovery
  time and data loss, not just configured schedules.
- **Rollback:** keep the previous image digest and compatible schema; prefer
  additive migrations until the rollback window closes. Application rollback
  does not undo data changes. Any restore/data-loss decision needs explicit
  approval. The current single-instance preview can incur replacement downtime.
- **Teardown:** use fresh reviewed plans, state, and deployment receipts for the
  exact owned resources. Decide database/attachment/export retention first;
  never destroy a shared database or bucket. Verify exact-resource absence and
  retained costs afterward. Follow the [preview teardown contract](../blueprints/container-api/README.md#teardown)
  only for its supported resource set, not for this unimplemented target design.

## Optional later: one useful AI feature

Consider a draft summary of a project's work items only if users need it. Define
an opt-in flow, authorized input scope, human review, quality test set, latency,
and cost per accepted summary. Evaluate hallucinations and cross-tenant leakage;
exclude secrets and make deletion/retention expectations explicit. No model,
service integration, or quality claim is implemented by this guide.
