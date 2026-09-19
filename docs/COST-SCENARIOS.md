# What will my backend cost?

Use this worksheet with the [reference backend](REFERENCE-BACKEND.md) and
[Founder Baseline](FOUNDER-BASELINE.md). It turns a product idea into measurable
cost inputs, not a quote or an assurance that a particular shape supports a
number of customers. No resources or paid load tests were run for these examples.
The [evidence guide](EVIDENCE.md) separates proposed, tested, and observed results.

**Status: UNPRICED.** All monetary unit rates, cloud totals, and total cost of
ownership (TCO) remain unknown until the target region, service configuration,
billing currency, dated price source, and commercial terms are recorded. An
unknown is never zero. Source documentation was checked on **2026-09-19**;
that date is not a rate-card validation or an estimate expiry date.

## 1. Start with your product, not a monthly price promise

Write down your API's peak requests per second, payload sizes, request duration,
database behavior, background jobs, availability objective, and recovery needs.
Monthly request totals alone do not size a backend. Replace the illustrative
inputs below with measurements before approving a deployment.

| Hypothetical input for a 30-day planning month | Prototype | First paying customers | Growth experiment |
|---|---:|---:|---:|
| Paying customer accounts, used only as a cost denominator | 0 | 20 | 200 |
| API requests in the month | 10,000 | 300,000 | 3,000,000 |
| Runtime replicas | 1 | 1 | 3 |
| Active hours per replica | 160 | 720 | 720 |
| OCPUs / memory GB per replica | 2 / 8 | 2 / 8 | 4 / 16 |
| Average objects retained, GB | 5 | 50 | 500 |
| Outbound internet traffic, GB before billing rules | 10 | 100 | 1,000 |
| Logs ingested, GB per day / retention days | 0.1 / 7 | 1 / 14 | 5 / 30 |
| Logical database data, GB; not allocated storage | 1 | 10 | 100 |
| Average retained backup data, GB; hypothetical only | 5 | 50 | 500 |
| Operations and maintenance hours in the month | 8 | 16 | 40 |
| Cloud subtotal / full TCO | UNPRICED | UNPRICED | UNPRICED |

These columns are independent planning exercises, not a scaling rule, production
recommendation, or an implemented replica topology in the current blueprint.
They exclude no component by implication: database sizing, boot/block volumes,
front door, non-production environments, and other items still need the worksheet
below. No scenario is certified for its customer count or availability objective.

## 2. Work the units before the money

For the illustrative runtime, count CPU and memory separately:

```text
OCPU-hours      = replicas × OCPUs per replica × billable hours per replica
memory GB-hours = replicas × memory GB per replica × billable hours per replica

Prototype: 1 × 2 × 160 = 320 OCPU-hours; 1 × 8 × 160 = 1,280 GB-hours
First customers: 1 × 2 × 720 = 1,440; 1 × 8 × 720 = 5,760
Growth experiment: 3 × 4 × 720 = 8,640; 3 × 16 × 720 = 34,560

First-customer logs: 1 GB/day × 30 days = 30 GB ingested
14-day retention: approximately 14 GB retained at steady state, before overhead
```

The runtime arithmetic assumes billable compute hours equal active hours for
the selected service and shape; **verify that assumption**. VM stop behavior
depends on shape and associated storage can continue to incur charges.
[Oracle: billing for stopped instances](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/resource-billing-stopped-instances.htm).

Use the exact SKU's CPU, memory, storage, time, and request units; do not substitute
vCPU-hours for OCPU-hours or logical data size for allocated capacity. Keep GB
versus GiB and the billing month's duration explicit. CPU/memory meters and other
service meters are listed in the [OCI price list](https://www.oracle.com/cloud/price-list/).
An ingestion quantity or retention estimate is not automatically a billable SKU.

## 3. Fill every line, including the less visible ones

For each row record: `scenario | service/SKU | region | quantity | billing unit |
unit rate | currency | official source/contract reference | checked-at | valid-until |
commercial terms | subtotal`. Start every unit rate and subtotal as **UNPRICED**.
Use `not applicable` only with a documented architecture reason; record zero only
after verifying the applicable terms. Keep private contract details out of Git.

| Cost line | Quantity and decision to capture before pricing |
|---|---|
| Runtime CPU and memory | Separate OCPU-hours and memory GB-hours; architecture, shape, billing minimums, scale-out ceiling, image/license charges |
| Boot/block volumes | Allocated capacity over time, performance level/units, detached volumes; not just application data used |
| Database | Engine, license model, compute and allocated storage, HA/replicas, scaling limits, I/O and backup meters; logical GB alone cannot price it |
| Object storage | Average retained capacity, storage class, requests, retrieval, retention constraints, versions and replication |
| Network/egress | Traffic source/destination and path, billable outbound quantity after verified tiers/allowances; gateway and public-IP meters if applicable |
| Front door | Gateway requests or load-balancer hours/capacity, TLS/WAF and associated traffic; do not double-count transferred data |
| Logs and monitoring | Ingestion, retained/archive data, metric/notification usage and selected service meters |
| Backups and recovery | Changed/retained data, retention, cross-region copies, restore tests and temporary restore infrastructure |
| Registry and delivery | Image versions/storage, scanning, CI runners/build minutes and deployment artifacts |
| Identity, secrets, dependencies | Selected identity, Secret Management and key-management meters plus email, payments, external APIs or AI usage if the product uses them |
| Domain and DNS | Registrar purchase/renewal quote, DNS queries/zones; allocate annual fees to the planning period |
| Support and software | Included entitlement versus any separately contracted support, third-party licenses and paid tools; never assume an added percentage |
| Human operations | Engineering, patching, incidents, backups and support hours × a founder-supplied loaded hourly rate |
| Commercial adjustments | Applicable discount/commitment, expiring credit, unused commitment, currency conversion/fees, taxes and payment timing |
| Extra environments | Development, staging, preview deployments, migration overlap and disaster-recovery resources |

Use the [Oracle Cost Estimator](https://www.oracle.com/cloud/costestimator.html)
and save the dated configuration/export alongside your private estimate. It is
an evaluation tool, not an official quote. The Console's estimate for one
resource may omit related services; do not treat it as the whole application
bill. [Oracle: estimating monthly costs](https://docs.oracle.com/en-us/iaas/Content/Billing/Tasks/signingup_topic-Estimating_Costs.htm).

Confirm account-specific support access and your contract before pricing support;
community help and this personal project are not an incident-response contract.
[Oracle support options](https://www.oracle.com/support/support-options.html).

## 4. Calculate the decision, not just the infrastructure bill

```text
Cloud usage estimate = sum(each verified SKU quantity × applicable rate)
                       with tiers/minimums applied per its billing rules
Cloud financial cost = cloud usage estimate adjusted for contract commitments
                       and valid discounts/credits, without double-counting
Full TCO             = cloud financial cost + external services/licenses/support
                       + operations labor + allocated one-time setup/migration
                       + applicable taxes/fees and explicit FX adjustment

Cloud cost per paying account = allocated cloud financial cost / paying accounts
TCO per paying account        = allocated full TCO / paying accounts
```

Use one currency and period throughout; identify the FX source/date and who
validated tax treatment. Separate recurring consumption, allocated one-time
costs, and cash payment timing. Show both the temporary credit-adjusted view
and the recurring cost without expiring incentives. Do not apply credits or
allowances twice across environments. This is a planning method, not tax or
financial advice or a competitor benchmark.

For the first-customer example, the denominators are 20, but both numerators
are still **UNPRICED**. For the prototype with zero paying accounts, cost per
paying account is **undefined**, not zero. State which shared costs are allocated
to this product; customer count is an accounting denominator, never a load test.

Build low/expected/high cases by changing explicit quantities: requests, payload
size, concurrency, runtime hours, replicas, log verbosity and backup retention.
For example, doubling growth egress changes the traffic input from 1,000 to 2,000
GB, but does not prove the network charge doubles because tiers may apply.
List the two largest priced drivers, missing inputs, and the measurement that
would reduce uncertainty. Re-estimate after architecture, region, price, terms,
or usage changes; an estimate past its recorded validity needs rechecking.

## 5. Before deployment, and after the experiment

- [ ] Record exact target, confirmed current rates, estimate validity, cost owner,
      low/expected/high totals and unresolved inputs. Do not label partial totals
      as a complete estimate or authorize deployment while critical costs are unknown.
- [ ] Review existing budgets and alert recipients. Budgets alert; they do not
      stop spending. [Oracle budgets](https://docs.oracle.com/en-us/iaas/Content/Billing/Concepts/budgetsoverview.htm).
- [ ] Propose supported compartment quotas and application/architecture limits
      where enforcement is needed; quotas bound resource consumption, not a
      currency bill. [Oracle quotas](https://docs.oracle.com/en-us/iaas/Content/Quotas/Concepts/resourcequotas.htm).
- [ ] Obtain explicit approval immediately before any OCI or IAM mutation,
      applying limits, scaling, or a paid load test. An estimate is not approval.
- [ ] Compare measured usage and finalized charges for the same period with
      the estimate; explain variance and record evidence, not a fabricated bill.
- [ ] Before teardown, identify exact managed resources from state and receipt,
      retained data, backups and cost drivers; obtain separate destructive approval.
- [ ] After teardown, inspect residual volumes, images, objects/versions, logs,
      backups, IPs, front doors, DNS, secrets and external subscriptions. Assign
      an owner, intended retention and current cost status to each retained item.

Stopping a VM is not deleting its storage. When terminating, explicitly review
boot/block-volume retention choices; do not assume an empty application means
a zero bill. [Oracle: terminating an instance](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/terminatinginstance.htm).
Follow the [baseline teardown gates](FOUNDER-BASELINE.md#safe-teardown), not a
compartment-wide cleanup command.
