# Contributing

This is currently an unlicensed evaluation draft. Contributions are limited to
authorized collaborators until a public license and contribution process are
approved. See [`LICENSE`](LICENSE).

Contributions should improve the founder journey without creating a second Oracle service manual.

## Where a change belongs

Contribute here when the change is primarily:

- a founder journey or decision;
- an AWS/GCP/Azure translation;
- a blueprint coupling several OCI services;
- a toolkit guardrail, artifact contract, adapter, or evaluation.

Contribute to [`oracle/skills`](https://github.com/oracle/skills) when it is a reusable fact or procedure about an Oracle service that can stand alone. Reference the upstream result here after it is reviewed.

## Change requirements

- Link consequential OCI claims to official Oracle sources.
- Mark time-sensitive facts and validate them at task time.
- Preserve the read-only → generate → write → destructive authorization model.
- Never add credentials, secret values, real customer identifiers, private OCIDs, or Terraform state.
- Add a behavioral prompt case when routing or safety behavior changes.
- Keep the three plugin manifests on the same version.
- Update the upstream lock only after inspecting the relevant diff.

## Validation

```bash
python3 scripts/validate.py
```

Also run the host-native plugin validators available in your environment and test the changed skill in a fresh session.

## Pull request evidence

Describe:

1. the founder problem;
2. why the change belongs here rather than upstream;
3. official sources used;
4. prompts tested in each supported host;
5. safety and cost impact;
6. apply/verify/rollback/teardown evidence for executable assets.
