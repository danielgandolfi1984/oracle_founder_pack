# Fix an offline identity configuration

Use this guide when the [identity preflight](IDENTITY-INTEGRATION.md) returns
`invalid_configuration`. It helps you correct local inputs; it does not test
login, contact a provider, or change IAM. Available in the source checkout on
`main`, not in the released skill archives.

## Ask for safe diagnostics

From the repository root, use the optional Python environment described in
[the setup guide](HTTP-LAB.md#1-install-the-optional-dependencies). Replace the
three placeholders with exact existing files outside the checkout:

```sh
"$LAB_ENV_DIR/venv/bin/python" -B examples/local-backend/provider_preflight.py \
  --config /absolute/private/path/provider-config.json \
  --jwks /absolute/private/path/provider-public-jwks.json \
  --bindings /absolute/private/path/provider-bindings.json \
  --diagnostics
```

The optional flag adds a `diagnostics` array without displaying paths, issuer
URLs, client IDs, subjects, key material or input contents. The default output
without the flag remains unchanged. Success has an empty array. Failure exits
with code **2** and reports the first detected problem, for example:

```json
{
  "status": "invalid_configuration",
  "diagnostics": [{"input": "config", "code": "invalid_time_policy"}],
  "provider_connection_tested": false,
  "token_verified": false,
  "network_calls": 0
}
```

The input label is only `config`, `jwks`, `bindings`, or `snapshot` (the combined
trusted configuration). Fix and rerun locally; one error code does not mean the
other inputs passed. Invalid command arguments still produce a fixed message
and exit 2, without echoing the arguments. No token input is accepted.

## What to check next

| Diagnostic code | Safe next check |
|---|---|
| `input_file_unavailable` | Verify the exact supplied file exists and is readable by your current account. The script does not search for credentials or repair access |
| `input_file_type` | Use an ordinary file, not a directory, named pipe or final symbolic link |
| `input_file_too_large` | Check the 64 KiB per-file limit. Do not truncate keys or remove security metadata merely to pass |
| `input_permissions` | The bindings file permits group/other access. Review its location and owner-only permissions yourself; the script does not run chmod |
| `invalid_json` | Use a UTF-8 JSON object with unique property names; no comments, trailing commas, NaN or Infinity |
| `invalid_config_fields` | Compare the config's exact seven field names with the [input table](IDENTITY-INTEGRATION.md#2-collect-configuration-not-credentials); do not add a token or secret |
| `invalid_issuer` | Review the HTTPS issuer's syntax, including absence of credentials, query and fragment. Do not guess it from the Console URL or an unverified token |
| `invalid_audience` | Use one nonempty printable-ASCII string, at most 512 characters, for this lab's API audience |
| `invalid_client_allowlist` | Use 1–16 distinct client identifiers as strings, each at most 256 printable-ASCII characters; never secrets |
| `invalid_required_scope` | Use one exact scope token, at most 128 characters, not a space-separated list. The admission scope does not grant workspace roles |
| `invalid_time_policy` | Check integer epoch seconds, actual acquisition time, expiry, a snapshot window at most one hour, and a maximum token lifetime of 1–3600 seconds. Obtain a fresh trusted snapshot if stale; do not re-date old keys |
| `invalid_public_jwks` | Compare key count, unique IDs, public RSA material and supported metadata with the [JWKS constraints](IDENTITY-INTEGRATION.md#2-collect-configuration-not-credentials). Do not strip fields automatically or add private keys |
| `invalid_subject_bindings` | Check explicit external-subject → local-member pairs, one-to-one mapping and the 1000-entry limit. Do not substitute email, client name or a seeded demo owner |
| `invalid_clock` | Review system time/monotonic-clock health; do not disable expiry checks. This tool never adjusts your system clock |
| `invalid_snapshot` | Validation could not complete safely or readiness changed. Rerun after reviewing the local inputs/runtime; stop if it persists. Do not bypass the verifier |

These codes classify **configuration**, not a bearer token. A valid preflight
does not establish key provenance, member existence, correct provider values,
or token acceptance. It also does not mean the HTTP lab's `/readyz` validates
identity configuration; that endpoint still checks only the database.

## Check provider compatibility before attempting login

Public Oracle sources reviewed **2026-09-21** show why a provider-specific
qualification step is needed. This is a comparison with the educational
adapter, not a claim about the configuration of your domain:

| Contract item | Documented consideration | This lab accepts |
|---|---|---|
| Access-token type | A [legacy Oracle access-token example](https://docs.oracle.com/en/cloud/get-started/subscriptions-cloud/csimg/obtaining-access-token-using-client-authorization-header.html) uses `typ: JWT`; it is not evidence that every current domain does | Only `at+jwt` or `application/at+jwt`. A generic JWT access token can be valid under another profile and still be incompatible here; `JWT` alone does not identify an ID token |
| Audience shape | Oracle's [access-token validation guidance](https://docs.oracle.com/en-us/iaas/Content/Identity/api-getstarted/TokenValidation.htm) permits string or array, depending on configured audiences | Exactly one string; arrays are rejected, even with one matching entry |
| Public-key metadata | The [Signing Certificates JWK endpoint](https://docs.oracle.com/en/cloud/paas/iam-domains-rest-api/api-security-signing-certificates-jwk.html) documents the certificate-chain field `x5c` | A narrow public RSA field set that excludes `x5c`; direct ingestion may therefore fail |
| Client and subject | Oracle's [access-token contract](https://docs.oracle.com/en-us/iaas/Content/Identity/api-getstarted/AccessToken.htm) distinguishes OAuth client ID, client name, and user/client subjects | An explicit client-ID allowlist and subject bindings. No automatic name conversion, user provisioning or role grants |

Do not alter signed tokens, rename claims, discard audiences or weaken
validation to make these differences disappear. A provider-specific adapter
would require its own reviewed trust rules and tests. The current verifier is
not that adapter, and this comparison does not authorize fetching a real token.

## Prepare the first connected test

Record these decisions privately with the application/identity owner. No
password, client secret, bearer token or private key belongs in this worksheet:

- **Provider and purpose:** existing identity provider or OCI Identity Domains;
  human sign-in versus machine-to-machine API access. A machine-token test does
  not establish a human login journey.
- **Target:** existing authorized test application, resource API, environment,
  owner, and exact issuer/audience/client/scope contract.
- **Compatibility:** review the four rows above and the lab's time, signature
  and key constraints; document mismatches before choosing an adapter.
- **Execution boundary:** separately reviewed production-framework/TLS bridge,
  private token handling, exact read-only checks, and explicit approval for any
  application registration, permissions or resource changes.
- **Evidence:** accepted authorized request, rejection cases, current tenant
  authorization after revocation, key lifecycle behavior, cleanup and limits.
  Keep raw evidence private and publish only a reviewed, redacted summary.

Until those decisions are made and the missing integration is implemented,
continue with the synthetic demo. Do not attach a real provider to
`http_lab.py`. See the [reference backend](../../docs/REFERENCE-BACKEND.md) for
the remaining implementation gates.
