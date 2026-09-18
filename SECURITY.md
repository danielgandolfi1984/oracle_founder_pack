# Security policy

Founder Toolkit for OCI is an independent personal open-source project, not an
Oracle product. Security reports are handled by Daniel Gandolfi, the project
maintainer, on a best-effort basis and are not covered by Oracle Support or an
Oracle response SLA.

## Reporting a vulnerability

Use the repository's
[private vulnerability reporting](https://github.com/danielgandolfi1984/oracle_founder_pack/security/advisories/new)
for a suspected vulnerability. Do not open a public issue containing exploit
details, credentials, private keys, auth tokens, customer information, private
OCIDs, Terraform state, or other sensitive evidence.

Include the affected version, impact, reproduction steps, and a minimal
redacted proof of concept. The maintainer will acknowledge and triage reports
as availability permits; no response or remediation time is guaranteed.

## Supported versions

Only the latest published `0.1.x` release is eligible for best-effort security
fixes. Source snapshots, prerelease blueprints, older releases, and unmodified
third-party dependencies may be out of scope.

## Safety boundary

- Read-only assessment and planning are the defaults.
- OCI writes, IAM changes, apply, and destroy require an exact preview and
  explicit approval immediately before the mutation.
- Destructive scope must come from reviewed state and deployment receipts, not
  broad compartment, tag, wildcard, or name-prefix selection.
- Secrets belong in an approved secret manager and must not be copied into
  source, examples, images, Terraform variables/state, logs, or receipts.
- The Container API path is sandbox-only and has not been exercised in an OCI
  tenancy by this project.

The repository's checks are defense-in-depth, not a substitute for a security
review of a user's application or OCI environment. See
[docs/RELEASING.md](docs/RELEASING.md) for the remaining qualification gates.
