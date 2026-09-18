# Toolkit architecture

## Design goal

Keep one portable founder workflow while allowing OCI facts and each coding-agent platform to evolve independently.

```text
Codex / Cursor / Claude Code
            |
     thin host manifest
            |
   portable oci-founder skill
            |
   founder journey orchestration
      /          |          \
oracle/skills  official OCI  toolkit blueprints
  upstream        docs       and contracts
            \     |     /
        preview -> approval -> OCI
```

The core skill can plan without credentials. Future executable layers remain explicit and independently testable.

## Layers

### 1. Portable skill core

`skills/oci-founder/` is the single source for agent instructions and references. It uses the common Agent Skills format and avoids host-specific frontmatter or invocation syntax.

The skill owns:

- journey detection and sequencing;
- repository discovery;
- cross-cloud translation;
- architecture selection;
- founder guardrails;
- routing to upstream skills.

### 2. Oracle knowledge upstream

`oracle/skills` owns reusable Oracle service procedures. A release reviews and pins an immutable upstream commit in `upstream/oracle-skills.lock.json`.

The source repository does not modify or silently vendor upstream files. A future release bundle may materialize selected paths, but must preserve the license, provenance, and checksums.

### 3. Official documentation

Time-sensitive claims are checked against Oracle documentation at task time, especially:

- pricing and promotions;
- region and service availability;
- quotas and service limits;
- IAM verbs and policy syntax;
- CLI, SDK, and API behavior;
- model and shape availability.

A pinned skill provides reviewed defaults, not permission to repeat stale facts.

### 4. Blueprints

The first candidate is the sandbox-only
[`Container API field preview`](../blueprints/container-api/README.md). It keeps
tenancy-level bootstrap authority and routine runtime authority in separate
Terraform roots and state. The Function API remains future work. Every stable
blueprint must contain infrastructure, policy intent, observability, tests,
rollback, and teardown as one unit.

Terraform is the canonical IaC format. The current Container API blueprint is a
local Terraform `1.16.3` path; it is not OCI Resource Manager compatible because
the currently documented Resource Manager operational line is `1.5.x`. Any
Resource Manager execution path must be a separately tested version-compatible
variant. Generated state is sensitive and never belongs in the repository.

### 5. Read-only context plugin

A future `oci-founder-context` MCP/plugin will reduce onboarding friction with read-only tools such as:

- current profile and identity inspection;
- region and compartment resolution;
- service-limit checks;
- resource inventory;
- log and cost queries;
- Terraform validation and plan summarization.

The MVP will not expose `apply`, resource mutation, IAM mutation, secret retrieval, or destroy as plugin tools. Those operations remain explicit shell/CI actions behind preview and approval.

### 6. Host adapters

| Host | Adapter | Purpose |
|---|---|---|
| Agent Plugins-compatible hosts and Cursor | root `plugin.json` | Portable skill discovery |
| Codex | `.codex-plugin/plugin.json` | Codex compatibility and presentation metadata |
| Claude Code | `.claude-plugin/plugin.json` | Native Claude plugin discovery |
| Codex and Cursor repository instructions | `AGENTS.md` | Contributor and safety rules |
| Claude Code repository instructions | `CLAUDE.md` | Imports the canonical `AGENTS.md` |

Host-specific hooks, subagents, rules, or UI are optional adapters. They must not fork the workflow or weaken its safety model.

## Execution contract

The journey has four authorization levels:

1. **Read-only:** inspect code, configuration names, resource metadata, logs, metrics, and limits.
2. **Generate:** write a plan, Terraform, policy proposal, or commands without applying them.
3. **Write:** change IAM or cloud resources after an exact preview and explicit approval.
4. **Destructive:** delete, revoke, rotate, or destroy exact resolved targets after a separate impact preview and explicit approval.

Authorization does not flow automatically from one level to the next.

## Artifact contracts

### Founder plan

Produced before implementation. It records repository evidence, chosen path, alternatives, identity/network/data design, cost drivers, approval gates, verification, teardown, and sources.

### Terraform plan summary

Produced before apply. For the Container API preview, the helper decodes the
exact saved plan through read-only `terraform show -json`, accepts only the
blueprint's complete resource/output graph, verifies plan variables and exact
provider region/profile bindings against the asserted target, checks critical security relationships,
omits raw values, and binds approval to target, binary-plan, rendered-plan, and
reviewed Terraform-source hashes plus the bootstrap receipt hash. It compares
the exact root configuration snapshot and provider lock embedded inside the
saved plan with the reviewed local stack before emitting that approval. Known concrete
relationship values are compared with the planned graph before apply; unknown
create-time IDs are checked again against the applied state. It calls out creates, in-place changes, replacements,
deletes, public exposure, data impact, and directional cost drivers.

### Deployment receipt

Produced after verification. It records IaC/code revisions, resource
identifiers, image digests, endpoints, URL-bound smoke-test evidence, alarm
path, bootstrap lineage, rollback, and the exact managed-resource teardown
scope. A single raw state snapshot supplies lineage, serial, outputs, addresses,
and address-to-OCID ownership, without emitting arbitrary state values. It never
contains credentials. Preview receipts are marked `locally_verified`; they are
local evidence, not signed attestations.

The bootstrap receipt derives its OCIR path from the reviewed registry endpoint
and the repository namespace/display name in state. Runtime state verification
compares security-critical relationship OCIDs with the IDs in the same state
graph, not only with expected resource addresses. That comparison includes API
Gateway logs, their deployment/log-group bindings, the notification subscription,
and alarm destinations and queries.

Bootstrap teardown additionally requires a fresh local readback artifact with
authenticated, read-only `not_found` results for every exact runtime receipt
OCID, including the child container and VNIC identifiers exposed as receipt
outputs even though they are not independent Terraform addresses. The audit binds it to the runtime receipt hash and post-destroy state
lineage/serial and includes its hash in the approval phrase. Its OCI GET producer
is still a trusted operator/verifier boundary in this preview.

## Upstream update flow

1. Detect a new `oracle/skills` commit.
2. Diff only the allowlisted paths used by the toolkit.
3. Classify effects on founder journeys, IAM, commands, and mutation behavior.
4. Run repository validation and cross-agent behavioral evaluations.
5. Require human review for every lock update.
6. Publish the new toolkit version with updated provenance.

No automatic merge is allowed for changed IAM, deployment, or destructive-operation guidance.

## Versioning

- Plugin manifests and skill metadata share one toolkit version.
- The toolkit version changes when founder behavior or packaging changes.
- The upstream Oracle Skills commit is tracked separately and immutably.
- A release notes whether upstream changes alter any journey or only supporting references.

## Sources

- https://github.com/oracle/skills
- https://agentskills.io/specification
- https://agent-plugins.org/specification
- https://learn.chatgpt.com/docs/build-skills
- https://learn.chatgpt.com/docs/build-plugins
- https://code.claude.com/docs/en/plugins-reference
- https://cursor.com/docs/reference/plugins
- https://docs.oracle.com/en-us/iaas/Content/dev/terraform/home.htm
- https://docs.oracle.com/en-us/iaas/Content/ResourceManager/Reference/terraformversions.htm
