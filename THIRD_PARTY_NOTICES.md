# Third-party notices

## Toolkit license

Founder Toolkit for OCI original content is Copyright (c) 2026 Daniel Gandolfi
and licensed under the Universal Permissive License 1.0 (UPL-1.0). See
[`LICENSE`](LICENSE).

## Oracle Skills

- Project: Oracle Skills
- Source: https://github.com/oracle/skills
- Reviewed commit: `b0afa3bfd7c7e3547458d7fe52649ab1b59706b7`
- License: Universal Permissive License 1.0 (UPL-1.0)
- License text: https://github.com/oracle/skills/blob/b0afa3bfd7c7e3547458d7fe52649ab1b59706b7/LICENSE.txt

No Oracle Skills files are vendored in this source tree at version `0.1.0`.
The project is an external source and install-time dependency. If a future
distribution bundles selected upstream files, that distribution must include
the corresponding UPL license text, source provenance, and checksums.

## Agent Plugins manifest schema

- Project: Agent Plugins Specification
- File: `schemas/1.0.0/plugin.schema.json`
- Canonical source: https://agent-plugins.org/schemas/1.0.0/plugin.schema.json
- Reviewed date: 2026-09-18
- Local snapshot: `schemas/agent-plugin-1.0.0.schema.json`
- Local SHA-256: `0a4aad95ce337878ad38802ebf0daa3fde76abe3f65400c86bcbb1ec0b3ab883`
- License: Apache License 2.0
- License mapping: https://github.com/agentplugins/agent-plugins-spec/blob/main/LICENSE.md

The schema snapshot is included only in the source repository for deterministic
manifest validation. It is not included in the runtime packages.

## PyYAML

- Project: PyYAML
- Version: `6.0.2`
- Source: https://pypi.org/project/PyYAML/6.0.2/
- License: MIT

PyYAML is a pinned development-validator dependency and is not vendored or
included in the runtime packages. The reviewed macOS/Python 3.9 and Linux
x86_64/Python 3.12 wheel hashes are recorded in
`requirements-validation.txt`.
