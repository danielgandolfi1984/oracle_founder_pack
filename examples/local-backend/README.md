# Local backend learning slice

Practice the application rules behind a small B2B SaaS before choosing cloud
resources: who can see a workspace, which operations require an owner, how a
retry avoids creating duplicate records, and whether data survives reopening.

**The default lesson is synthetic and in-process, not a deployable service.**
`demo.py` opens no listening port, sends no network requests, uses no OCI
credentials, and has no real identity-provider integration. It is available on `main` only;
the released `v0.1.1` skill archives remain unchanged. The separately maintained
Container API is now `0.2.0-preview.4`; see its [security update](../../docs/SECURITY-UPDATE-2026-09-21.md).
Installing the released skill does not install this example.

After this lesson, the optional [HTTP and signed-token lab](HTTP-LAB.md) adds
`curl` requests to a temporary `127.0.0.1` listener and RS256 verification of
locally issued synthetic tokens. It requires separate pinned dependencies;
the default commands below remain dependency-free and do not start a server.

The separate [identity integration guide](IDENTITY-INTEGRATION.md) then shows
how trusted issuer/audience settings, public keys and explicit user bindings
fit together. Its preflight and synthetic rotation demo are offline; they do
not connect an identity provider or change the HTTP lab's local-only contract.

## Run it locally

Prerequisites: a checkout of this repository, Python **3.10 or later** with its
`sqlite3` module, and permission to create temporary files. There are no
third-party Python packages, account signup, Docker, or cloud setup steps.

From the repository root:

```sh
python3 -B examples/local-backend/demo.py
python3 -B -m unittest discover -s tests -p test_local_backend.py -v
```

Or ask your coding agent:

> Inspect `examples/local-backend/` and its tests in this source checkout.
> Explain the trust boundary, then run the two local commands above. Temporary
> writes containing synthetic fixtures are allowed; do not use credentials,
> network access, OCI, or any customer database. Report failures and limitations.

The demo creates an isolated temporary directory and synthetic fixtures:

| Workspace | People | Starting permissions |
|---|---|---|
| `w-a` | `alice`, `amy` | Alice is the owner; Amy is a member |
| `w-b` | `bob` | Bob is the owner |

It exercises project/work-item creation, an idempotent retry, cross-workspace
denial, role downgrade and membership revocation, persistence after reopening,
and a backup restored into a **new** database file. Expect safe `PASS` labels
and successful command exit, followed by a passing test summary with `OK`.
Output is not supposed to contain bearer values, credentials, or customer data.
A failure is a failed local check, not a reason to try an OCI command.

## What runs, and where trust stops

```text
demo or unit test -> direct API.handle(...) call -> authorization -> SQLite
                         |
                         +-> injected synthetic verifier (tests/demo only)
```

The in-process interface is `API(store, verify_token=None)`, with
`handle(method, path, headers=None, body=None)` returning `(status, payload)`.
Paths and numeric statuses describe an application contract; they are **not**
an HTTP server, HTTP parser, browser endpoint, or transport security layer.
Do not use `curl` against `demo.py`. Use only the separate, explicitly started
[loopback HTTP adapter](HTTP-LAB.md) for HTTP requests; never expose it publicly.

Without an explicitly supplied verifier, business requests are denied with
`401`. Only the demo and tests inject a map of synthetic bearer values to
synthetic subjects. That map is a fixture, **not authentication suitable for
real users**. The optional HTTP lab has a fixed-key RS256 verifier checking
issuer, audience, signature and token times, but only with synthetic local
issuance. Integration with a real identity provider remains a release blocker.

The intended integration boundary is:

1. A trusted verifier establishes the authenticated subject or rejects the
   request; never derive identity from an untrusted user-ID header.
2. The application reads current workspace membership and role for the subject.
   A selected workspace ID is not proof of access.
3. It checks that each project/item belongs to that workspace before accessing
   it. Membership and role are checked again on later requests and replays;
   a previously accepted fixture value does not preserve revoked privileges.

## Application contract

Only health/readiness are anonymous. Business operations require a verified
subject. In the following table, `{w}`, `{p}`, `{i}`, and `{subject}` identify
a workspace, project, item, and member respectively.

| Call | Input or behavior |
|---|---|
| `GET /healthz` | In-process health check |
| `GET /readyz` | Readiness checks the working database |
| `GET /workspaces` | Lists only the subject's current memberships |
| `GET /workspaces/{w}/projects` | Lists that workspace's projects |
| `POST /workspaces/{w}/projects` | Body: `{"name": "Demo project"}` |
| `GET /workspaces/{w}/projects/{p}/items` | Lists that project's work items |
| `POST /workspaces/{w}/projects/{p}/items` | Body: `{"title": "First task"}` |
| `PATCH /workspaces/{w}/projects/{p}/items/{i}` | Body: `{"status": "done"}`; allowed values: `todo`, `doing`, `done` |
| `PATCH /workspaces/{w}/members/{subject}` | Owner only; body: `{"role": "member"}` or `{"role": "owner"}` |
| `DELETE /workspaces/{w}/members/{subject}` | Owner only; removes membership |

Owners and members can use the project/item operations. Members cannot change
roles or remove memberships. Removing or demoting the last owner is rejected
with `409`; this is not a workspace-deletion endpoint. Authenticated requests
matching these routes with forbidden or unknown workspace/project/item IDs return `403`
without revealing another workspace's data.

POST operations use an `Idempotency-Key` header. Its namespace includes the
authenticated subject, workspace, and operation; the request body must match
the original request. An accepted identical retry returns the original `201`
response snapshot without creating another record. Reusing the key in that
scope with a different body returns `409`. Replays must still pass current
authorization; cached success is not a shortcut around revoked membership.
This teaches an application-level retry contract, not distributed exactly-once
delivery or a guarantee about external side effects.

## Persistence and recovery exercise

SQLite keeps this lesson self-contained. It is **not** a recommendation to
replace the founder's existing PostgreSQL/MySQL database or a claim that this
storage design meets production requirements. The example binds SQL values
using parameters; see the official [Python placeholder guidance](https://docs.python.org/3/library/sqlite3.html#how-to-use-placeholders-to-bind-values-in-sql-queries).

The demo closes and reopens its working database to check committed data. It
also exercises SQLite's [backup API](https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.backup)
and verifies a restore in a new file. Existing destination files must not be
overwritten. This local check does not measure a cloud recovery time/point
objective, off-site durability, disaster recovery, or recovery under load.

Temporary files contain synthetic records only and are cleaned up by the demo.
Do not supply a customer database, real tokens, secrets, or operational backup
paths. There is no cloud teardown step. If a run is interrupted and leaves a
temporary directory, identify that exact run's synthetic directory before
removing anything; never clean up a broad home, repository, or account scope.

## What passing this example does not prove

- Real sign-in, provider integration, password management, MFA, invitations,
  or account recovery. Neither synthetic lookup nor locally issued signed
  tokens establish the identity of a real user.
- TLS, domain ownership, rate limiting, or internet-facing security. The
  default lesson has no HTTP transport; the optional lab tests only its
  deliberately restricted loopback adapter and input/body limits.
- Production database migrations, multi-process/concurrent behavior,
  availability, capacity, encrypted backup operations, or measured recovery.
- Uploads/Object Storage, app secrets, centralized logs/alerts, billing,
  a frontend, or any optional AI feature.
- OCI deployment, IAM correctness, live resource cost, or customer outcomes.

Keep existing OCI Terraform, deployment receipts, release manifests, and
approval gates unchanged. Do not package this example into the existing
Container API image and infer that its reviewed resource graph now supports
the reference SaaS.

## Your next decision

Use the results to discuss application behavior with your coding agent:

> Review this local slice's workspace isolation and retry rules. Map them to
> my existing backend and identity provider. List the missing implementation
> and tests before proposing any infrastructure change. Do not deploy.

Continue with the [reference backend design](../../docs/REFERENCE-BACKEND.md)
for the larger acceptance contract and [evidence guide](../../docs/EVIDENCE.md)
for the distinction between local checks, approved sandbox evidence, and
production qualification. A green local run completes only this teaching slice.
