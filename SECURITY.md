# Security status

OCI Founder Toolkit is an unlicensed evaluation draft, not a supported public
product. It has no approved public security contact or vulnerability-response
SLA. That missing ownership is a public-release blocker, not a field to invent.

Authorized Oracle reviewers should report suspected vulnerabilities through an
approved internal Oracle security channel and must not include credentials,
private keys, tokens, customer identifiers, private OCIDs, Terraform state, or
secret values in an issue or repository artifact.

## Evaluation safety boundary

- Read-only assessment and local generation are the defaults.
- OCI writes, IAM changes, apply, and destroy require an exact preview and
  explicit approval immediately before the mutation.
- Destructive scope must come from reviewed state and deployment receipts, not
  broad compartment, tag, wildcard, or name-prefix selection.
- Secrets belong in an approved secret manager and must not be copied into
  source, examples, images, Terraform variables/state, logs, or receipts.
- The Container API path is sandbox-only and has not been exercised in an OCI
  tenancy.

The repository's checks are defense-in-depth, not a substitute for Oracle's
formal security review. See [`docs/RELEASING.md`](docs/RELEASING.md) for the
remaining public-release gates.
