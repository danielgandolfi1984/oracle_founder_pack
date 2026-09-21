# What has been proved, and what still needs testing

Use this page before relying on a demo, an estimate, or a deployment claim.
A document, a generated file, a passing CI run and a running customer workload
are different kinds of evidence. None should be presented as another.

Snapshot: **2026-09-21**. This summary links to existing records; it does not
replace their versions, limitations or failure history. Detailed maintainer
evidence remains in [VALIDATION.md](VALIDATION.md).

## Current evidence you can inspect

| Question | Current result | Evidence and limit |
|---|---|---|
| Is there a published skill I can install? | Yes, `v0.1.1` public preview | [Publication receipt](../tests/results/2026-09-18-v0.1.1-publication.json) records the tag, Codex project install/reinstall and downloaded asset verification. It does not qualify every host runtime |
| Are there focused skills for starting and migrating? | Yes, two source-only `0.1.0` companions on `main` | [Companion lifecycle receipt](../tests/results/2026-09-21-companion-install.json) records six local-source cases: two skills × three installer layouts, including removal and reinstall. It does not prove native host behavior or live OCI use |
| Do the three skills exist in the public source and install together? | Yes, at the recorded revision in one Codex project layout | [Public-source assessment](../tests/results/2026-09-21-public-source-assessment.json) binds the public clone, exact skill trees, joint installation, selective removal and scoped cleanup. It does not qualify native sessions or joint use on other hosts |
| Can I follow the user journey in English or Portuguese? | Yes, equivalent complete founder guides | [English](FOUNDER-GUIDE.md) and [Português](i18n/pt-BR/FOUNDER-GUIDE.md) cover installation, prompts, account access, VCN/VM, migration, costs and glossary. Not every engineering reference or historical receipt is translated |
| Has the skill answered a real agent prompt? | One recorded native Codex comparison passed with reservations | [Native probe](../tests/results/2026-09-18-v0.1.1-codex-native.json) and [assessment](../tests/results/2026-09-18-v0.1.1-assessment.json). This is not a full cross-host replay or a usability benchmark |
| Do repository and package checks run in CI? | Yes, for the exact commits linked | The bilingual three-skill source at `2baedb0` passed both jobs in [run 35598862683](https://github.com/danielgandolfi1984/oracle_founder_pack/actions/runs/35598862683). Check the [workflow](https://github.com/danielgandolfi1984/oracle_founder_pack/actions/workflows/validate.yml) for later revisions; CI is not an OCI deployment |
| Has the VM lab been executed in an OCI account by this project? | Not recorded | [FIRST-VM.md](FIRST-VM.md) is a source-reviewed, human-executed guide, not field-test evidence |
| Has the Container API preview been applied, rolled back and removed in OCI? | Not recorded | Its [README](../blueprints/container-api/README.md) describes local checks and open field gates. Generated Terraform is not proof of deployed resources |
| Can I exercise business rules locally? | A separate synthetic, in-process slice exists | [Local lab](../examples/local-backend/README.md) and [tests](../tests/test_local_backend.py) exercise membership, roles, projects/tasks, retries, SQLite persistence and new-file recovery. No HTTP listener, real token verification or OCI integration |
| Can I send HTTP requests and validate signed tokens locally? | An optional loopback lab exists | [HTTP lab](../examples/local-backend/HTTP-LAB.md), [optional tests](../examples/local-backend/http-tests/) and [signed-request smoke](../examples/local-backend/http_smoke.py) exercise `127.0.0.1` requests and RS256 tokens with ephemeral local keys. No real identity provider, TLS, public hosting or OCI integration |
| Can I prepare a provider trust configuration and rehearse key rotation? | An offline preflight and synthetic rehearsal exist | [Identity guide](../examples/local-backend/IDENTITY-INTEGRATION.md), [verifier tests](../examples/local-backend/http-tests/test_provider_auth.py) and [preflight tests](../examples/local-backend/http-tests/test_provider_preflight.py) cover the explicit supported token contract. No provider connection, real access token, automatic refresh or provider-compatibility evidence |
| Is the full authenticated backend implemented? | No | [REFERENCE-BACKEND.md](REFERENCE-BACKEND.md) is the complete target. The unchanged Container API preview has only anonymous test endpoints; the separate local lab is not a deployable authenticated service |
| Are there measured monthly costs, customer capacity or a time-to-production benchmark? | No | [COST-SCENARIOS.md](COST-SCENARIOS.md) contains illustrative workload assumptions, not observed bills or capacity results |
| Are there verified founder/customer success stories in this toolkit? | Not yet | Do not turn the reference scenario into a testimonial or invent a customer, quotation or deployment result |

The immutable release tag and archives are unchanged by documentation on
`main`. Installation evidence for that release does not automatically validate
new code, a new host version or a new operational path.

The source-only companions are standalone founder planning instructions, not
new implementations of upstream Oracle service procedures. Their local-source
installer receipt binds exact skill fingerprints. Separate manual, content-forward
checks exercised a new FastAPI/PostgreSQL project and a Node.js workload arriving
from AWS; they kept secrets out of the conversation, preserved stack choices,
and required migration evidence and rollback planning. These narrow manual
checks are not native cross-host qualification or a deployment benchmark.

### Public-source installation follow-up

At commit `2baedb08012111e91b1f5b22e77211bbcc344de1`, an unauthenticated HTTPS
clone matched the three reviewed skill trees. The
[initial attempt](../tests/results/2026-09-21-public-source-initial.json) stopped
at installer acquisition before installing any skill. Its underlying npm or
integrity diagnostic was not retained; the cause remains undetermined.

A [separate follow-up](../tests/results/2026-09-21-public-source-codex.raw.json)
used the existing reviewed cache with `npm ci --offline --ignore-scripts` and
the original dependency-lock and CLI-file hash checks. It installed the three
skills from the verified clone into one Codex project layout. Removing only
`oci-founder-start` preserved `oci-founder` and `oci-founder-migrate` plus their
lock entries. Final removal left no installed skills or unexpected residuals;
empty shared directories and an empty skill lock were allowed. Twelve named
global skill targets were unchanged.

Only npm acquisition was offline, not the HTTPS clone. These receipts do not
test installation directly through the CLI's remote-URL route, native agent
discovery or behavior, other hosts' joint layouts, or any OCI deployment. The
[assessment](../tests/results/2026-09-21-public-source-assessment.json) preserves
both results and binds the original sanitized receipts by SHA-256.

## Reproduce the local application checks

From a source checkout of `main` (not the released skill archive), run:

```sh
python3 -B -m unittest discover -s tests -p test_local_backend.py -v
python3 -B examples/local-backend/demo.py
```

The local journey was exercised on 2026-09-19 with Python 3.12.14 and temporary
synthetic data. It verified creation/retry, cross-workspace denial, owner/member
permissions, immediate revocation under the same fixture identity, persistence
after reopening, and reading an independent backup copy. The workflow runs
both the tests and the demo again for each new source commit. A passing result
does not verify real identity-provider tokens, a listening HTTP service, cloud
database recovery, OCI deployment or any production security boundary.

### Optional signed HTTP checks

Follow the [HTTP lab setup](../examples/local-backend/HTTP-LAB.md) to install
the hash-pinned optional dependencies into an isolated CPython 3.12 environment.
The separate tests exercise fixed-key RS256 verification, raw HTTP framing,
strict loopback/Host restrictions, private session files and cleanup. The
signed-request smoke additionally checks accepted and tampered tokens, project
creation/retry, cross-workspace denial and immediate membership revocation
through a real `127.0.0.1` listener. These checks were exercised locally on
2026-09-19; their dedicated CI job reruns against each new source revision.

This is local cryptographic and transport evidence with synthetic users. It
does not establish a real person's identity or qualify external issuer/JWKS
integration, public HTTP hosting, TLS, key rotation, production availability,
managed-database recovery or OCI operation. The default in-process lesson and
the released skill packages remain independent of the optional dependencies.

### Offline provider-configuration and rotation checks

Using the same optional environment, run:

```sh
"$LAB_ENV_DIR/venv/bin/python" -B -m unittest discover \
  -s examples/local-backend/http-tests -p 'test_provider*.py' -v
"$LAB_ENV_DIR/venv/bin/python" -B examples/local-backend/provider_demo.py
```

On 2026-09-19, 47 focused tests and the synthetic in-process journey passed
under CPython 3.12.14. They exercise strict access-token admission, explicit
subject bindings, unconfigured-key rejection, key overlap/removal, snapshot
expiry and clock rollback, invalid-reload denial, recovery with valid
configuration, private input-file handling and current workspace permissions.
The preflight validates existing files only; it does not prove where public
keys came from, verify a token or connect to a provider. The CI job also runs
these tests and the synthetic journey for new source revisions.

This evidence extends the offline learning contract, not the HTTP lab's
fixed-key verifier. `ProviderVerifier.ready()` checks snapshot freshness
separately; the existing `/readyz` still checks only SQLite. Real-provider token
compatibility, trusted metadata retrieval, automated key refresh, OAuth/login,
TLS and deployment remain unverified. No existing release receipt is replaced.

The 2026-09-21 follow-up adds optional `--diagnostics` with fixed input labels
and error codes, retaining the previous default JSON. Its
[diagnostic tests](../examples/local-backend/http-tests/test_provider_diagnostics.py)
check classification, output redaction, no file changes/network calls, and
fail-closed reload/recovery. All 22 added diagnostic tests and the combined
69-test offline provider suite passed locally under CPython 3.12.14. The
[troubleshooting guide](../examples/local-backend/IDENTITY-TROUBLESHOOTING.md)
separates local configuration failures from documented provider-profile
differences. This is still offline evidence, not a connected-provider result.

## Labels to use in guides and demonstrations

- **Proposed:** a design, expected result or test that has not run.
- **Source-reviewed:** checked against the linked official documentation on
  the stated date; no execution is implied.
- **Locally tested:** exercised using the exact application, tool and fixture
  revisions recorded, without implying OCI access.
- **Sandbox tested:** executed in an authorized OCI sandbox, with a private
  target-bound receipt and redacted results.
- **Field observed:** measured in the stated real-world context with permission
  to use the evidence. Scope and observation period must be explicit.

These are documentation labels, not new machine-receipt status values. Preserve
existing script schemas. A pass applies to a specific test, not every behavior
of a service or all versions of a host.

## A reproducible proof card

Prepare this checklist **before** an experiment. Leave unknowns as unknowns.
Keep account identifiers and raw operational evidence in a restricted location
outside Git. Share a redacted summary only after review.

| Record | Minimum detail |
|---|---|
| Claim and scope | What is being tested and what a pass would establish |
| Revisions | Toolkit tag/commit, application commit and image digest if applicable, IaC/provider/lock versions, host and CLI versions |
| Target and authority | Private account, principal/profile, region, compartment and exact resources; who approved each mutation |
| Workload | Synthetic dataset, request mix, payload sizes, concurrency, duration and acceptance thresholds |
| Timing | Account setup, local setup, deployment, verification and cleanup measured separately; include retries and waiting time |
| Outcomes | Pass/fail/not run for every test, redacted errors and evidence location; no screenshot-only pass claim |
| Recovery | Rollback and restore attempts, what data was retained, and tests repeated after recovery |
| Costs | Dated estimate, usage interval, observed bill/usage after reporting lag, credits shown separately, unresolved items |
| Cleanup | Exact managed-resource inventory, deleted/retained/blocked outcomes and next review owner |
| Limits | What was not tested and what changed since the run |

For the manual VM lab, use its receipt and exact-resource cleanup process. For
the Container API preview, use the existing saved-plan, state and receipt
contracts. A handwritten proof card must not substitute for those safety gates.

## The first field-validation plan

This is a proposed sequence, **not a record of completed execution**:

1. Select one isolated sandbox and one path. Confirm the identity, scope,
   spending allowance, time window, region/capacity, data restrictions and
   cleanup owner. Obtain the path's explicit approvals before any mutation.
2. Complete the documented prerequisites and capture the exact revisions.
   Record account onboarding time separately from an already-prepared run.
3. Execute the chosen path with synthetic data. Verify the actual target,
   endpoint/SSH result, intended access boundary and observable failure signals.
4. For a reviewed IaC path, check the second plan for unintended changes. Do not
   infer idempotency from a single successful apply. For the manual VM lab,
   mark this IaC test not applicable rather than inventing a second apply.
5. Exercise the approved rollback/recovery test, then verify the recovered
   workload. When data is involved, test restore; keeping a backup file is not
   evidence of successful recovery.
6. Preview and approve exact-resource teardown. Record retained storage,
   backups and other dependencies, and follow up when billable usage appears.
7. Have a second operator reproduce the scoped test independently. Publish
   redacted results with failures and open items, not just the successful run.

The local lab tests application authorization and persistence using synthetic
identities and SQLite; the optional mode adds locally signed tokens and
loopback HTTP checks. The full backend's real login and production HTTP boundary,
upload, managed-database and sandbox restore tests must wait for those
integrations to exist. See its [acceptance plan](REFERENCE-BACKEND.md). Neither
the local lab nor a `200 OK` from the Container API preview's health endpoint
closes those gates.

## Customer stories without invented proof

When a founder completes an evaluation, request permission before publishing
their name, company, logo, quotation, metrics or architecture. Do not put
customer data into public issues. A useful case record includes:

- the original situation and why OCI was considered;
- the exact workload and what the team preserved or changed;
- setup effort, failed attempts and help needed, not just the final command;
- cost assumptions, observed usage period and non-recurring credits;
- results, operational tradeoffs, limitations and the founder's next decision;
- the scope of consent and the approved public evidence.

An anonymized example must still have real supporting evidence and permission
where required. A fictional scenario must say it is fictional and must not
appear among customer results. For reproducible public labs, use synthetic data
and independently reviewed receipts instead of confidential customer material.

Next: [cost scenarios](COST-SCENARIOS.md), [reference backend](REFERENCE-BACKEND.md),
or [support and reporting boundaries](../SUPPORT.md).
