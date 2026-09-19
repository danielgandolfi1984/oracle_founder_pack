# Choose your first OCI journey

Canonical guide, reviewed **2026-09-19**. Short companion guides:
[Português (Brasil)](i18n/pt-BR/START-HERE.md) ·
[Español](i18n/es/START-HERE.md). They are entry points, not full translations.

Founder Toolkit for OCI is Daniel Gandolfi's independent personal project,
not an Oracle product or Oracle-supported service. Start with one useful
outcome, not a catalog of services. You can assess a backend without an OCI
account; using your account is a separate decision.

## 1. Pick the job you need to finish

| Your situation | Start with | Your first deliverable | Before going further |
|---|---|---|---|
| **Solo founder:** “I need to get oriented.” | [Install and assess one backend](QUICKSTART.md) | One recommended runtime, assumptions, cost drivers, and a next action | Learn account access and complete the manual VM lab if OCI foundations are new |
| **Small team:** “We need a shared starting point.” | Quickstart plus [Founder Baseline](FOUNDER-BASELINE.md) | A reviewed plan naming deployment, billing, security, and incident owners; separate development and production scope | Review individual access and the release/rollback process; do not share one person's private keys |
| **Moving from AWS/GCP/Azure:** “What changes?” | [Use-case recipes](USE-CASES.md) and [glossary](GLOSSARY.md) | A mapping of runtime, database, identity, network, and data-transfer assumptions, including non-equivalences | Validate one isolated flow with synthetic data; plan rollback before any migration or DNS cutover |
| **First customer:** “Can I responsibly put this online?” | [Reference backend](REFERENCE-BACKEND.md), [cost scenarios](COST-SCENARIOS.md), and [evidence](EVIDENCE.md) | A go/no-go checklist covering HTTPS, authorization, backup/restore, monitoring, cost, and support ownership | Close the evidence and security gaps before customer data or a production commitment |

The standalone `oci-founder` **v0.1.1** remains a planning skill without its
verified operational dependencies. Installing it does not authenticate your
terminal, grant IAM access, or turn these guides into an automatic deployment.
The [first VM lab](FIRST-VM.md) is executed by you in the Console and terminal.
The reference backend is a design target, not a claim of a deployed product.
Check [validation status](VALIDATION.md) before relying on an example.

## 2. If you need an OCI account

**Already have company access?** Ask the account administrator for the correct
tenancy, identity domain, project compartment, and scoped permissions. Do not
create a second account or use the tenancy administrator for routine work
merely to get past an access error.

**Starting personally?** Review the official [signup and Free Tier FAQ](https://www.oracle.com/cloud/free/faq/)
and follow its signup link yourself. Review the terms, country availability,
payment-method requirements, identity verification, and home-region selection
before submitting. Enter contact, card, password, and MFA information only in
the official account flow, never in a repository or agent conversation.

Signup is not permission for an agent to enroll you in a paid plan. A paid
upgrade is a separate financial decision: review the current
[upgrade procedure](https://docs.oracle.com/en-us/iaas/Content/GSG/Tasks/buysubscription_topic-Upgrade_Your_Free_Promotion.htm),
payment authorization, and applicable terms, then confirm it yourself. Do not
upgrade just because an example fails. This project promises no credits,
program eligibility, free capacity, acceptance of a payment method, or zero bill.

Before creating resources, record the account's actual billing status, the
person responsible for charges, and a reviewed cost envelope using
[cost scenarios](COST-SCENARIOS.md). Do not build a business continuity plan
around a promotion: check expiration and data-retention conditions in the
official FAQ. Keep card details and invoices out of public issues.

## 3. Choose the region for your users, not this example

Write a short decision record before signup or a regional deployment:

| Question | Evidence to collect |
|---|---|
| Where are customers and dependent systems? | Candidate locations and measured application latency from relevant networks; geography alone is not a benchmark |
| Are the exact services and sizes available? | Current [service availability](https://www.oracle.com/cloud/distributed-cloud/service-availability/), service-specific documentation, and the options/limits visible in your tenancy |
| Where may data, backups, and logs reside? | Customer contracts and requirements reviewed with the responsible privacy/security/legal owner; this guide is not a compliance conclusion |
| How will you recover? | Required recovery time/data loss, backup location, restoration test, and additional regional cost |

Your tenancy's **home region cannot be changed after provisioning**. Distinguish
that choice from the region of a particular application. Review Oracle's
[region management guide](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/managingregions.htm)
before selecting or subscribing to a region; do not ask an agent to add a
subscription as an automatic troubleshooting step. Availability listings do
not reserve Compute capacity. Keep a reviewed alternative or defer the lab if
the selected shape cannot be provisioned.

In the Console, check the region selector and compartment when a resource
appears missing; regional resources are shown in the selected region.
See [working in regions](https://docs.oracle.com/en-us/iaas/Content/GSG/Concepts/working-with-regions.htm).
There is no single default region for every Latin American business.

## 4. Move from planning to a controlled lab

1. Complete the [quickstart](QUICKSTART.md) for one agent and one repository.
2. Follow [account and local access](ACCOUNT-SETUP.md): find identifiers, choose
   one local authentication method, and run the documented read-only test.
3. Review the [VM lab](FIRST-VM.md): exact compartment, region, network exposure,
   shape, storage, cost, and cleanup scope. Approve each creation/change before
   executing it; IAM permission alone is not consent to do it now.
4. Record what actually passed, what failed, and what remains untested using the
   [evidence guide](EVIDENCE.md). Never label a generated plan as a live test.
5. Remove only the lab resources you identified and approved, or record their
   retention and continuing cost. Never delete everything in a compartment.

Do not paste keys, tokens, passwords, Terraform state, customer data, or private
account identifiers into public issues. CLI/API access and VM SSH are distinct;
the account guide explains which credential belongs to each.

## 5. If you get stuck, use the right help route

```text
Where did the journey stop?
├─ Signup / card / Console login / MFA
│  └─ Official account recovery or support chat; not a GitHub credential dump.
├─ Skill not discovered / unclear guide / toolkit bug
│  └─ Quickstart troubleshooting, then a redacted project issue.
├─ CLI authentication / wrong region / IAM denial
│  └─ Account guide, then your account administrator; no blanket admin grant.
├─ VM capacity / service limit
│  └─ Check the exact error and account limits; review alternatives and costs.
└─ SSH / route / application issue
   └─ VM lab diagnostics; distinguish reachability, key, and application errors.
```

For signup, sign-in, and MFA, follow Oracle's
[account access and chat instructions](https://docs.oracle.com/en-us/iaas/Content/GSG/Tasks/signinginIdentityDomain.htm).
For OCI technical or billing problems, use the
[official support options](https://docs.oracle.com/en-us/iaas/Content/GSG/Tasks/contactingsupport.htm)
for your actual account and entitlement, or the
[community/help routes](https://docs.oracle.com/en-us/iaas/Content/GSG/support/getting-help.htm).
Do not assume Free Tier includes a technical service-request entitlement.
The FAQ and support pages distinguish account chat, community help, and support
requests; confirm the route available to you without promising a response time.

For this toolkit, read [SUPPORT.md](../SUPPORT.md) and report a sanitized
reproduction with the version, agent, OS, step, and exact error. Project help
is best effort with no SLA; it cannot unlock an OCI account, change billing,
grant capacity, or provide Oracle Support coverage. Report suspected security
issues through [SECURITY.md](../SECURITY.md), not a public issue.
