# Oracle Skills upstream

This directory records the exact official `oracle/skills` snapshot reviewed by a toolkit release.

The source repository does not vendor or modify Oracle Skills. The lock is a
source-review record, not a package-manager lock: direct installation from the
upstream default branch can retrieve newer content. A reproducible evaluation
uses a detached checkout of the recorded commit and installs `oci/` or `db/`
from that local path. Release packaging may later materialize a reviewed
allowlist.

## Update policy

1. Fetch the candidate upstream commit without modifying this repository.
2. Diff the recorded `oci`, `db`, and packaging dependency scope.
3. Review changes to IAM, CLI commands, deployment steps, mutation gates, and destructive operations manually.
4. Run repository validation and cross-agent behavioral cases.
5. Update the commit, tree IDs, date, selected paths, and third-party notice in one reviewed change.

Never point a released toolkit at a moving branch.

## Sources

- https://github.com/oracle/skills
- https://github.com/oracle/skills/blob/main/LICENSE.txt
- https://github.com/oracle/skills/blob/main/SKILL_AUTHORING_GUIDE.md
