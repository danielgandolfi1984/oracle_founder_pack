---
name: oci-founder-start
description: Help a founder or developer new to OCI plan their first project, account readiness, safe agent access, and a minimal VM or backend architecture. Use for greenfield onboarding and first-VM/VCN questions; return a read-only plan, not deployment or migration execution.
license: UPL-1.0
metadata:
  author: Daniel Gandolfi
  version: "0.1.0"
  status: preview
---

# Start a project on OCI

Help the user leave with a small first milestone, the Console information they
need, and a safe next action. This standalone preview is an independent personal
project by Daniel Gandolfi, not an Oracle product, endorsement or support service.
It needs no other skill, repository files or cloud account to produce a plan.
See [LICENSE](LICENSE).

## Meet the beginner where they are

Answer in the user's language, including English or Portuguese, keeping official
service names. Explain unfamiliar terms when first used. A beginner's short
prompt is enough: give a useful provisional path, not a long questionnaire.
Ask only what can change the next decision; label everything else as an
assumption or not yet checked. Do not invent a stack, region or free entitlement.
For a focused question, answer that question rather than imposing a full plan.

Examples the user can ask in any coding agent:

- English: "I have never used OCI. Help me plan my first development VM and network. Do not create anything."
- Português: "Nunca usei OCI. Quero começar meu backend e entender conta, VCN e VM. Faça só o plano, sem criar recursos."

## Choose one small first milestone

Use the stated goal, existing stack and operational preferences. If a repository
is in scope, inspect only relevant source/build/deployment files read-only; do
not run its scripts or read credentials, environment values, private keys or
Terraform state. Otherwise plan from the user's description without requiring
a repository.

- For learning a VM or needing OS control, propose a Compute development VM and explain that patching and host operations remain the user's responsibility.
- For an existing persistent containerized backend, evaluate Container Instances before assuming the user needs a VM or Kubernetes. Check lifecycle, ingress and scaling needs; do not promise Cloud Run/Fargate equivalence.
- For a function-compatible event/request handler, evaluate Functions. Do not convert an ordinary server into a function by renaming it.
- Preserve a chosen database and runtime unless evidence shows a blocker. Kubernetes or a new database engine is not an onboarding prerequisite.

For a VM milestone, identify the proposed region, non-root project compartment,
VCN/subnet, traffic source, administrative access path, OS/CPU-architecture fit,
shape sizing assumptions and storage. Reuse suitable resources when their scope
is known. Plan only required network access: no public database or unrestricted
SSH by default. A private VM also needs a deliberate management and outbound
access path; "private" is not a complete connectivity design.

## Account and agent readiness without secrets

Keep a short readiness list with **confirmed**, **missing** or **not checked**;
never infer access from the fact that the user can sign in to the Console.

| Needed context | Where the user can inspect it | What the agent actually needs |
|---|---|---|
| Tenancy | Console profile menu, then tenancy details | Confirm the intended account; keep its OCID local when required by a configured tool |
| Target region | Console region selector | Region identifier and whether required services/capacity have been checked |
| Project compartment | Compartments page and the chosen compartment's details | Non-root target and whether the user has appropriate scoped access |
| Existing VCN/subnet or VM | Its Console details in the chosen region/compartment | Intended network/exposure and resource references, not a full tenancy export |
| Local agent authentication | User's existing OCI CLI/SDK setup, if any | Profile alias and authentication method/status, not the configuration file contents |
| API-key method only | Intended user's details and API Keys page | Confirm user OCID and public-key fingerprint in the local configuration; never disclose the private key |

An OCID is a resource identifier, not a password, but account metadata need not
be posted publicly. Distinguish Console login, OCI API authentication and VM SSH:
they are different access paths. For API-key authentication, explain that the
public signing key is registered with the intended user and the private key
stays protected locally; this is not an SSH key or a bearer auth token. Use the
current official authentication guide for the selected method, not remembered
setup commands. Do not read or print a credential file, copy keys into chat, or
ask the user to paste a token. Missing authentication is a prerequisite, not
permission to create keys, install tools or grant IAM access.

## Return a small, checkable plan

Normally give a short recommendation, the relevant readiness gaps, and one first
proof to run later. For a requested full starting plan, also identify:

- Prerequisites and the smallest architecture, separating observed facts from assumptions.
- A proposed success check: intended endpoint or administrative access, actual readiness, expected network denials, and where logs/metrics would be inspected.
- Cost drivers, owner/environment tags, budget alert and practical resource limits. A budget is an alert, not a hard spending cap; prices and free capacity remain unverified until checked.
- Rollback and cleanup scope, including retained volumes, backups and addresses. Stopping a VM is not evidence that every charge stops.

End with one concrete **read-only next action**. A proposed design is not a
deployment, an endpoint response is not production readiness, and this skill
does not promise zero cost, availability or a completion time.

## Boundaries and handoff

This skill does not edit files, install dependencies, generate credentials or
execute cloud changes. Read-only account inspection is optional and requires
the user to place that account/region/compartment in scope; never probe another
profile automatically. For implementation, explain the handoff and the exact
target/change review needed before any IAM, network, budget, quota or resource
mutation. Never propose broad administrator permissions as a shortcut.

Keep reusable service procedures in the official `oracle/skills` project.
Reference an installed official skill only if its availability and reviewed
provenance are known; do not install it automatically or reconstruct its missing
procedures. This planning skill remains useful when no such skill is installed.
Verify current official Oracle sources for service behavior, Console locations,
region availability, quotas and pricing; if unavailable, mark the claim unverified.
Never publish internal-only Oracle material as a source for this public skill.

## Sources

- [Oracle resource identifiers and tenancy details](https://docs.oracle.com/en-us/iaas/Content/General/Concepts/identifiers.htm)
- [Compartments](https://docs.oracle.com/en-us/iaas/Content/Identity/compartments/Working_with_Compartments.htm)
- [VCN and connectivity concepts](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/overview.htm)
- [Compute instances](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/instances.htm)
- [CLI/SDK configuration](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm) and [API signing keys](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/apisigningkey.htm)
- [Container Instances](https://docs.oracle.com/en-us/iaas/Content/container-instances/overview-of-container-instances.htm) and [Functions](https://docs.oracle.com/en-us/iaas/Content/Functions/Concepts/functionsoverview.htm)
- [Budget behavior](https://docs.oracle.com/en-us/iaas/Content/Billing/Concepts/budgetsoverview.htm)
- [Official Oracle skills](https://github.com/oracle/skills)
