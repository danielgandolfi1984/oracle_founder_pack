# Is OCI a good fit for your backend?

Use this guide to decide whether OCI deserves a small, reversible evaluation
for your product. The useful outcome is a supported decision, including
"not yet" when a requirement is unresolved. This toolkit does not establish
that OCI is universally cheaper, faster, or simpler than another cloud.

Public Oracle sources checked on **2026-09-19**. This is a decision framework,
not a benchmark, price quote, or Oracle endorsement of this personal project.

## Start with the product, not a service name

Write down the first customer action your backend must support, the data it
touches, where its users are, and what failure would mean. Keep the current
database and identity provider unless there is evidence to change them.

For a concrete design exercise, use the [reference backend](REFERENCE-BACKEND.md):
an authenticated user creates a work item and attaches a private file within
their organization. It is a proposed design, not a deployed sample application.

| Your requirement | OCI path worth evaluating | What still needs proof |
|---|---|---|
| Learn Linux, networking and direct VM access | [Compute and the first-VM lab](FIRST-VM.md) | Your team's ability to operate and patch the OS, restore data and limit exposure |
| Run a persistent containerized API without requiring Kubernetes | [Container Instances](https://docs.oracle.com/en-us/iaas/Content/container-instances/overview-of-container-instances.htm) | Application contract, ingress, identity, logs, failure recovery and measured capacity |
| Run handlers on calls or events | [OCI Functions](https://docs.oracle.com/en-us/iaas/Content/Functions/Concepts/functionsoverview.htm) | Handler compatibility, execution limits, latency and downstream connections |
| Serve users near an OCI region | [Region assessment](GETTING-STARTED.md#3-choose-the-region-for-your-users-not-this-example) | End-to-end latency from actual user locations, required services and available account capacity |
| Preserve an existing application or database investment | A staged application evaluation with the current data layer | Driver behavior, cross-cloud connectivity, transfer cost, recovery and migration effort |

The service links describe Oracle capabilities. They are not evidence that this
toolkit has exercised them in your account. The Container API implementation is
a separate [sandbox preview](../blueprints/container-api/README.md), with narrower
capabilities than the reference backend.

## A fair comparison with your current option

Compare the same workload and service objective. Use the current cloud as the
baseline when it already runs the product; for a new product, document the
candidate baseline instead of inventing historical results.

| Decision | Evidence to collect for each candidate | Example reason to pause |
|---|---|---|
| Total cost | Same currency and period, complete [cost worksheet](COST-SCENARIOS.md), operator effort and migration cost | A low runtime price excludes the database, network or support requirement |
| Performance | Same application revision, payloads, dataset, request mix, test duration and concurrency; record CPU architecture, memory, p50/p95 latency, throughput and errors | Comparing different hardware or only a health endpoint |
| Operational effort | Time to diagnose one failure, ship a change, restore data and remove the environment; record manual steps | Only one maintainer can recover the system |
| Runtime and data fit | Test drivers, extensions, filesystem assumptions, background work, request limits and dependencies | A required behavior has no tested substitute |
| Location and recovery | Region/service support, measured access latency, backup/restore path and customer requirements | Assuming proximity alone proves availability or compliance |
| Safety and support | Tenant isolation, credential handling, patching, incident ownership and actual support entitlement | A public sandbox is being presented as a supported customer environment |

Set required thresholds **before** testing, including the maximum cost you are
willing to authorize. A failed must-have requirement cannot be averaged away
with a favorable score elsewhere. The [Oracle cost estimator](https://www.oracle.com/cloud/costestimator.html)
can help assemble a scenario; it does not replace workload measurements or
your applicable commercial terms.

## What a useful evaluation delivers

1. One candidate architecture and the reasons it fits this particular product.
2. A list of assumptions, missing evidence and conditions that would reverse
   the recommendation.
3. A costed, bounded experiment with an owner, expiry and explicit approval
   before any resource creation or paid commitment.
4. Test results recorded using the [evidence guide](EVIDENCE.md), including
   failures, retained resources and costs not yet visible in billing.
5. A decision: proceed to the next gate, revise the design, or stay with the
   current option. Include the cost of reversing the decision.

For a migration, start with synthetic data and isolated traffic. Moving customer
data, changing DNS, enabling paid services or cutting production traffic over
requires a separate reviewed plan and approval. Do not deploy two production
environments merely to fill in a comparison table.

## The decision record

Keep the working record private if it contains account or customer context.
Publish only reviewed, redacted evidence:

```text
Product action and target users:
Current baseline and candidate:
Must-have requirements and thresholds:
Sources and date checked:
Measured results and exact revision:
Assumptions and untested behavior:
Estimated cost / observed cost / still unknown:
Operational owner and support route:
Decision and reason:
What would change the decision:
Next step, expiry, rollback and cleanup:
```

Ask the skill:

```text
Use the oci-founder skill. Help me decide whether OCI fits this backend.
Start from the repository and these product requirements: [requirements].
Compare with [current architecture or candidate baseline]. Preserve my data
and identity choices unless evidence supports a change. Identify must-have
tests, full cost drivers and reasons not to migrate yet. Label assumptions.
Give me one recommendation and one next experiment. Planning only: do not
use credentials, create files, run cloud commands or change resources.
```

Next: [choose your founder route](GETTING-STARTED.md), then check
[what has actually been validated](EVIDENCE.md).
