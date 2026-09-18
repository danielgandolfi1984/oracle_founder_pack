# Bootstrap stack

This is the privileged, infrequent half of the [Container API field preview](../../README.md). It creates an immutable private OCIR repository, a dedicated-compartment Container Instance dynamic group, a repository-name-scoped pull policy, and an alert-only compartment budget after an explicit no-existing-budget preflight.

Use a tenancy administrator profile only for this stack. Keep its state and approval separate from runtime. The stack does not create a compartment, user, group, API key, or routine deployer policy.
