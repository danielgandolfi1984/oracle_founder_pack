# ADR 0003: Publish as an independent personal project

- Status: accepted
- Date: 2026-09-18
- Decision owner: Daniel Gandolfi

## Decision

Founder Toolkit for OCI is an independent personal open-source project created
and maintained by Daniel Gandolfi.

- Copyright holder and licensor: Daniel Gandolfi
- Public publisher, maintainer, and release manager: Daniel Gandolfi
- Repository: `danielgandolfi1984/oracle_founder_pack`
- License: Universal Permissive License 1.0, SPDX `UPL-1.0`
- Public display name: **Founder Toolkit for OCI**
- Compatible technical identifiers retained: `oci-founder-toolkit` and
  `oci-founder`
- Support: best-effort community support through GitHub Issues, with no SLA
- Security intake: GitHub private vulnerability reporting
- Release status: public preview; not production-qualified or Oracle-supported

Daniel Gandolfi works at Oracle and publishes this project in his personal
capacity. The views expressed here are his own and do not represent Oracle.
This is not an Oracle product and is not sponsored, endorsed, maintained, or
supported by Oracle.

The user's project-owner declaration is the basis for recording Daniel
Gandolfi as the rights holder and publisher. This ADR records the repository
decision; it is not legal advice about employment or intellectual-property
obligations outside the repository.

## Naming and trademark boundary

“Founder Toolkit” is the project name. “for OCI” is a descriptive statement of
the platform it works with. Public metadata uses a neutral visual identity and
does not use Oracle logos, the O Tag, Oracle trade dress, or an Oracle publisher
identity.

Accurate references to Oracle products and official Oracle documentation remain
permitted as descriptive technical context. They must not imply that Oracle
created, certified, sponsors, endorses, maintains, or supports this project.

The repository includes this attribution:

> Oracle, Java, MySQL, and NetSuite are registered trademarks of Oracle and/or
> its affiliates. Other names may be trademarks of their respective owners.

## Internal presentation boundary

The Oracle-template presentation at
`artifacts/OCI-Founder-Toolkit-Oracle-Template-v11-User-Guide.pptx` remains:

- an internal, confidential working artifact;
- ignored by Git;
- excluded from source control and every public archive;
- outside the UPL-1.0 grant for this project; and
- unavailable for public redistribution without a separate Oracle content,
  confidentiality, and brand decision.

The public repository may describe that boundary but must never embed, attach,
or publish the internal deck.

## Contribution model

Contributions are accepted through GitHub issues and pull requests.
Contributors must have the right to submit their work and submit it under
UPL-1.0. Oracle-confidential, customer-confidential, and other unauthorized
third-party material is prohibited.

The project does not require or imply an Oracle Contributor Agreement. Reusable
Oracle service procedures should still be proposed to the upstream
`oracle/skills` project rather than copied into this toolkit.

## Public-preview boundary

The public license authorizes use, modification, and redistribution. It does
not establish:

- Oracle Support coverage;
- a response-time or availability SLA;
- production readiness;
- native behavioral qualification across Codex, Cursor Agent, and Claude Code;
- a fixed price, Free Tier, quota, region, or service guarantee; or
- live OCI plan, apply, rollback, or teardown evidence.

The planning skill may be published as `0.1.0` while those limitations remain
explicit. The Container API blueprint remains a separately versioned,
sandbox-only field preview.

## Distribution decision

Public-preview packages use:

- `status: public-preview`;
- `license: UPL-1.0`;
- publisher Daniel Gandolfi;
- deterministic archives, manifests, and checksums; and
- immutable tag `v0.1.0` for the first public preview.

The source revision must pass CI before tagging. Release artifacts must be built
from that exact revision. Security and support policies must be present inside
the public archives.

## Consequences

Positive:

- founders can install and use the planning skill without individual written
  authorization;
- the publisher and support boundary are explicit;
- the license aligns with the reviewed `oracle/skills` dependency;
- the project can remain personal without claiming Oracle product status.

Tradeoffs:

- Daniel Gandolfi owns release, security, support, and lifecycle decisions;
- support remains best effort;
- public wording must preserve the independent-project and trademark boundary;
- technical and OCI field qualification remain separate from licensing.

## Superseded state

This decision replaces the restrictive evaluation license and the former
`LicenseRef-OCI-Founder-Toolkit-Evaluation` identifier. References that treated
Oracle approval as a prerequisite for this personal repository are superseded.
Oracle approval remains necessary only for separately publishing the internal
Oracle-template deck or making an official Oracle sponsorship, branding, or
support claim.

## Primary references

- [Universal Permissive License and FAQ](https://oss.oracle.com/licenses/upl/)
- [SPDX UPL-1.0 identifier](https://spdx.org/licenses/UPL-1.0.html)
- [Oracle trademark guidelines](https://www.oracle.com/legal/trademarks/)
- [Oracle logo guidelines](https://www.oracle.com/legal/logos/)
- [GitHub private vulnerability reporting](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/report-privately)
