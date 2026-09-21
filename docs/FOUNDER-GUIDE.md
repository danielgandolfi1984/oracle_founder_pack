# Founder guide: from your repository to an informed OCI decision

**English · revision 2026-09-21 · [Português completo](i18n/pt-BR/FOUNDER-GUIDE.md).**
For founders and backend developers using Codex, Cursor or Claude Code.
You can start without an OCI account. The first outcome is a reviewed plan,
not a cloud deployment. Daniel Gandolfi maintains this independent personal
project; he works at Oracle, but the project is not an Oracle product or SLA.

## 1. Install the published skill first

Have Git, Node.js **22.20.0 or later**, `npx`, and your chosen agent installed
and authenticated. Open the backend repository where you want the skill.
Run **one** of these commands there; replace the example local directory:

```bash
cd /absolute/path/to/your-backend

# Codex
npx --yes skills@1.7.0 add \
  'https://github.com/danielgandolfi1984/oracle_founder_pack#v0.1.1' \
  --skill oci-founder -a codex --copy -y

# OR Cursor
npx --yes skills@1.7.0 add \
  'https://github.com/danielgandolfi1984/oracle_founder_pack#v0.1.1' \
  --skill oci-founder -a cursor --copy -y

# OR Claude Code
npx --yes skills@1.7.0 add \
  'https://github.com/danielgandolfi1984/oracle_founder_pack#v0.1.1' \
  --skill oci-founder -a claude-code --copy -y
```

These commands copy project-scoped files; omit `-g`. Do not install three
copies into the same backend. They require package/source downloads but no
OCI credentials. The pinned installer does not pin all transitive dependencies.
This is the published **v0.1.1 public preview**, not a marketplace installation.

Confirm with the same agent name, replacing `codex` if needed:

```bash
npx --yes skills@1.7.0 list -a codex --json
```

Expect `oci-founder` at project scope. Qualified installer destinations are
`.agents/skills/oci-founder` for Codex/Cursor and `.claude/skills/oci-founder`
for Claude Code. Layout tests passed for all three; native evidence is one
Codex probe with reservations, not full Cursor/Claude runtime qualification.
See [installation details](QUICKSTART.md) and [compatibility](COMPATIBILITY.md).

## 2. Ask for your first useful result

| Agent | Start the request with | If the skill is missing |
|---|---|---|
| Codex CLI/IDE | `Use $oci-founder.` or select through `/skills` | Confirm the list, then restart if needed |
| Cursor | `/oci-founder` | Reopen or reload the target workspace |
| Claude Code | `/oci-founder` | Start a new session if necessary |

Host references: [Codex](https://learn.chatgpt.com/docs/build-skills),
[Cursor](https://cursor.com/docs/skills), [Claude Code](https://code.claude.com/docs/en/skills).
In another surface, select the named skill using its available picker.

```text
Use the oci-founder skill. Inspect this backend read-only. I know AWS/GCP/Azure,
but I am new to OCI. Recommend the smallest safe path for [product goal].
Separate repository facts from assumptions; explain unfamiliar terms,
cost drivers, missing tests and one next step. Do not install anything,
open credential files, execute cloud commands or change resources.
```

Use your agent's explicit prefix above. Expect one recommendation, why it fits,
what would change it, and one next action. A service catalog or an unverified
fixed price is not a useful assessment. Ask for `founder-plan.md` only when you
want a full plan; a focused question should not require that artifact.

## 3. Understand what you installed

| Component | Its job | What it does not grant |
|---|---|---|
| Founder skill | Sequence decisions, translate concepts and review risk | Cloud access or approval to execute |
| `oracle/skills` | Reusable Oracle service procedures | Automatic availability or verified provenance on your machine |
| CLI/SDK/connector | Execute an authorized request | IAM permissions merely because a tool exists |
| Profile plus credential | Authenticate the caller | Access to every resource or authority to mutate now |
| IAM policy | Authorize scoped operations | Your approval of a particular change |

Reuse upstream rather than rewriting its service manuals. Operational routing
requires the full toolkit's lock/verifier and a verified installed upstream
copy; otherwise stay at planning level. Follow the
[verification-first upstream guide](../skills/oci-founder/references/upstream-oracle-skills.md).

Optional source-only journeys are `oci-founder-start` for a new project and
`oci-founder-migrate` for an existing workload. They are **not in v0.1.1** and
do not inherit its release or host evidence. To evaluate one, first clone `main`
to a new local directory, review its contents and record the commit:

```bash
git clone --branch main --single-branch \
  https://github.com/danielgandolfi1984/oracle_founder_pack.git \
  /absolute/path/to/oci-founder-toolkit
git -C /absolute/path/to/oci-founder-toolkit rev-parse HEAD

cd /absolute/path/to/your-backend
npx --yes skills@1.7.0 add /absolute/path/to/oci-founder-toolkit \
  --skill oci-founder-start -a codex --copy -y
```

Choose `oci-founder-migrate` instead if that is your job; select exactly one
agent (`codex`, `cursor` or `claude-code`) and no global installation. Confirm
the selected name with the list command. `main` moves: a reviewed local commit,
not the branch label, identifies the evaluated source. Source installation
does not authorize dependency installation, account access or deployment.

## 4. Choose: a new product or an existing workload

**Starting:** describe the first customer action, data, users, expected traffic,
budget and recovery needs. Keep a familiar database and identity provider unless
evidence supports changing them. A VM teaches infrastructure; a persistent
container API or an event handler may suggest a different runtime. Do not start
with Kubernetes merely because you might grow.

> Use the oci-founder-start skill. Plan an MVP for [customer action], using
> [language/database]. Explain one runtime choice, minimum foundation, cost
> inputs and acceptance tests. Planning only; no credentials or cloud changes.

**Migrating:** inventory runtime, database extensions, identity, storage, queues,
background jobs, network paths, DNS and observability. Label each cloud mapping
as close, approximate or without a direct equivalent. Compare the same workload
and recovery objective; include overlap cost, egress and operator effort.

> Use the oci-founder-migrate skill. Assess this existing [cloud] backend
> read-only. Preserve data and login choices. Identify incompatibilities,
> a synthetic-data experiment, rollback criteria and reasons not to migrate yet.
> Do not copy customer data, change DNS, cut over traffic or deploy.

Before a rehearsal, define acceptable downtime, recovery time (RTO), data-loss
window (RPO), and functional/performance pass criteria. Use synthetic or
separately approved sanitized data; test restoration and reconciliation rather
than treating a backup file as proof of recovery.

For cutover, name the operator, final synchronization, authoritative writer,
background consumers and conditions to stop. Freeze or synchronize writes using
a reviewed method. Retain the source for an agreed recovery window. Reverting
DNS does not reverse writes accepted in OCI: the rollback plan must address
reconciliation or forward recovery before traffic moves. Each execution and
eventual source retirement needs its own exact-target approval.

If those optional skills are not installed, use `oci-founder` with the same
request. Define go/no-go thresholds before testing. OCI is not assumed to be
universally cheaper or faster; use the [decision framework](WHY-OCI.md).

## 5. Prepare your account and region deliberately

For company access, ask the administrator for the tenancy, identity domain,
project compartment and scoped permissions. For a personal account, complete
the [official signup flow](https://www.oracle.com/cloud/free/faq/) yourself.
Paid enrollment/upgrade is a separate decision; no free capacity, credit or
zero bill is promised. Keep payment details, passwords and MFA out of chat.

Choose a region from user latency, required services, data-location requirements
and recovery design. Check [current availability](https://www.oracle.com/cloud/distributed-cloud/service-availability/)
and actual account capacity. The [home region cannot be changed after provisioning](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/managingregions.htm);
it is not necessarily the application's region. No single region fits all LATAM.

## 6. Find the Console values without exposing them

Sign in to [the Console](https://cloud.oracle.com/) yourself. Labels may vary.
Keep the values in private local notes outside Git; use placeholders in public
examples and share only the necessary scope with a trusted executor.

| Needed value | Where to look | Why |
|---|---|---|
| Tenancy OCID | Profile → Tenancy → Tenancy Information → Copy | Confirm the account |
| User OCID | Profile → User settings → User Information | API signing identity, if that method is chosen |
| Region identifier | Top region selector; match the official region list | Target regional resources |
| Compartment OCID | Identity & Security → Compartments → selected compartment | Bound project operations |
| Resource OCID | Specific VM, VCN, subnet or other resource details | Target the exact object |

An OCID is an identifier, not a password or permission. Never provide a full
credential/configuration dump. Sources: [locating IDs](https://docs.oracle.com/en-us/iaas/Content/GSG/Tasks/contactingsupport_topic-Locating_Oracle_Cloud_Infrastructure_IDs.htm),
[user/API-key setup](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/apisigningkey.htm).
Use a dedicated non-root project compartment, not production or the tenancy root.

## 7. Connect the local CLI, then test read-only access

A Console login does not authenticate your agent's terminal. Check `oci --version`;
if missing, install through the [official CLI guide](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm)
only after approving that local change. These examples use Bash/Zsh; in
PowerShell place each OCI command on one line. Run them yourself first.

```bash
oci session authenticate --profile-name FOUNDER
oci session validate --profile FOUNDER --auth security_token

oci network vcn list \
  --compartment-id '<compartment-ocid>' --region '<region-id>' \
  --profile FOUNDER --auth security_token --all
```

Choose a new profile name if `FOUNDER` exists; use it consistently. Complete
region selection/browser login/MFA yourself, then validate. Replace both ID
placeholders before the list command. An empty list can be valid; check scope.
Session success proves authentication, not create permission. Token and signing
key files stay local. Sources: [CLI sessions](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/clitoken.htm),
[`vcn list`](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/network/vcn/list.html).

Tell the agent only the executor, profile name, authentication method, region,
necessary compartment ID and intended read-only query. Review host permissions
before allowing credential use. A remote runner needs a separate setup; do not
copy a human session to it. See [account setup](ACCOUNT-SETUP.md) for the optional
API signing path. OCI API keys, VM SSH keys and app-user tokens are different.

**API signing alternative:** in the intended user's Console details, open
Tokens and keys → API keys (older layouts: Resources → API Keys). Register
only the public signing key; keep its private key protected locally. Use
Configuration File Preview to prepare a separate local profile containing
`user`, `tenancy`, `region`, `fingerprint` and `key_file`; preserve existing
profiles and restrict file permissions. Review these values locally, never
paste the configuration or key into chat/Git. For the read-only query above,
choose that profile and `--auth api_key`, not `security_token`.
[Official API-key procedure](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/apisigningkey.htm).

## 8. Plan the first VCN and VM before creating anything

Use a disposable, human-executed learning lab, not a customer environment.
Agree on owner, end time, current cost inputs and permissions for creation and
cleanup. Record the region, compartment, exact IDs and keep/delete decisions
in a private lab receipt. If public networking is prohibited, stop and agree
on a private-access design with the administrator; do not bypass policy.

| Lab element | Example to review, not a default | Check |
|---|---|---|
| VCN | `founder-lab-vcn`, `10.20.0.0/16` | No overlap with office/VPN/other networks |
| Regional public subnet | `lab-public`, `10.20.10.0/24` | Inside the VCN; correct route table and security lists |
| Internet gateway and route | `lab-igw`; `0.0.0.0/0` → gateway | Route is a path, not an inbound permission |
| NSG | `lab-ssh-nsg`; stateful TCP destination `22` | Source is your actual public IPv4 `/32` |
| VM | `lab-vm`; reviewed image, shape, CPU/RAM and boot volume | Image/CPU compatibility, capacity and storage cost |

Public reachability requires the public IP, route, gateway and applicable rules.
NSG and security-list allows combine: a narrow NSG cannot undo a broad SSH rule.
Inspect both and the OS firewall; never allow SSH from `0.0.0.0/0` for this lab.
[Oracle security rules](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/securityrules.htm).

## 9. Create, verify and clean up with separate approvals

Use [the detailed VM lab](FIRST-VM.md) alongside this sequence. For every OCI
or IAM mutation, review the exact target/plan and explicitly approve immediately
before execution. Knowing IAM permits an action is not approval to perform it.

1. In Networking → Virtual cloud networks, create the reviewed VCN manually;
   enable lab DNS hostnames. Create its regional public subnet and record IDs.
   [VCN](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/create_vcn.htm) / [subnet procedure](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/create_subnet.htm).
2. Create/enable its internet gateway and set the subnet's route table to the
   reviewed gateway. Create the SSH NSG, narrow broader SSH rules in this lab's
   security lists, and preserve other required rules deliberately.
3. In Compute → Instances, review the VM image/shape, existing VCN/subnet,
   public IPv4, NSG attachment and boot volume. Save a new SSH private key
   securely before continuing, or supply only an approved existing public key.
   Approve the reviewed creation and record VM/VNIC/volume IDs when Running.
4. Connect with `ssh -i /absolute/private/key opc@PUBLIC_IP` for Oracle Linux,
   or `ubuntu@PUBLIC_IP` for Ubuntu. Restrict local key permissions; verify the
   server fingerprint through a trusted channel. Inspect `uname -m` and
   `cat /etc/os-release`, then `exit`. [Official SSH instructions](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/connect-to-linux-instance.htm).
5. Record success/failure, actual scope, telemetry and missing checks. SSH works
   does not mean an application is secure, available or production-ready.
6. Before deletion, review receipt/state and an exact keep/delete list; approve
   destructive actions separately. Terminate the VM with explicit volume
   retention choices, then remove only unshared lab networking/dependencies.
   Stop on unexpected resources. [Termination behavior](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/terminatinginstance.htm).

Confirm deleted and retained resources individually and revisit billing when
usage appears. **Stop is not cleanup**; storage and shape-dependent charges can
remain. [Stopped-instance billing](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/resource-billing-stopped-instances.htm).
Never delete an entire compartment to repair a failed cleanup.

## 10. Keep safety and costs visible

Use least privilege, named owners, separate development/production scope and
private state/receipts. Never expose keys, tokens, customer data or Terraform
state in prompts or issues. Diagnosis is read-only; applying a fix needs its
own approval. A generated plan is not an approved `terraform apply`.

Price runtime, database, storage, network, logs, backups, delivery, support and
operator time in one currency/period. Record region, quantities, dated rates
and expiry. The [cost scenarios](COST-SCENARIOS.md) are **unpriced assumptions**,
not bills or capacity results. Unknown is not zero. [Budgets alert but do not
cap spending](https://docs.oracle.com/en-us/iaas/Content/Billing/Concepts/budgetsoverview.htm);
review supported quotas and architecture limits separately with the owner.

## 11. A small glossary to read your plan

| Term | Meaning in this journey |
|---|---|
| Tenancy / compartment | Account boundary / logical project scope; neither replaces network controls |
| OCID / IAM | Exact resource identifier / scoped authorization rules |
| Region / AD / FD | Geographic region / availability domain / fault domain inside an AD |
| VCN / subnet / CIDR | Cloud network / contained address range / address-range notation |
| VNIC / NSG / security list | Network interface / selected-interface rules / subnet-associated rules |
| Image / shape / boot volume | OS starting point / compute allocation / persistent OS disk |
| OCPU | OCI CPU unit; normalize against the chosen processor before comparing vCPUs |
| Profile / session / SSH key | Local identity selection / temporary API credential / VM-login credential |
| Budget / quota | Cost alerting / supported resource-allocation constraint, not a currency cap |
| Rollback / restore / teardown | Revert a change / recover data / remove exact approved resources |

Cross-cloud terms are approximate, not equivalent services. Use the
[full glossary](GLOSSARY.md) and ask the skill to explain one term in your plan.

## 12. Choose an example without overstating its evidence

- The released skill plans/routes; installing it does not install full blueprints.
- The [Container API preview](../blueprints/container-api/README.md) is a separate,
  single-instance sandbox with anonymous test endpoints, not a complete SaaS.
- The [local backend](../examples/local-backend/README.md) tests synthetic business
  rules; optional signed HTTP stays on loopback. It is not public hosting.
- The [identity preflight](../examples/local-backend/IDENTITY-INTEGRATION.md) checks
  existing configuration offline. `--diagnostics` adds safe labels, not a real
  login, provider connection, live token check or automatic key refresh.
- The [reference backend](REFERENCE-BACKEND.md) remains the larger design target.
  Local green tests are not OCI field validation or production approval.

## 13. Get help and leave with one next step

### Update or remove a project copy

Before updating, review the new tag/commit and any local skill edits. Remove
the old project copy, then install the reviewed replacement using sections 1
or 3. Do not add a global duplicate. From the same backend directory:

```bash
npx --yes skills@1.7.0 remove oci-founder -y
npx --yes skills@1.7.0 list -a codex --json
```

For a companion, replace `oci-founder` with its exact name; choose your agent
in the list command. The qualified removal omits `-a`: with `skills@1.7.0`,
agent-filtered removal can leave the shared `.agents` copy behind. Review the
project scope first; other agents using that shared copy are affected. Confirm
the selected skill is absent. Removing a skill does **not** delete OCI resources.
See the [qualified lifecycle](QUICKSTART.md) before changing installation scope.

### Troubleshoot and ask for help

Skill missing? Confirm project, selected agent, list result and session refresh.
For CLI errors, check that executor's profile, expiry, region and compartment;
ask your administrator about exact IAM operations, never blanket admin access.
For SSH, distinguish reachability from key/username errors; do not widen ingress.

For toolkit problems, follow [SUPPORT.md](../SUPPORT.md) with version, agent, OS,
reproduction and redacted output. For vulnerabilities use [SECURITY.md](../SECURITY.md).
Account/billing/service incidents use your official OCI support entitlement;
project issues cannot grant access, capacity or an Oracle support commitment.

Before your next step, state: **my target; my evidence; what remains unknown;
my cost/owner; the required approval; and how I reverse or end the experiment.**
Check [EVIDENCE.md](EVIDENCE.md): source-reviewed, locally tested, live sandbox
and production results are different. This paired user journey is maintained
in EN/PT; engineering receipts and every linked deep-dive are not all translated.
