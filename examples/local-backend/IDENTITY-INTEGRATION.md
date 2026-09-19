# Identity integration: an offline readiness lesson

Reviewed against public sources on **2026-09-19**. This is a source-only,
educational step toward a future provider integration, **not a connected login
system or a claim of compatibility with OCI Identity Domains**.

You can rehearse an explicit trust configuration, public-key snapshots, subject
bindings, and rejection cases without visiting a provider or supplying a real
token. The existing [HTTP lab](HTTP-LAB.md) remains synthetic-only: never give
it real bearer credentials or expose its standard-library server to a network.

## 1. Understand the three separate decisions

| Decision | Question | This lesson's boundary |
|---|---|---|
| Token verification | Did the configured issuer sign a suitable access token for this API and allowed client? | An offline verifier with an intentionally narrow profile |
| Identity binding | Which local member corresponds to the verified external subject? | An explicit mapping within one configured issuer; no automatic signup |
| Authorization | May that member act in this workspace now? | Current database membership and role, not token-supplied owner/admin claims |

An **access token** is for a resource API. An **ID token** describes an
authentication event for a client and must not substitute for API access. The
resource API's audience and the calling application's client ID are different
concepts. Oracle explains these validation distinctions in its
[token-validation guidance](https://docs.oracle.com/en-us/iaas/Content/Identity/api-getstarted/TokenValidation.htm).

Our verifier requires RS256 and an access-token type of `at+jwt` or
`application/at+jwt`, not generic `JWT`. This follows the explicit-type approach
of [RFC 9068](https://www.rfc-editor.org/rfc/rfc9068.html#section-4) and the
cross-token-confusion defenses in
[RFC 8725](https://www.rfc-editor.org/rfc/rfc8725.html#section-3.12).
It is **not** a complete RFC conformance certification.

The implementation additionally requires one exact audience string, an allowed
`client_id`, the configured scope, bounded token lifetime, a fresh configured
key snapshot, and a known subject binding. Provider defaults can differ in
token type, claims, audience shape, scope names, key format, or algorithm.
If they differ, record the incompatibility; do not disable validation or relabel
an ID token to make this lesson pass. No provider is trusted by default.

## 2. Collect configuration, not credentials

Ask the application's identity owner for reviewed values. Keep the files
outside Git and do not attach them to public issues or chats. A public signing
key is not a private credential, but the integrity of its source is critical.
JWKS means a JSON object containing a `keys` array; key provenance matters as
much as parsing the file. See [RFC 7517](https://www.rfc-editor.org/rfc/rfc7517.html#section-9.1).

| Input | What to collect and check |
|---|---|
| `issuer` | Exact configured HTTPS issuer, including significant trailing slash; never derive trust from a token's unverified claims |
| `audience` | Your resource API's intended audience, not the caller's client ID, domain OCID, or a guessed console URL |
| `allowed_client_ids` | Explicit list of 1–16 distinct client identifiers allowed to call this API; identifiers only, never client secrets |
| `required_scope` | Exact API-admission scope, such as this lesson's `founder:api`; not an assertion that Oracle predefines that scope |
| `max_token_lifetime_seconds` | Reviewed integer from 1 to 3600, fitting this lesson's short-lived-token policy |
| `jwks_fetched_at` / `jwks_expires_at` | UTC epoch integers recording actual snapshot acquisition and its local trust deadline; window at most 3600 seconds and current time inside it |
| Public JWKS | Reviewed public RSA signing keys and their `kid` identifiers from the configured provider's trusted source |
| Subject bindings | Explicit external-subject-to-local-member mapping, with an owner and review process |

The time fields are **our local snapshot policy**, not standard JWKS fields or
a promise of the provider's key lifetime. Do not refresh the acquisition date
on an old file to make it appear current. A completed preflight cannot prove
that the file actually came from the provider.

This adapter accepts 1–8 RSA keys, sized 2048–8192 bits, with exponent 65537.
Each key requires `kid`, `kty`, `n`, and `e`; optional fields
are `alg: RS256`, `use: sig`, and `key_ops: ["verify"]`. Other JWK fields,
including `x5c`, are unsupported here. If a provider publishes a broader set,
an identity/security reviewer must determine whether selecting compatible
public signing keys preserves its meaning. Do not blindly strip fields or
security distinctions to force a match. Never supply RSA private components,
symmetric keys, private PEM files, client secrets, passwords, or tokens.

The binding-file shape is a JSON object, for example the **synthetic** mapping
`{"external|alice": "alice"}`. Identity is the tuple **(issuer, subject)**:
this map's keys are scoped to the one configured issuer. Email, display name,
and an unverified token are not authoritative identity bindings. The map is
one-to-one, with at most 1000 entries; no two external subjects may collapse
onto one local member. Do not map a real person onto a seeded demo owner.
A machine/client subject is not automatically a human user or workspace owner.

## 3. OCI Identity Domains: read-only discovery checklist

These are inspection steps for an **existing**, authorized application/domain.
They do not create applications, assign roles, grant scopes, activate clients,
change IAM, consent, or acquire tokens. If a required application or permission
does not exist, record that gap and plan it separately with the identity owner.

1. In the Console, open **Identity & Security → Domains**, choose the intended
   domain, and inspect its **Domain information**. Record the Domain URL and
   confirm the domain and environment with its owner. Oracle documents this
   path in [Finding an Identity Domain URL](https://docs.oracle.com/en-us/iaas/Content/Identity/api-getstarted/locate-identity-domain-url.htm).
2. Use that verified domain's published OpenID discovery document for metadata
   review. Oracle documents the read-only
   [`GET /.well-known/openid-configuration`](https://docs.oracle.com/en/cloud/paas/iam-domains-rest-api/op-well-known-openid-configuration-get.html)
   endpoint. Record its `issuer` and `jwks_uri`; do not guess the signing-key
   URL or assume the Domain URL itself is the issuer. These scripts do not
   fetch discovery or JWKS, and this checklist does not authorize an agent to
   browse private accounts automatically.
3. Under the chosen domain's **Integrated applications**, inspect the existing
   application's OAuth/resource configuration with its owner. Distinguish the
   calling client's ID from the resource server's **Primary audience** and
   defined scopes. Oracle describes those fields in
   [Adding a Confidential Application](https://docs.oracle.com/en-us/iaas/Content/Identity/applications/add-confidential-application.htm);
   use the field definitions, not its creation workflow. Do not reveal or
   regenerate a client secret, click Save, or change allowed grants here.
4. Have the owner verify the actual access-token contract and the association
   between issuer, API audience, permitted clients, scopes, and public signing
   keys. Oracle's [OAuth validation guidance](https://docs.oracle.com/en-us/iaas/Content/Identity/api-getstarted/TokenValidation.htm)
   covers signature, issuer, audience, and token validation. Compare the
   contract with this adapter's narrower rules; record any mismatch.
5. Obtain only the reviewed public snapshot and non-secret configuration
   through the approved process. Record provenance and collection time in
   your private review notes. This document does not request a sample token,
   access to your console session, or an export of user credentials.

Passing the local checks below establishes neither a live Oracle connection
nor compatibility with your domain's emitted tokens. OCI API-signing keys
used by the CLI are also not your application's OAuth signing keys.

## 4. Run the synthetic lesson and explicit-file preflight

Use **CPython 3.12** and the same hash-locked optional dependencies installed
in [HTTP-LAB.md](HTTP-LAB.md#1-install-the-optional-dependencies). From the
repository root, activate that environment in its original terminal:

```sh
source "$LAB_ENV_DIR/venv/bin/activate"
python -B examples/local-backend/provider_demo.py
python -B -m unittest discover -s examples/local-backend/http-tests -v
```

The provider demo is in-process and uses only generated synthetic identities,
signatures, and data. It does not fetch metadata, issue provider tokens, start
a login flow, or connect to OCI. The full optional test suite also includes
the separate HTTP lab's temporary loopback tests.

For configuration review, supply **three exact existing files yourself**.
Replace every path below with your own absolute path outside the checkout;
these are placeholders, not files to search for on your machine:

```sh
python -B examples/local-backend/provider_preflight.py \
  --config /absolute/private/path/provider-config.json \
  --jwks /absolute/private/path/provider-public-jwks.json \
  --bindings /absolute/private/path/provider-bindings.json
```

The config object contains exactly the seven fields in the input table above
from `issuer` through `jwks_expires_at`; JWKS and bindings are separate files.
Each input must be a regular, non-symlink file no larger than 64 KiB. The
bindings file must deny group and other access: owner-only `0400` or `0600`
works on POSIX. Preflight does not find files automatically or fix permissions.

Success returns `status: configuration_valid` together with
`provider_connection_tested: false`, `token_verified: false`, and
`network_calls: 0`. Configuration failure returns `status: invalid_configuration`, the same
false/zero evidence fields, and exit code 2. Neither response echoes your
values. This CLI accepts no bearer-token input and does not validate a live
token, fetch keys, or prove that a mapped member exists in your application.

## 5. Rehearse rotation and revocation honestly

Snapshot reload is an explicit, local operation: validate a fresh reviewed
snapshot, swap the complete accepted key set atomically, and allow an approved
overlap interval when old and new public keys are both needed. Removing an old
key makes subsequent validations with that key fail. An invalid reload
disables verification rather than silently continuing with the old set;
an expired snapshot also fails closed. There is no background refresh, remote
key fetch, distributed synchronization, or automatic recovery mechanism.

This is **not provider-token revocation**. There is no introspection, logout
notification, stolen-token denylist, or session-revocation channel. Conversely,
the backend rechecks workspace membership and owner privileges on each call:
revoking membership still yields **403** for that workspace even while a token
remains cryptographically valid. Removing a subject binding rejects identity
admission; it is not a request to revoke the provider's token.

The required scope is one global API-admission gate. It does not implement
read/write scopes per route, replace tenant authorization, or grant an owner
role. Write down those missing requirements before connecting a real product.

## 6. Gate the production step

Before handling any real bearer credential, implement and review verified TLS
and an authentication bridge in your existing production framework. Never
attach a real provider to `http_lab.py`, tunnel its listener, or repurpose
`http.server` as production hosting. Keep tokens out of arguments, URLs, logs,
screenshots, and Git. Do not add a browser flow without its own review.

Remaining work includes provider-specific contract qualification, login and
callback/session protections, provisioning and binding lifecycle, operational
key rotation, revocation strategy, route-level permissions where needed,
rate limits, deployment secrets, and staging evidence. A successful offline
demo does not complete these tasks. Continue with the
[reference backend](../../docs/REFERENCE-BACKEND.md) and record results in the
[evidence guide](../../docs/EVIDENCE.md) before claiming a connected or
production-ready integration.
