# Reusing `oracle/skills`

`oracle/skills` is the official, open-source collection of practical Oracle
skills. Treat it as the upstream source for reusable service knowledge and this
toolkit as the founder-journey composition layer.

## Trust boundary and reviewed provenance

Operational reuse is verification-gated. The values below disclose the exact
snapshot recorded by the full toolkit; copying them into this reference does
not by itself verify a checkout or an installed skill.

| Reviewed item | Exact value |
|---|---|
| Commit | `b0afa3bfd7c7e3547458d7fe52649ab1b59706b7` |
| `LICENSE.txt` SHA-256 | `939579ce6e384d07f665d3f8078d3596a41c3517465a92d9ce680ebb23e33205` |
| `oci` tree | `a6e98fe28bfba69c98773c22c447bbe311f40e32` |
| `db` tree | `87377c0d40accfb68629e8f3054cd3a6ad63566b` |
| `.claude-plugin` tree | `e90330c495d0b634b857bc659f9cb58004de0004` |

The portable skill-only archive includes this reference but intentionally does
not include the full toolkit's `upstream/oracle-skills.lock.json` or
`scripts/verify_oracle_skills_lock.py`. Those are explicit external
dependencies, not silent links. If either file is unavailable, fail closed at
planning level: do not install, update, or operationally route to an upstream
skill. An installed skill or the values printed above are not substitutes for
that verification boundary.

No successful verifier run against a real `oracle/skills` checkout is claimed
by the toolkit documentation. Claim a pass only when the verifier was actually
run against the checkout in the current workflow and returned a passing
receipt.

## Verification-first installation

Do not install, update, clone, or fetch anything unless the user requests that
environment change. When installation is requested, use this order:

1. Confirm that a reviewed full toolkit checkout exposes both the lock and the
   verifier named above.
2. Obtain the upstream checkout at the recorded commit.
3. Run the full toolkit verifier and require a passing receipt.
4. Only then run a project-scoped install from the backend that will use the
   skill.

```bash
git clone https://github.com/oracle/skills.git /absolute/path/to/oracle-skills-reviewed
git -C /absolute/path/to/oracle-skills-reviewed checkout --detach b0afa3bfd7c7e3547458d7fe52649ab1b59706b7

python3 /absolute/path/to/oci-founder-toolkit/scripts/verify_oracle_skills_lock.py \
  --lock /absolute/path/to/oci-founder-toolkit/upstream/oracle-skills.lock.json \
  --checkout /absolute/path/to/oracle-skills-reviewed
```

Stop if the verifier is missing, errors, or reports `summary.passed: false`.
After a pass, change to the target backend and install only the domain the task
needs. Each add command must name exactly one agent and must omit `-g`:

```bash
cd /absolute/path/to/target-backend

# OCI domain for Codex
npx --yes skills@1.7.0 add /absolute/path/to/oracle-skills-reviewed/oci \
  -a codex --copy -y

# Oracle Database domain for Codex; run separately and only when needed
npx --yes skills@1.7.0 add /absolute/path/to/oracle-skills-reviewed/db \
  -a codex --copy -y

npx --yes skills@1.7.0 list --json
```

The example targets Codex. For Cursor or Claude Code, replace `codex` with
exactly one of `cursor` or `claude-code`; never add multiple `-a` flags to one
command. Run only the domain command needed by the request and execute it from
the target backend so discovery remains project-scoped. Do not use `-g`.

The pinned `skills@1.7.0` version constrains the top-level installer package,
not its full transitive dependency graph, so this convenience flow is not a
bit-for-bit installer replay. Installing directly from the remote
`oracle/skills/oci` or `oracle/skills/db` source resolves moving upstream
content and does not match the reviewed snapshot. Claude Code can register a
remote marketplace, but that also may resolve newer content; use the verified
local checkout instead.

## Current routing

At the reviewed commit:

| Founder need | Upstream start point |
|---|---|
| Deploy a Function from a local workstation | `oci/functions/oci-functions-deploy/SKILL.md` |
| Troubleshoot Functions setup, deploy, invocation, or observability | `oci/functions/oci-functions-troubleshoot/SKILL.md` |
| Design or scaffold an OKE cluster or Terraform stack | `oci/oke/skills/oke-cluster-generator/SKILL.md` |
| Diagnose an OKE cluster or workload incident | `oci/oke/skills/oke-troubleshooter/SKILL.md` |
| Configure GVA secondary VNIC node pools | `oci/oke/skills/oke-gva-deployer/SKILL.md` |
| Deploy or validate Multus multihome networking on an existing GVA node pool | `oci/oke/skills/oke-multihome-deployer/SKILL.md` |
| Build with OCI Generative AI, agents, RAG, or governance | `oci/enterprise-ai/SKILL.md` |
| Work with Oracle Database, drivers, SQL, ORDS, migrations, or safe agent DB workflows | `db/SKILL.md` and its routed topics |
| Work with OCI IoT Platform | `oci/iot-platform/SKILL.md` |
| OCI Container Instances, API Gateway, Load Balancer, or OCI Database with PostgreSQL procedures | No reviewed upstream skill is currently routed. Use current official OCI documentation. The toolkit repository's Container API blueprint is a temporary sandbox preview, not a replacement for an upstream service skill |

## Runtime routing behavior

Before delegating, inspect the host's available skill catalog or readable
installed skill tree. Do not infer availability from this file, a remote
repository, or the disclosed provenance values alone.

- If the exact dedicated skill is available and its installed copy can be tied
  to a checkout that passed the full toolkit verifier, load it and preserve the
  founder constraints and mutation ceiling when handing off the task.
- If only an unreviewed or unknown version is available, disclose that status
  and remain at planning level.
- If the skill, full toolkit lock, or full toolkit verifier is absent, stay at
  architecture or planning level, name the exact missing dependency, and do
  not recreate its deployment, troubleshooting, SQL, or IAM procedure from
  memory.
- If installation is requested, follow the verification-first flow above. A
  successful source verifier receipt does not prove a different pre-existing
  installed copy came from that source.

The lock records what maintainers reviewed; it does not prove what the current
host loaded.

## Gaps owned by this toolkit

- founder discovery and architecture selection;
- AWS/GCP/Azure mental-model translation;
- Founder Baseline sequencing for compartment, identity, tags, budgets, quotas, and state;
- end-to-end Container API and Function API composition;
- deployment receipts, verification, and teardown contracts;
- cross-agent packaging and behavioral tests.

These are journey concerns rather than service manuals.

## Contribution rule

Use this decision test:

1. Would the content help an OCI user who is not a founder and not using this toolkit?
2. Is it primarily a fact or procedure about one Oracle service?
3. Can it stand alone without a toolkit blueprint?

If the answers are mostly yes, contribute it to `oracle/skills` and reference
it here. If the content sequences several services for the founder journey or
encodes toolkit policy, keep it here.

Do not patch vendored upstream files. Update the upstream repository, review
the new immutable commit, run cross-agent and safety tests, then update the
lock.

## Provenance rules

- Pin a 40-character commit SHA for every reviewed release.
- Record only the upstream paths the toolkit relies on.
- Do not consume a moving `main` branch in a release bundle.
- If a future release bundles upstream content, include its license and checksums in release provenance.
- Never auto-merge changes to upstream IAM, CLI, deployment, or destructive-operation instructions.

The toolkit lock is a source-review record, not a package-manager lock. A
passing verifier receipt establishes that the inspected checkout matches the
recorded commit, trees, clean-worktree state, and license hash; it does not
prove that an arbitrary installed skill came from that checkout.

## Sources

- https://github.com/oracle/skills
- https://github.com/oracle/skills/blob/main/SKILL_AUTHORING_GUIDE.md
- https://github.com/oracle/skills/tree/main/oci
- https://github.com/oracle/skills/tree/main/db
