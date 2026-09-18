# Contributing

Founder Toolkit for OCI is an independent personal project maintained by
Daniel Gandolfi and licensed under the [UPL-1.0](LICENSE). It is not an Oracle
project. Contributions are welcome through GitHub issues and pull requests.

By submitting a contribution, you represent that you have the right to submit
it and agree that it is provided under the UPL-1.0. Do not submit Oracle- or
third-party-confidential material, customer information, credentials, private
OCIDs, Terraform state, or content you are not authorized to publish.

Contributions should improve the founder journey without creating a second
Oracle service manual.

## Where a change belongs

Contribute here when the change is primarily:

- a founder journey or decision;
- an AWS/GCP/Azure translation;
- a blueprint coupling several OCI services;
- a toolkit guardrail, artifact contract, adapter, or evaluation.

Contribute to [`oracle/skills`](https://github.com/oracle/skills) when it is a
reusable fact or procedure about an Oracle service that can stand alone.
Reference the upstream result here after it is reviewed.

## Change requirements

- Link consequential OCI claims to official Oracle sources.
- Mark time-sensitive facts and validate them at task time.
- Preserve the read-only → generate → write → destructive authorization model.
- Never add credentials, secret values, real customer identifiers, private
  OCIDs, confidential employer material, or Terraform state.
- Add a behavioral prompt case when routing or safety behavior changes.
- Keep the three plugin manifests on the same version.
- Update the upstream lock only after inspecting the relevant diff.
- Keep the Oracle-template presentation and every other internal working
  artifact outside public commits and packages.

## Validation

```bash
python3 scripts/validate.py
```

Also run the host-native plugin validators available in your environment and
test a changed skill in a fresh session.

## Pull request evidence

Describe:

1. the founder problem;
2. why the change belongs here rather than upstream;
3. official sources used;
4. prompts tested in each supported host;
5. safety and cost impact; and
6. apply, verify, rollback, and teardown evidence for executable assets.

The maintainer may decline changes that increase support or security burden,
duplicate an upstream Oracle skill, or blur the independent-project boundary.
