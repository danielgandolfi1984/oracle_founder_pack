# ADR 0003: Choose the public-license and publisher model

- Status: proposed; approval required
- Date: 2026-09-18
- Decision owners: project rights holder, Oracle Legal/OSS, Oracle trademark,
  security, support, and repository owners

## Outcome needed

The repository is publicly visible, but the current evaluation license does
not grant the public permission to install, run, modify, or redistribute the
toolkit. Before an **installable** founder-facing public preview can be
published, the decision owners must approve the rights holder, publisher,
project classification, license, name/brand use, contribution model, security
intake, and support boundary.

This record prepares that decision. It does not provide legal advice, grant
rights, change the current license, or represent Oracle approval.

## Why this is a product blocker

The founder experience promises a short, self-service installation path. That
promise cannot be offered to the general public while every evaluator needs
prior written authorization and no authorization-request channel exists.
Technical validation cannot substitute for permission to use the software.

Three release states must remain distinct:

| State | What it means | Current status |
|---|---|---|
| Public source | People can view and fork through GitHub as permitted by GitHub's functionality; this does not grant broader install or execution rights | Available |
| Installable public preview | A public license authorizes self-service use and an immutable distribution coordinate supplies a stable installation target, with explicit preview and no-SLA boundaries | Blocked |
| Oracle-supported release | Oracle-approved publisher, support, security, lifecycle, field qualification, and distribution controls are operational | Blocked |

An open-source license can enable the second state. It does not create Oracle
Support coverage, an SLA, a production-readiness claim, or permission to use
Oracle trademarks and logos.

## Options considered

| Option | Founder adoption | Patent and contribution model | Operational cost | Assessment |
|---|---|---|---|---|
| Keep the restrictive evaluation license | Every public user still needs prior written authorization | No new public grant | Lowest transition effort, but incompatible with self-service adoption | Use only if the project remains a controlled evaluation |
| **UPL-1.0** | Permissive use, modification, distribution, sublicensing, and commercial use | Express copyright and patent grants; contribution policy still needs separate approval | Simple redistribution obligations and alignment with `oracle/skills` | **Provisional recommendation, subject to approval** |
| Apache-2.0 | Broad, familiar permissive adoption | Express patent grant and defensive patent termination; intentionally submitted contributions are addressed by the license unless the contributor explicitly states otherwise or another agreement applies | Requires license preservation, modified-file notices, and `NOTICE` handling when applicable | Strong fallback if Oracle policy prefers its patent and notice model |
| Dual UPL-1.0/Apache-2.0 | Downstream users choose either license | Two patent/compliance regimes | More manifest, packaging, contribution, and support ambiguity | Not recommended without a concrete legal or commercial need |
| Open source plus a separate commercial license | Can support a future commercial model | Requires centralized ownership or sufficient contributor agreements | Highest governance burden | Defer unless a real dual-licensing strategy exists |

## Provisional recommendation

Evaluate **UPL-1.0** first because it aligns with the reviewed
[`oracle/skills` license at the pinned commit](https://github.com/oracle/skills/blob/b0afa3bfd7c7e3547458d7fe52649ab1b59706b7/LICENSE.txt),
permits the founder-first self-service use case, includes an express patent
grant, and keeps the public license model simple. Use **Apache-2.0** as the
fallback if Oracle Legal/OSS or patent policy prefers defensive patent
termination and the Apache notice model.

Do not implement either option until the actual rights holder and authorized
publisher are documented. Repository history, employment, a personal GitHub
account, or public visibility alone does not establish authority to relicense.
Do not use a dual license merely to postpone the decision.

## Approval packet

The approvers must record each item below; none should be inferred by a build
script or repository contributor.

| Decision | Required recorded value |
|---|---|
| Project classification | Official Oracle project, Oracle-sponsored preview, or independent/community project |
| Rights holder | Legal entity or person that owns and can license the original work, including applicable copyright years |
| Publisher | Public author/developer/publisher identity used in manifests, packages, and release notes |
| Repository home | Approved personal or organization-owned repository and migration plan, if any |
| Public license | Canonical license and SPDX identifier: `UPL-1.0` or `Apache-2.0` |
| Patent review | Approval of the selected patent grant and termination model |
| Name and marks | Approval or replacement of “OCI Founder Toolkit,” Oracle/OCI references, logos, and visual assets |
| Contributions | Oracle Contributor Agreement, another CLA, DCO, or closed-contribution policy; merge and release authority |
| Security | Named owner, confidential external intake, supported versions, disclosure process, and response boundary |
| Support | Community or Oracle channel, supported versions, lifecycle/deprecation policy, and explicit SLA or no-SLA statement |
| Distribution | Tag/release owner, namespaces, SBOM/provenance/signing requirements, and compromised-release withdrawal process |
| Scope and exclusions | Which code, skills, documentation, examples, and assets are covered; explicit exclusions |
| Evidence | Approver names/roles, dates, and durable links to Legal/OSS, trademark, security, and support decisions |

If the project is Oracle-sponsored, Oracle employees and external contributors
must follow the contribution process approved for that project. The repository
must not claim an Oracle publisher, Oracle Contributor Agreement requirement,
or official status before those decisions are recorded.

## Trademark and internal-material boundary

Neither proposed software license authorizes branding the toolkit as
Oracle-sponsored or using Oracle logos. The project name, publisher identity,
branding, and logo/template use require the applicable approval and must not
imply sponsorship or support that has not been approved. Accurate referential
text about Oracle and OCI must follow the Oracle trademark guidelines.

The Oracle-template presentation at
`artifacts/OCI-Founder-Toolkit-Oracle-Template-v11-User-Guide.pptx` remains
Git-ignored, excluded from every archive, marked `Confidential: Internal`, and
outside any proposed public software license. Publishing it requires a
separate content, confidentiality, and brand decision.

## Implementation after approval

Apply the approved decision atomically rather than changing only `LICENSE`:

1. Replace the evaluation license with the canonical approved text and
   approved rights-holder notice.
2. Synchronize the SPDX identifier, publisher, repository, and project status
   in all three plugin manifests, package builders, validators, tests, README,
   Quickstart, compatibility, roadmap, and release documentation.
3. Publish contribution, code-of-conduct, governance, maintainer, security,
   support, lifecycle, and third-party policies approved for the project.
4. Include support and security instructions in every distributable archive;
   regenerate deterministic packages, hashes, manifests, and lifecycle
   evidence.
5. Enable the approved confidential vulnerability-reporting path and document
   a compromised-release withdrawal process.
6. Publish an immutable preview tag only after its exact revision passes CI,
   public-coordinate install/remove/reinstall, required SBOM/provenance/signing
   checks, and the remaining preview gates in `RELEASING.md`.

Keep `preview`, `sandbox-only`, `no SLA`, and unqualified-host/field warnings
where they remain true. A public license grants rights; it does not make the
toolkit production-ready or supported.

## Consequences while this ADR is proposed

- `LICENSE` and `LicenseRef-OCI-Founder-Toolkit-Evaluation` remain unchanged.
- No tag, GitHub release, marketplace listing, public package, or install
  invitation is authorized.
- The source may continue to be reviewed under its existing terms.
- Technical qualification and an OCI sandbox pilot may continue for authorized
  collaborators under the existing terms, but they do not close the legal,
  publisher, trademark, security, or support gates.

## Primary references

- [Universal Permissive License and FAQ](https://oss.oracle.com/licenses/upl/)
- [SPDX UPL-1.0 identifier](https://spdx.org/licenses/UPL-1.0.html)
- [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0.html)
- [Applying Apache License 2.0](https://www.apache.org/legal/apply-license)
- [Oracle trademark guidelines](https://www.oracle.com/legal/trademarks/)
- [Oracle logo guidelines](https://www.oracle.com/legal/logos/)
- [Oracle Contributor Agreement](https://oca.opensource.oracle.com/js/views/home.html)
- [GitHub repository licensing guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)
- [GitHub public-repository license grant](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service#5-license-grant-to-other-users)
- [GitHub private vulnerability reporting](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/report-privately)
