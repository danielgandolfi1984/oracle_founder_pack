#!/usr/bin/env python3
"""Dependency-free structural checks for OCI Founder Toolkit."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROVISIONAL_REPOSITORY = "https://github.com/danielgandolfi1984/oracle_founder_pack"
ERRORS: list[str] = []
CHECKS = 0
IGNORED_VALIDATION_PARTS = {".git", ".pptx-build", "__pycache__", ".terraform"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-host-preflight-evidence",
        action="store_true",
        help=(
            "Validate source contracts without requiring the committed host-preflight receipt. "
            "This is reserved for scripts/qualify_hosts.py while it creates a new receipt."
        ),
    )
    return parser.parse_args()


ARGS = parse_args()


def ignored(path: Path) -> bool:
    return bool(IGNORED_VALIDATION_PARTS.intersection(path.relative_to(ROOT).parts))


def check(condition: bool, message: str) -> None:
    global CHECKS
    CHECKS += 1
    if not condition:
        ERRORS.append(message)


def load_json(relative_path: str) -> dict:
    path = ROOT / relative_path
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        ERRORS.append(f"{relative_path}: invalid JSON: {exc}")
        return {}
    check(isinstance(value, dict), f"{relative_path}: root must be an object")
    return value if isinstance(value, dict) else {}


def tree_fingerprint(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        check(not path.is_symlink(), f"{path.relative_to(ROOT)}: fingerprint input must not be a symlink")
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update((path.stat().st_mode & 0o777).to_bytes(4, "big"))
        content = path.read_bytes()
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        ERRORS.append(f"{path.relative_to(ROOT)}: missing YAML frontmatter")
        return {}, text

    end = text.find("\n---\n", 4)
    if end == -1:
        ERRORS.append(f"{path.relative_to(ROOT)}: unclosed YAML frontmatter")
        return {}, text

    values: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line or line[0].isspace() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values, text


required_files = [
    "README.md",
    "LICENSE",
    "CHANGELOG.md",
    "SECURITY.md",
    "SUPPORT.md",
    "AGENTS.md",
    "CLAUDE.md",
    "plugin.json",
    ".codex-plugin/plugin.json",
    ".claude-plugin/plugin.json",
    "skills/oci-founder/SKILL.md",
    "skills/oci-founder/agents/openai.yaml",
    "skills/oci-founder/references/container-api-preview.md",
    "skills/oci-founder/references/use-cases.md",
    "docs/QUICKSTART.md",
    "docs/GLOSSARY.md",
    "docs/USE-CASES.md",
    "docs/FOUNDER-BASELINE.md",
    "docs/HOST-QUALIFICATION.md",
    "docs/RELEASING.md",
    "docs/VALIDATION.md",
    "scripts/qualify_hosts.py",
    "scripts/qualify_skill_install.py",
    "scripts/build_release.py",
    "scripts/validate_agent_plugin_schema.py",
    "scripts/scan_release_sources.py",
    "scripts/probe_codex_native.py",
    "scripts/verify_oracle_skills_lock.py",
    "scripts/skills-cli-runtime/package.json",
    "scripts/skills-cli-runtime/package-lock.json",
    "requirements-validation.txt",
    "packaging/README.skill.md",
    "packaging/README.full.md",
    "schemas/agent-plugin-1.0.0.schema.json",
    "third_party/README.md",
    "third_party/licenses/Apache-2.0.txt",
    "upstream/oracle-skills.lock.json",
    "tests/prompts/smoke.jsonl",
    "tests/test_qualify_hosts.py",
    "tests/test_qualify_skill_install.py",
    "tests/test_skill_contract.py",
    "tests/test_build_release.py",
    "tests/test_agent_plugin_schema.py",
    "tests/test_codex_native_evidence.py",
    "tests/test_scan_release_sources.py",
    "tests/test_package_evidence.py",
    "tests/test_probe_codex_native.py",
    "tests/test_verify_oracle_skills_lock.py",
    "tests/fixtures/docker-fastapi/Dockerfile",
    "tests/fixtures/docker-fastapi/app.py",
    "tests/fixtures/docker-fastapi/requirements.txt",
    "tests/results/2026-09-18-host-preflight.json",
    "tests/results/2026-09-18-skill-install-lifecycle.json",
    "tests/results/2026-09-17-skill-completion.json",
    "tests/results/2026-09-17-orient-fastapi-gcp.md",
    "tests/results/2026-09-17-behavioral-contracts.md",
    "tests/results/2026-09-18-codex-native-probe.json",
    "tests/results/2026-09-18-codex-native-output.json",
    "tests/results/2026-09-18-codex-native-runner-probe.json",
    "tests/results/2026-09-18-codex-native-runner-assessment.json",
    "tests/results/2026-09-18-skill-package-install-lifecycle.json",
    "tests/results/2026-09-18-skill-package-install-lifecycle.raw.json",
    "tests/results/2026-09-18-full-package-install-lifecycle.json",
    "tests/results/2026-09-18-full-package-install-lifecycle.raw.json",
    "tests/results/2026-09-18-behavioral-case-index.json",
    "tests/results/2026-09-18-skill-revision-assessment.json",
    ".terraform-version",
    "blueprints/container-api/VERSION",
    "blueprints/container-api/README.md",
    "blueprints/container-api/app/Dockerfile",
    "blueprints/container-api/app/app.py",
    "blueprints/container-api/tools/founderctl.py",
    "blueprints/container-api/terraform/bootstrap/.terraform.lock.hcl",
    "blueprints/container-api/terraform/bootstrap/main.tf",
    "blueprints/container-api/terraform/bootstrap/variables.tf",
    "blueprints/container-api/terraform/bootstrap/versions.tf",
    "blueprints/container-api/terraform/runtime/.terraform.lock.hcl",
    "blueprints/container-api/terraform/runtime/checks.tf",
    "blueprints/container-api/terraform/runtime/container.tf",
    "blueprints/container-api/terraform/runtime/network.tf",
    "blueprints/container-api/terraform/runtime/versions.tf",
    "blueprints/container-api/tests/test_app.py",
    "blueprints/container-api/tests/test_founderctl.py",
]

for relative in required_files:
    check((ROOT / relative).is_file(), f"missing required file: {relative}")

portable = load_json("plugin.json")
codex = load_json(".codex-plugin/plugin.json")
claude = load_json(".claude-plugin/plugin.json")

for relative, manifest in (
    ("plugin.json", portable),
    (".codex-plugin/plugin.json", codex),
    (".claude-plugin/plugin.json", claude),
):
    check(
        manifest.get("name") == "oci-founder-toolkit",
        f"{relative}: name must be oci-founder-toolkit",
    )
    check(
        bool(re.fullmatch(r"\d+\.\d+\.\d+", str(manifest.get("version", "")))),
        f"{relative}: version must be strict semver",
    )

versions = {portable.get("version"), codex.get("version"), claude.get("version")}
check(len(versions) == 1, "plugin manifest versions must match")
licenses = {portable.get("license"), codex.get("license"), claude.get("license")}
check(
    licenses == {"LicenseRef-OCI-Founder-Toolkit-Evaluation"},
    "evaluation manifests must reference the repository evaluation license notice",
)
check(
    portable.get("$schema") == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
    "plugin.json: unexpected or missing Agent Plugins schema",
)
check(
    hashlib.sha256((ROOT / "schemas/agent-plugin-1.0.0.schema.json").read_bytes()).hexdigest()
    == "0a4aad95ce337878ad38802ebf0daa3fde76abe3f65400c86bcbb1ec0b3ab883",
    "Agent Plugins 1.0.0 schema snapshot changed without a provenance review",
)
check(
    hashlib.sha256((ROOT / "third_party/licenses/Apache-2.0.txt").read_bytes()).hexdigest()
    == "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30",
    "Agent Plugins Apache-2.0 license text changed without a provenance review",
)
third_party_notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
check(
    "Agent Plugins manifest schema" in third_party_notices
    and "License: Apache License 2.0" in third_party_notices,
    "THIRD_PARTY_NOTICES.md: Agent Plugins schema license attribution is required",
)
requirements_validation = (ROOT / "requirements-validation.txt").read_text(encoding="utf-8")
check("PyYAML==6.0.2" in requirements_validation, "validation dependencies must pin PyYAML 6.0.2")
check(
    requirements_validation.count("--hash=sha256:") == 2,
    "validation dependencies must include the reviewed macOS and Linux wheel hashes",
)
check("skills" not in portable, "plugin.json: Agent Plugins v1 discovers skills; do not add a skills field")
check("skills" not in claude, ".claude-plugin/plugin.json: standard skills directory is auto-discovered")
check(codex.get("skills") == "./skills/", ".codex-plugin/plugin.json: skills path must be ./skills/")
check(
    "ship" not in str(portable.get("description", "")).lower(),
    "plugin.json: planning-only 0.1 description must not promise to ship",
)
check(
    portable.get("repository") == PROVISIONAL_REPOSITORY
    and portable.get("homepage") == PROVISIONAL_REPOSITORY,
    "plugin.json: provisional repository and homepage must match the selected GitHub repository",
)
check(
    codex.get("repository") == PROVISIONAL_REPOSITORY
    and codex.get("homepage") == PROVISIONAL_REPOSITORY,
    ".codex-plugin/plugin.json: provisional repository metadata is missing or inconsistent",
)

portable_allowed = {
    "$schema",
    "name",
    "version",
    "description",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
    "extensions",
}
check(
    not (set(portable) - portable_allowed),
    "plugin.json: contains fields outside Agent Plugins v1 schema",
)

gitignore_text = (ROOT / ".gitignore").read_text(encoding="utf-8")
gitignore_lines = {
    line.strip()
    for line in gitignore_text.splitlines()
    if line.strip() and not line.lstrip().startswith("#")
}
check("dist/" in gitignore_lines, ".gitignore: deterministic release outputs must remain untracked")
check("artifacts/*" in gitignore_lines, ".gitignore: presentation artifacts must remain untracked")
check(
    not any(line.startswith("!artifacts/") for line in gitignore_lines),
    ".gitignore: Oracle-internal presentations must not be eligible for a public-source commit",
)
for package_readme in ("packaging/README.skill.md", "packaging/README.full.md"):
    package_text = (ROOT / package_readme).read_text(encoding="utf-8").lower()
    check("not a public release" in package_text, f"{package_readme}: evaluation status must be explicit")
    check("project-scoped" in package_text, f"{package_readme}: qualified install scope must be explicit")
check(
    len(str(portable.get("name", ""))) <= 64
    and bool(re.fullmatch(r"(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", str(portable.get("name", "")))),
    "plugin.json: name must satisfy Agent Plugins v1 constraints",
)

skill_files = sorted((ROOT / "skills").glob("*/SKILL.md"))
check(bool(skill_files), "skills/: at least one immediate child skill is required")
all_skill_files = sorted((ROOT / "skills").rglob("SKILL.md"))
check(skill_files == all_skill_files, "skills must be immediate children of skills/ for portable discovery")

for skill_path in skill_files:
    frontmatter, text = parse_frontmatter(skill_path)
    relative = skill_path.relative_to(ROOT)
    name = frontmatter.get("name", "")
    description = frontmatter.get("description", "")
    check(name == skill_path.parent.name, f"{relative}: name must match the skill directory")
    check(bool(description), f"{relative}: description is required")
    check(len(description) <= 1024, f"{relative}: description exceeds 1024 characters")
    check("## Sources" in text, f"{relative}: a Sources section is required")
    version_match = re.search(r"(?m)^  version:\s*[\"']?([^\"'\s]+)", text)
    check(bool(version_match), f"{relative}: metadata.version is required")
    if version_match:
        check(
            version_match.group(1) == portable.get("version"),
            f"{relative}: metadata.version must match plugin manifests",
        )

    skill_root = skill_path.parent.resolve()
    for markdown in skill_path.parent.rglob("*.md"):
        markdown_text = markdown.read_text(encoding="utf-8")
        for raw_target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", markdown_text):
            target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target_path = target.split("#", 1)[0]
            if not target_path:
                continue
            resolved = (markdown.parent / target_path).resolve()
            try:
                resolved.relative_to(skill_root)
                inside_skill = True
            except ValueError:
                inside_skill = False
            check(
                inside_skill,
                f"{markdown.relative_to(ROOT)}: portable skill link escapes the skill directory: {target}",
            )

for path in ROOT.rglob("*"):
    if ignored(path):
        continue
    if path.is_symlink():
        ERRORS.append(f"{path.relative_to(ROOT)}: source packages must not contain symlinks")

markdown_link = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
for markdown in ROOT.rglob("*.md"):
    if ignored(markdown):
        continue
    text = markdown.read_text(encoding="utf-8")
    for raw_target in markdown_link.findall(text):
        target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target_path = target.split("#", 1)[0]
        if not target_path:
            continue
        resolved = (markdown.parent / target_path).resolve()
        check(
            resolved.exists(),
            f"{markdown.relative_to(ROOT)}: broken relative link: {target}",
        )

lock = load_json("upstream/oracle-skills.lock.json")
check(
    bool(re.fullmatch(r"[0-9a-f]{40}", str(lock.get("commit", "")))),
    "upstream lock: commit must be a 40-character lowercase SHA",
)
check(lock.get("vendored") is False, "upstream lock: version 0.1.0 must record vendored=false")
check(bool(lock.get("paths")), "upstream lock: selected paths are required")
check(lock.get("runtime_enforced") is False, "upstream lock: advisory runtime status must be explicit")
check(
    set(lock.get("paths", [])) == {"oci", "db", ".claude-plugin"},
    "upstream lock: dependency scope must cover routed OCI and DB domains",
)

upstream_reference = (
    ROOT / "skills/oci-founder/references/upstream-oracle-skills.md"
).read_text(encoding="utf-8")
upstream_provenance_values = {
    str(lock.get("commit", "")),
    str(lock.get("license_sha256", "")),
    *(str(value) for value in lock.get("trees", {}).values()),
}
for value in upstream_provenance_values:
    check(
        bool(value) and value in upstream_reference,
        f"upstream reference: reviewed lock value is missing: {value!r}",
    )
check(
    "fail closed at\nplanning level" in upstream_reference
    and "scripts/verify_oracle_skills_lock.py" in upstream_reference
    and "upstream/oracle-skills.lock.json" in upstream_reference,
    "upstream reference: standalone skill must fail closed without the full toolkit verifier and lock",
)
check(
    upstream_reference.find("verify_oracle_skills_lock.py")
    < upstream_reference.find("npx --yes skills@1.7.0 add"),
    "upstream reference: verification must precede installation",
)

def documented_add_commands(text: str) -> list[str]:
    collapsed = text.replace("\\\n", " ")
    return [
        line.strip()
        for line in collapsed.splitlines()
        if line.strip().startswith("npx ") and " add " in line
    ]


upstream_add_commands = documented_add_commands(upstream_reference)
check(
    len(upstream_add_commands) == 2,
    "upstream reference: expected exactly the reviewed OCI and DB add examples",
)
for command in upstream_add_commands:
    check(
        command.startswith("npx --yes skills@1.7.0 add "),
        "upstream reference: every installer example must pin skills@1.7.0",
    )
    check(
        len(re.findall(r"(?:^|\s)-a(?:\s|$)", command)) == 1,
        "upstream reference: every add command must target exactly one agent",
    )
    check(
        not re.search(r"(?:^|\s)-g(?:\s|$)", command),
        "upstream reference: global installation is forbidden",
    )

readme_text = (ROOT / "README.md").read_text(encoding="utf-8")
for command in documented_add_commands(readme_text):
    check(
        command.startswith("npx --yes skills@1.7.0 add ")
        and len(re.findall(r"(?:^|\s)-a(?:\s|$)", command)) == 1
        and not re.search(r"(?:^|\s)-g(?:\s|$)", command),
        "README: add examples must be pinned, project-scoped, and single-agent",
    )

install_evidence = load_json("tests/results/2026-09-18-skill-install-lifecycle.json")
check(
    install_evidence.get("kind") == "oci-founder-skill-install-lifecycle",
    "skill install evidence: unexpected kind",
)
check(
    install_evidence.get("schema_version") == "2.0",
    "skill install evidence: unexpected schema version",
)
check(
    install_evidence.get("status") == "pass_with_reservations",
    "skill install evidence: lifecycle did not pass",
)
check(
    install_evidence.get("scope") == "three-isolated-projects",
    "skill install evidence: each agent needs its own isolated project",
)
check(
    install_evidence.get("skills_cli", {}).get("observed_version") == "1.7.0",
    "skill install evidence: unexpected skills CLI version",
)
check(
    install_evidence.get("skills_cli", {}).get("version_exact_match") is True,
    "skill install evidence: skills CLI version must match exactly",
)
check(
    install_evidence.get("skills_cli", {}).get("integrity", {}).get("verified_before_execution") is True,
    "skill install evidence: skills CLI files were not verified before execution",
)
install_offline_cache = install_evidence.get("skills_cli", {}).get("offline_cache", {})
check(
    install_evidence.get("skills_cli", {}).get("source")
    == "npm-pinned-reviewed-files-offline-cache"
    and install_offline_cache.get("provided") is True
    and install_offline_cache.get("copied_before_npm_execution") is True
    and install_offline_cache.get("source_path_recorded") is False
    and install_offline_cache.get("source_tree_sha256")
    == install_offline_cache.get("copied_tree_sha256"),
    "skill install evidence: verified offline cache lineage is missing or inconsistent",
)
check(
    "--offline"
    in install_evidence.get("steps", {}).get("npm_ci_ignore_scripts", {}).get("argv", []),
    "skill install evidence: npm acquisition must record offline replay",
)
check(
    install_evidence.get("skills_cli", {}).get("dependency_lock", {}).get("verified") is True,
    "skill install evidence: reviewed dependency lock was not verified",
)
runtime_package = ROOT / "scripts/skills-cli-runtime/package.json"
runtime_lock = ROOT / "scripts/skills-cli-runtime/package-lock.json"
check(
    install_evidence.get("skills_cli", {}).get("dependency_lock", {}).get("observed_package_json_sha256")
    == hashlib.sha256(runtime_package.read_bytes()).hexdigest(),
    "skill install evidence: runtime package manifest fingerprint is stale",
)
check(
    install_evidence.get("skills_cli", {}).get("dependency_lock", {}).get("observed_lock_sha256")
    == hashlib.sha256(runtime_lock.read_bytes()).hexdigest(),
    "skill install evidence: runtime dependency lock fingerprint is stale",
)
current_skill_tree = tree_fingerprint(ROOT / "skills/oci-founder")
skill_revision_assessment = load_json(
    "tests/results/2026-09-18-skill-revision-assessment.json"
)
check(
    skill_revision_assessment.get("kind") == "oci-founder-skill-revision-assessment"
    and skill_revision_assessment.get("schema_version") == "1.0"
    and skill_revision_assessment.get("assertions_hidden_from_evaluators") is True,
    "skill revision assessment: unexpected identity, schema, or evaluator boundary",
)
check(
    skill_revision_assessment.get("historical_skill_tree_sha256")
    == "746cc9a3462ce96c067eedd91e848a905f04ed402b8f579836ce126c5b4d703f"
    and skill_revision_assessment.get("current_skill_tree_sha256") == current_skill_tree,
    "skill revision assessment: historical or current skill lineage is stale",
)
revision_cases = {
    str(case.get("id", "")): case
    for case in skill_revision_assessment.get("cases", [])
    if isinstance(case, dict)
}
check(
    set(revision_cases)
    == {
        "focused-runtime-choice",
        "skill-only-upstream-fail-closed",
        "full-toolkit-upstream-verification-first",
    }
    and all(case.get("status") == "pass" for case in revision_cases.values()),
    "skill revision assessment: targeted current-skill cases are incomplete",
)
for effect in ("file_writes", "network_calls", "oci_commands", "cloud_mutations"):
    check(
        skill_revision_assessment.get("effects", {}).get(effect) is False,
        f"skill revision assessment: {effect} must be false",
    )
check(
    skill_revision_assessment.get("model_sessions", {}).get("started") is True
    and skill_revision_assessment.get("model_sessions", {}).get("count") == 3
    and skill_revision_assessment.get("model_sessions", {}).get("host_native") is False,
    "skill revision assessment: content-forward model-session boundary is missing",
)
check(
    skill_revision_assessment.get("formal_native_gate") == "BLOCKED"
    and skill_revision_assessment.get("release_qualified") is False,
    "skill revision assessment: targeted content tests must not close native or release gates",
)
check(
    install_evidence.get("toolkit", {}).get("skill_tree_sha256_before")
    == current_skill_tree,
    "skill install evidence: source skill fingerprint is stale",
)
check(
    install_evidence.get("toolkit", {}).get("skill_tree_sha256_after")
    == current_skill_tree,
    "skill install evidence: post-run skill fingerprint is stale",
)
check(
    install_evidence.get("toolkit", {}).get("skill_source_unchanged") is True,
    "skill install evidence: source skill changed during qualification",
)
check(
    install_evidence.get("runner", {}).get("script_sha256")
    == hashlib.sha256((ROOT / "scripts/qualify_skill_install.py").read_bytes()).hexdigest(),
    "skill install evidence: runner fingerprint is stale",
)
environment_policy = install_evidence.get("environment_policy", {})
for key in (
    "source_environment_copied",
    "cloud_token_or_password_named_variables_inherited",
    "proxy_variables_inherited",
    "home_redirected",
):
    check(
        environment_policy.get(key) is False,
        f"skill install evidence: environment policy {key} must be false",
    )
check(
    environment_policy.get("strategy") == "allowlist",
    "skill install evidence: child environment must use an allowlist",
)

install_cases = install_evidence.get("cases", [])
check(isinstance(install_cases, list), "skill install evidence: cases must be a list")
case_by_agent = {
    case.get("agent"): case
    for case in install_cases
    if isinstance(case, dict) and isinstance(case.get("agent"), str)
}
expected_locations_by_agent = {
    "codex": [".agents/skills/oci-founder"],
    "cursor": [".agents/skills/oci-founder"],
    "claude-code": [".claude/skills/oci-founder"],
}
check(
    set(case_by_agent) == set(expected_locations_by_agent),
    "skill install evidence: exactly one case per supported agent is required",
)
for agent, expected_locations in expected_locations_by_agent.items():
    case = case_by_agent.get(agent, {})
    check(case.get("passed") is True, f"skill install evidence: {agent} case did not pass")
    check(
        case.get("remove_agent_filter_omitted") is True,
        f"skill install evidence: {agent} removal must omit the unreliable agent filter",
    )
    filtered_probe = case.get("agent_filtered_remove_probe", {})
    if agent in {"codex", "cursor"}:
        check(
            filtered_probe.get("required") is True
            and filtered_probe.get("performed") is True
            and filtered_probe.get("confirmed") is True
            and filtered_probe.get("command_reported_success") is True
            and filtered_probe.get("active_lock_entry_remained") is True,
            f"skill install evidence: {agent} filtered-remove limitation was not reproduced",
        )
        check(
            filtered_probe.get("remaining_install", {}).get("locations")
            == expected_locations,
            f"skill install evidence: {agent} filtered-remove probe did not retain the expected universal copy",
        )
    else:
        check(
            filtered_probe.get("required") is False
            and filtered_probe.get("performed") is False,
            "skill install evidence: Claude Code must not claim the universal-copy probe",
        )
    for phase in ("first_install", "second_install"):
        install = case.get(phase, {})
        check(
            install.get("locations") == expected_locations,
            f"skill install evidence: {agent} {phase} used an unexpected location",
        )
        check(
            install.get("exact_location_set") is True,
            f"skill install evidence: {agent} {phase} location set is not exact",
        )
        check(
            install.get("all_copies_match_source") is True,
            f"skill install evidence: {agent} {phase} tree mismatch",
        )
        check(
            install.get("regular_copy") is True and not install.get("copy_errors"),
            f"skill install evidence: {agent} {phase} is not a regular copied tree",
        )
    for key in ("first_list_contains_skill", "second_list_contains_skill"):
        check(
            case.get(key) is True,
            f"skill install evidence: {agent} {key} must be true",
        )
    for phase in ("first_remove_residuals", "final_remove_residuals"):
        residuals = case.get(phase, {})
        check(
            residuals.get("clean") is True,
            f"skill install evidence: {agent} {phase} left residuals",
        )
        check(
            residuals.get("skills_lock_empty_or_absent") is True,
            f"skill install evidence: {agent} {phase} left an active lock entry",
        )
        check(
            not residuals.get("unexpected_files")
            and not residuals.get("unexpected_directories")
            and not residuals.get("symlinks")
            and not residuals.get("remaining_skill_copies"),
            f"skill install evidence: {agent} {phase} residual allowlist failed",
        )

check(
    install_evidence.get("profile_safety", {}).get("observed_global_skill_targets_unchanged") is True,
    "skill install evidence: observed global skill targets changed",
)
check(
    install_evidence.get("profile_safety", {}).get("observed_global_skill_targets_contain_symlink") is False
    and install_evidence.get("profile_safety", {}).get("observed_global_skill_targets_acceptable") is True,
    "skill install evidence: observed global skill targets include a symlink or failed the closed safety gate",
)
check(
    install_evidence.get("effects", {}).get("toolkit_skill_source_changed") is False,
    "skill install evidence: toolkit skill source changed",
)
check(
    install_evidence.get("toolkit", {}).get("skill_tree_sha256_before")
    == tree_fingerprint(ROOT / "skills/oci-founder"),
    "skill install evidence: installed skill fingerprint is stale",
)
check(
    install_evidence.get("profile_safety", {}).get("global_install_attempted") is False,
    "skill install evidence: global install must not be attempted",
)
check(
    install_evidence.get("release_qualified") is False,
    "skill install evidence: project lifecycle alone cannot qualify a release",
)

native_runner_assessment = load_json(
    "tests/results/2026-09-18-codex-native-runner-assessment.json"
)
native_historical_skill_tree = native_runner_assessment.get(
    "historical_receipt", {}
).get("skill_tree_sha256")
native_codex = load_json("tests/results/2026-09-18-codex-native-probe.json")
native_output = load_json("tests/results/2026-09-18-codex-native-output.json")
native_installation = native_codex.get("installation", {})
native_replay = native_codex.get("native_replay", {})
native_qualification = native_codex.get("qualification", {})
check(
    native_codex.get("qualification_id") == "codex-native-orient-aws-fastapi-001",
    "Codex native evidence: unexpected qualification ID",
)
check(
    native_installation.get("source_tree_sha256") == native_historical_skill_tree
    and native_installation.get("installed_tree_sha256")
    == native_historical_skill_tree,
    "Codex historical native evidence: installed/source skill lineage is inconsistent",
)
check(
    native_installation.get("regular_copy") is True
    and native_installation.get("symlinks_found") is False
    and native_installation.get("removed") is True,
    "Codex native evidence: install or removal boundary failed",
)
check(
    native_replay.get("skill_discovered") is True
    and native_replay.get("structured_output_valid") is True
    and native_replay.get("explicit_invocation") is True,
    "Codex native evidence: explicit skill discovery probe failed",
)
check(
    native_replay.get("sandbox") == "read-only"
    and native_replay.get("file_change_events") == 0
    and native_replay.get("mcp_tool_calls") == 0
    and native_replay.get("web_searches") == 0
    and native_replay.get("cloud_commands_executed") is False
    and native_replay.get("files_changed") is False,
    "Codex native evidence: read-only effect boundary failed",
)
native_output_payload = (ROOT / "tests/results/2026-09-18-codex-native-output.json").read_bytes().rstrip(b"\n")
check(
    hashlib.sha256(native_output_payload).hexdigest() == native_replay.get("final_output_sha256"),
    "Codex native evidence: structured output hash mismatch",
)
check(
    native_output.get("skill_name") == "oci-founder"
    and native_output.get("skill_version") == portable.get("version")
    and native_output.get("skill_discovered") is True
    and native_output.get("cloud_commands_executed") is False
    and native_output.get("files_changed") is False,
    "Codex native evidence: structured output safety or identity mismatch",
)
check(
    native_qualification.get("q2_probe", {}).get("status") == "PASS"
    and native_qualification.get("q3_probe", {}).get("status") == "PASS"
    and native_qualification.get("q2_formal_gate", {}).get("status") == "BLOCKED"
    and native_qualification.get("q3_formal_gate", {}).get("status") == "BLOCKED",
    "Codex native evidence: probe/formal-gate distinction is missing",
)

native_runner = load_json("tests/results/2026-09-18-codex-native-runner-probe.json")
native_runner_path = ROOT / "tests/results/2026-09-18-codex-native-runner-probe.json"
native_runner_codex = native_runner.get("codex", {})
native_runner_events = native_runner_codex.get("event_summary", {})
native_runner_effects = native_runner.get("effects", {})
native_runner_environment = native_runner.get("environment_policy", {})
native_runner_installation = native_runner.get("installation", {})
native_runner_removal = native_runner.get("removal", {})
check(
    native_runner.get("kind") == "oci-founder-codex-native-probe"
    and native_runner.get("schema_version") == "1.0"
    and native_runner.get("status") == "pass_with_reservations"
    and native_runner.get("release_qualified") is False,
    "Codex historical native runner evidence: unexpected identity, schema, status, or release claim",
)
check(
    native_runner.get("runner", {}).get("script_sha256")
    == native_runner_assessment.get("historical_receipt", {}).get("runner_sha256")
    == "1151f8cd8863e32a2cfc57645f298c011cad28454ee599366aa641447ea723ed",
    "Codex historical native runner evidence: runner lineage is inconsistent",
)
check(
    native_runner.get("probe_q2") == "PASS"
    and native_runner.get("probe_q3") == "PASS"
    and native_runner.get("formal_q2") == "BLOCKED"
    and native_runner.get("formal_q3") == "BLOCKED",
    "Codex historical native runner evidence: recorded probe/formal-gate distinction is missing",
)
check(
    native_runner_installation.get("source_tree_sha256") == native_historical_skill_tree
    and native_runner_installation.get("tree_sha256", {}).get(".agents/skills/oci-founder")
    == native_historical_skill_tree
    and native_runner_installation.get("locations") == [".agents/skills/oci-founder"]
    and native_runner_installation.get("copy_count") == 1
    and native_runner_installation.get("exact_location_set") is True
    and native_runner_installation.get("all_copies_match_source") is True
    and native_runner_installation.get("regular_copy") is True,
    "Codex historical native runner evidence: exact project-scoped install boundary failed",
)
check(
    native_runner_codex.get("exit_code") == 0
    and native_runner_codex.get("timed_out") is False
    and native_runner_codex.get("structured_output_valid") is True
    and native_runner_codex.get("structured_output_errors") == [],
    "Codex historical native runner evidence: native model session or structured response failed",
)
check(
    native_runner_events.get("invalid_json_lines") == 0
    and native_runner_events.get("completed_command_executions", 0) > 0
    and native_runner_events.get("forbidden_executables_observed") == []
    and native_runner_events.get("deny_shims_triggered") == []
    and native_runner_events.get("file_change_events") == 0
    and native_runner_events.get("mcp_tool_calls") == 0
    and native_runner_events.get("web_searches") == 0,
    "Codex historical native runner evidence: event-level effect boundary failed",
)
for effect in (
    "cloud_mutation_attempted",
    "observed_global_skill_targets_changed",
    "oci_command_executed",
    "project_tree_changed_during_model_session",
    "source_skill_changed",
):
    check(
        native_runner_effects.get(effect) is False,
        f"Codex historical native runner evidence: {effect} must be false",
    )
check(
    native_runner_environment.get("strategy") == "allowlist"
    and native_runner_environment.get("source_environment_copied") is False
    and native_runner_environment.get("cloud_token_or_password_named_variables_inherited") is False
    and native_runner_environment.get("proxy_variables_inherited") is False
    and native_runner_environment.get("home_redirected") is False,
    "Codex historical native runner evidence: child environment policy is unsafe",
)
check(
    native_runner_removal.get("clean") is True
    and native_runner_removal.get("fixture_unchanged") is True
    and native_runner_removal.get("remaining_skill_copies") == []
    and native_runner_removal.get("symlinks") == []
    and native_runner_removal.get("unexpected_agent_directories") == []
    and native_runner_removal.get("skills_lock_empty_or_absent") is True,
    "Codex historical native runner evidence: removal or disposable-fixture boundary failed",
)
check(
    native_runner.get("skills_cli", {}).get("expected_version") == "1.7.0"
    and native_runner.get("skills_cli", {}).get("integrity", {}).get("verified_before_execution") is True
    and native_runner.get("skills_cli", {}).get("dependency_lock", {}).get("verified") is True,
    "Codex historical native runner evidence: reviewed installer runtime was not verified",
)

current_native_runner_sha256 = hashlib.sha256(
    (ROOT / "scripts/probe_codex_native.py").read_bytes()
).hexdigest()
assessment_current = native_runner_assessment.get("current_runner", {})
assessment_historical = native_runner_assessment.get("historical_receipt", {})
assessment_renewal = native_runner_assessment.get("renewal", {})
check(
    native_runner_assessment.get("kind") == "oci-founder-codex-native-runner-assessment"
    and native_runner_assessment.get("schema_version") == "1.0",
    "Codex native runner assessment: unexpected identity or schema",
)
check(
    assessment_current.get("path") == "scripts/probe_codex_native.py"
    and assessment_current.get("sha256") == current_native_runner_sha256
    and assessment_current.get("skill_tree_sha256") == current_skill_tree
    and assessment_current.get("unit_contract_count") == 12
    and assessment_current.get("unit_contracts_passed") is True
    and assessment_current.get("native_rerun_status") == "BLOCKED",
    "Codex native runner assessment: hardened runner status or fingerprint is stale",
)
check(
    assessment_historical.get("path")
    == "tests/results/2026-09-18-codex-native-runner-probe.json"
    and assessment_historical.get("sha256")
    == hashlib.sha256(native_runner_path.read_bytes()).hexdigest()
    and assessment_historical.get("recorded_status") == native_runner.get("status")
    and assessment_historical.get("recorded_probe_q2") == native_runner.get("probe_q2")
    and assessment_historical.get("recorded_probe_q3") == native_runner.get("probe_q3")
    and assessment_historical.get("normalized_q2") == "PASS_WITH_RESERVATIONS"
    and assessment_historical.get("normalized_q3") == "PARTIAL",
    "Codex native runner assessment: historical receipt binding or normalization is invalid",
)
check(
    assessment_renewal.get("status") == "BLOCKED"
    and assessment_renewal.get("model_session_started") is False
    and assessment_renewal.get("cloud_mutation_attempted") is False
    and native_runner_assessment.get("formal_q2") == "BLOCKED"
    and native_runner_assessment.get("formal_q3") == "BLOCKED"
    and native_runner_assessment.get("release_qualified") is False,
    "Codex native runner assessment: renewal or formal-gate status is overstated",
)

host_preflight = load_json("tests/results/2026-09-18-host-preflight.json")
if not ARGS.skip_host_preflight_evidence:
    check(
        host_preflight.get("kind") == "oci-founder-host-preflight"
        and host_preflight.get("schema_version") == "1.0"
        and host_preflight.get("scope") == "read_only",
        "host preflight evidence: unexpected identity, schema, or scope",
    )
    check(
        host_preflight.get("repo_validation", {}).get("status") == "passed"
        and host_preflight.get("repo_validation", {}).get("mode")
        == "source-without-host-preflight-evidence"
        and "--skip-host-preflight-evidence"
        in host_preflight.get("repo_validation", {}).get("probe", {}).get("argv", []),
        "host preflight evidence: repository validation did not use the reproducible renewal mode",
    )
    host_toolkit = host_preflight.get("toolkit", {})
    check(
        host_toolkit.get("skill_tree_sha256") == current_skill_tree,
        "host preflight evidence: skill fingerprint is stale",
    )
    for relative in ("plugin.json", ".codex-plugin/plugin.json", ".claude-plugin/plugin.json"):
        check(
            host_toolkit.get("manifest_sha256", {}).get(relative)
            == hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(),
            f"host preflight evidence: manifest fingerprint is stale for {relative}",
        )
    for relative in ("scripts/qualify_hosts.py", "scripts/validate.py"):
        check(
            host_toolkit.get("validation_tool_sha256", {}).get(relative)
            == hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(),
            f"host preflight evidence: validation-tool fingerprint is stale for {relative}",
        )
    check(
        host_preflight.get("development_validator_runtime", {}).get("status") == "passed"
        and host_preflight.get("development_validator_runtime", {}).get("pyyaml_version") == "6.0.2"
        and host_preflight.get("development_validator_runtime", {}).get("requirements_sha256")
        == hashlib.sha256((ROOT / "requirements-validation.txt").read_bytes()).hexdigest(),
        "host preflight evidence: reviewed validator runtime is missing or stale",
    )
    for name in ("codex_plugin_creator", "portable_skill"):
        check(
            host_preflight.get("hosts", {}).get("codex", {}).get("development_validators", {}).get(name, {}).get("status")
            == "passed",
            f"host preflight evidence: development validator {name} did not pass",
        )
    preflight_policy = host_preflight.get("environment", {}).get("subprocess_policy", {})
    check(
        preflight_policy.get("strategy") == "allowlist"
        and preflight_policy.get("cloud_token_or_password_named_variables_inherited") is False
        and preflight_policy.get("raw_environment_recorded") is False,
        "host preflight evidence: subprocess environment policy is unsafe",
    )
    for effect in (
        "installation_attempted",
        "host_configuration_changed",
        "model_session_started",
        "oci_command_executed",
        "cloud_mutation_attempted",
    ):
        check(
            host_preflight.get("summary", {}).get(effect) is False,
            f"host preflight evidence: {effect} must be false",
        )
    check(
        host_preflight.get("summary", {}).get("release_qualified") is False,
        "host preflight evidence: inventory must not claim release qualification",
    )

blueprint_version = (ROOT / "blueprints/container-api/VERSION").read_text(encoding="utf-8").strip()
check(
    blueprint_version == "0.2.0-preview.3",
    "Container API blueprint must remain at the reviewed 0.2.0-preview.3 contract",
)
check(
    (ROOT / ".terraform-version").read_text(encoding="utf-8").strip() == "1.16.3",
    ".terraform-version must pin Terraform 1.16.3",
)

bootstrap_root = ROOT / "blueprints/container-api/terraform/bootstrap"
runtime_root = ROOT / "blueprints/container-api/terraform/runtime"
for label, terraform_root in (("bootstrap", bootstrap_root), ("runtime", runtime_root)):
    versions_text = (terraform_root / "versions.tf").read_text(encoding="utf-8")
    check('required_version = "= 1.16.3"' in versions_text, f"{label}: Terraform must be pinned exactly")
    check('version = "= 9.2.0"' in versions_text, f"{label}: OCI provider must be pinned exactly")
    provider_lock = (terraform_root / ".terraform.lock.hcl").read_text(encoding="utf-8")
    check('version     = "9.2.0"' in provider_lock, f"{label}: provider lock must select OCI 9.2.0")
    check('constraints = "9.2.0"' in provider_lock, f"{label}: provider lock must record the exact constraint")

check(
    (bootstrap_root / ".terraform.lock.hcl").read_bytes()
    == (runtime_root / ".terraform.lock.hcl").read_bytes(),
    "bootstrap and runtime provider lock files must be identical",
)

bootstrap_hcl = "\n".join(path.read_text(encoding="utf-8") for path in sorted(bootstrap_root.glob("*.tf")))
runtime_hcl = "\n".join(path.read_text(encoding="utf-8") for path in sorted(runtime_root.glob("*.tf")))
all_hcl = bootstrap_hcl + "\n" + runtime_hcl

check('resource "oci_identity_' not in runtime_hcl, "runtime stack must contain no OCI IAM resource")
check("manage all-resources" not in all_hcl.lower(), "Terraform must not grant manage all-resources")
check("terraform_remote_state" not in all_hcl, "preview stacks must not couple state through terraform_remote_state")
check('provisioner "local-exec"' not in all_hcl, "Terraform must not use local-exec")
check('provisioner "remote-exec"' not in all_hcl, "Terraform must not use remote-exec")
check('is_public      = false' in bootstrap_hcl, "OCIR repository must be private")
check('is_immutable   = true' in bootstrap_hcl, "OCIR repository must be immutable")
check("where target.repo.name" in bootstrap_hcl, "image-pull IAM must be repository-scoped")
check(
    "${oci_identity_dynamic_group.container_instances.name}" in bootstrap_hcl,
    "image-pull IAM policy must depend directly on its dynamic group",
)
check(
    "budget_target_verified_without_existing_budget" in bootstrap_hcl,
    "bootstrap must require the no-existing-budget preflight",
)
check('is_public_ip_assigned = false' in runtime_hcl, "Container Instance VNIC must refuse a public IP")
check('is_resource_principal_disabled = true' in runtime_hcl, "sample app must not receive a resource principal")
check('is_non_root_user_check_enabled = true' in runtime_hcl, "container must enforce a non-root user")
check('is_root_file_system_readonly   = true' in runtime_hcl, "container root filesystem must be read-only")
check('drop_capabilities = ["ALL"]' in runtime_hcl, "container must drop all Linux capabilities")
check('destination               = "169.254.169.254/32"' in runtime_hcl, "DNS egress must target the OCI VCN resolver")
check("oci_core_service_gateway.oracle_services" in runtime_hcl, "private OCIR access must use a Service Gateway")
check("approved_repository_path" in runtime_hcl, "runtime image must bind to the bootstrap repository path")
check("network_cidr_contract" in runtime_hcl, "Terraform must enforce the network CIDR contract")
check("precondition" in runtime_hcl, "network CIDR contract must use a blocking precondition")
check("can(cidrnetmask" in runtime_hcl, "network CIDR contract must reject non-IPv4 CIDRs")
check('check "network_cidr_contract"' not in runtime_hcl, "network CIDR contract must not use advisory check blocks")
check(
    "`temporary-upstream-gap`" in (ROOT / "blueprints/container-api/README.md").read_text(encoding="utf-8"),
    "temporary Container Instances service knowledge must retain its upstream-gap label",
)

dockerfile = (ROOT / "blueprints/container-api/app/Dockerfile").read_text(encoding="utf-8")
check(bool(re.search(r"(?m)^ARG PYTHON_IMAGE$", dockerfile)), "Dockerfile base image argument must have no default")
check("FROM ${PYTHON_IMAGE}" in dockerfile, "Dockerfile must consume the reviewed base image argument")
check("USER 65532:65532" in dockerfile, "Dockerfile must run as the non-root runtime user")

for relative in (
    "blueprints/container-api/app/app.py",
    "blueprints/container-api/tools/founderctl.py",
    "blueprints/container-api/tests/test_app.py",
    "blueprints/container-api/tests/test_founderctl.py",
):
    source = (ROOT / relative).read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=relative)
    except SyntaxError as exc:
        ERRORS.append(f"{relative}: invalid Python: {exc}")
        continue
    check(not any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "system" for node in ast.walk(tree)), f"{relative}: os.system-style execution is forbidden")
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in {"run", "Popen", "call", "check_call", "check_output"}:
            continue
        shell_values = [keyword.value for keyword in node.keywords if keyword.arg == "shell"]
        check(
            not any(isinstance(value, ast.Constant) and value.value is True for value in shell_values),
            f"{relative}: subprocess shell=True is forbidden",
        )

founderctl_text = (ROOT / "blueprints/container-api/tools/founderctl.py").read_text(encoding="utf-8")
check(
    '[str(executable_path), "show", "-json", str(path)]' in founderctl_text,
    "founderctl must decode exact plans/states with argv-safe terraform show",
)
check('TERRAFORM_VERSION = "1.16.3"' in founderctl_text, "founderctl must verify the exact Terraform version")
check('SCHEMA_VERSION = "1.2"' in founderctl_text, "founderctl artifact schema must match preview.3")
check("plan_target_variable_mismatch" in founderctl_text, "plan reviews must bind embedded variables to the target")
check("provider_target_binding_mismatch" in founderctl_text, "plan reviews must bind providers to target regions")
check('"oci_profile": oci_profile' in founderctl_text, "approval targets must bind the OCI profile")
check("incomplete_or_unexpected_resource_set" in founderctl_text, "plan reviews must require the complete resource set")
check("decode_saved_state" in founderctl_text, "receipts must decode one raw Terraform state snapshot")
check('"status": "locally_verified"' in founderctl_text, "local receipts must not claim signed verification")
check("resource_ids" in founderctl_text and "state_lineage_mismatch" in founderctl_text, "teardown must bind state lineage and resource identifiers")
check("validate_state_security_contract" in founderctl_text, "receipt and teardown must revalidate security-critical state")
check(
    "plan_relationship_blockers" in founderctl_text
    and "planned_gateway_route_relationship_mismatch" in founderctl_text,
    "plan review must reject concrete relationship values outside the reviewed graph",
)
check(
    "logging_source_resource_reference_mismatch" in founderctl_text
    and "planned_monitoring_query_relationship_mismatch" in founderctl_text,
    "plan review must bind logging, notification, and alarm relationships",
)
check(
    "iac_source_evidence" in founderctl_text and '"iac_source_manifest"' in founderctl_text,
    "approval artifacts must bind the reviewed Terraform source manifest",
)
check(
    "saved_plan_source_evidence" in founderctl_text
    and 'tfconfig/m-/' in founderctl_text
    and "saved plan source snapshot does not match" in founderctl_text,
    "saved-plan provenance must compare its embedded Terraform snapshot with reviewed sources",
)
check(
    "provider lock does not match the reviewed saved plan" in founderctl_text,
    "deployment receipts must bind the supplied provider lock to the saved plan snapshot",
)
check(
    "RUNTIME_CHILD_READBACK_OUTPUTS" in founderctl_text
    and "readback_resource_ids" in founderctl_text,
    "destroy readback must include child container and VNIC identifiers",
)
check("destroy_plan_resource_id_mismatch" in founderctl_text, "destroy plans must match exact current resource identifiers")
check(
    "{iac_source_hash[:16]} {receipt_hash[:16]}" in founderctl_text
    and "{current_state_hash[:16]}" in founderctl_text,
    "destroy approval must bind the IaC source, receipt, and current state hashes",
)
check(
    "os.replace(" in founderctl_text and "src_dir_fd=parent_descriptor" in founderctl_text,
    "founderctl outputs must use directory-bound atomic replacement",
)
check(
    "O_NOFOLLOW" in founderctl_text and "dir_fd=parent_descriptor" in founderctl_text,
    "founderctl outputs must reject symlink traversal through every path component",
)
check("url_sha256" in founderctl_text, "smoke evidence must bind to the deployed URL")
check("runtime_destroy_evidence_missing" in founderctl_text, "bootstrap teardown must require runtime destroy evidence")
check(
    "oci-destroy-readback-evidence" in founderctl_text
    and "runtime_destroy_readback_evidence_invalid" in founderctl_text,
    "bootstrap teardown must validate exact-ID OCI readback evidence",
)
check(
    "repository_path_output_reference_mismatch" in founderctl_text
    and "repository_contract" in founderctl_text,
    "bootstrap receipts must derive the OCIR repository path",
)

smoke_path = ROOT / "tests/prompts/smoke.jsonl"
if smoke_path.is_file():
    cases = []
    case_ids: set[str] = set()
    allowed_modes = {"answer", "assess", "generate", "execute", "diagnose", "teardown"}
    allowed_journeys = {"orient", "bootstrap", "ship", "verify", "operate", "teardown", "graduate"}
    allowed_selection = {"implicit", "explicit"}
    allowed_mutation_ceilings = {"read-only", "generate"}
    for line_number, line in enumerate(smoke_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            case = json.loads(line)
        except json.JSONDecodeError as exc:
            ERRORS.append(f"tests/prompts/smoke.jsonl:{line_number}: invalid JSON: {exc}")
            continue
        cases.append(case)
        case_id = str(case.get("id", ""))
        check(bool(case_id), f"smoke case {line_number}: id is required")
        check(case_id not in case_ids, f"smoke case {line_number}: duplicate id {case_id!r}")
        case_ids.add(case_id)
        check(bool(case.get("prompt")), f"smoke case {line_number}: prompt is required")
        check(bool(case.get("assertions")), f"smoke case {line_number}: assertions are required")
        check(case.get("mode") in allowed_modes, f"smoke case {line_number}: invalid mode")
        check(case.get("journey") in allowed_journeys, f"smoke case {line_number}: invalid journey")
        check(case.get("selection") in allowed_selection, f"smoke case {line_number}: invalid selection")
        check(
            case.get("mutation_ceiling") in allowed_mutation_ceilings,
            f"smoke case {line_number}: replay must remain read-only or generate-only",
        )
        check(bool(case.get("expected_route")), f"smoke case {line_number}: expected_route is required")
    check(len(cases) >= 5, "at least five behavioral smoke cases are required")

    structured_evaluation = load_json("tests/results/2026-09-17-skill-completion.json")
    check(
        structured_evaluation.get("evaluation_surface")
        == "codex-subagent-content-forward-test",
        "skill completion evidence: unexpected evaluation surface",
    )
    check(
        structured_evaluation.get("assertions_hidden_from_evaluators") is True,
        "skill completion evidence: assertions must be hidden from evaluators",
    )
    check(
        structured_evaluation.get("skill_tree_sha256")
        == native_historical_skill_tree,
        "historical skill completion evidence: skill lineage is inconsistent",
    )
    effects = structured_evaluation.get("effects", {})
    for effect in ("file_writes", "network_calls", "oci_commands", "cloud_mutations"):
        check(effects.get(effect) is False, f"skill completion evidence: {effect} must be false")

    structured_results: dict[str, dict] = {}
    case_by_id = {str(case.get("id", "")): case for case in cases}
    for result in structured_evaluation.get("cases", []):
        result_id = str(result.get("id", ""))
        check(result_id in case_by_id, f"skill completion evidence: unknown case {result_id!r}")
        check(result_id not in structured_results, f"skill completion evidence: duplicate case {result_id!r}")
        structured_results[result_id] = result
        expected_assertions = len(case_by_id.get(result_id, {}).get("assertions", []))
        check(result.get("status") == "pass", f"skill completion evidence: case {result_id!r} did not pass")
        check(
            result.get("assertions_passed") == expected_assertions,
            f"skill completion evidence: case {result_id!r} assertion count mismatch",
        )
        check(
            result.get("assertions_failed") == 0,
            f"skill completion evidence: case {result_id!r} has failed assertions",
        )
        check(bool(result.get("evaluator")), f"skill completion evidence: case {result_id!r} lacks evaluator")
        check(bool(result.get("evidence")), f"skill completion evidence: case {result_id!r} lacks evidence")

    behavioral_index = load_json("tests/results/2026-09-18-behavioral-case-index.json")
    check(
        behavioral_index.get("kind") == "oci-founder-behavioral-case-index"
        and behavioral_index.get("schema_version") == "1.0",
        "behavioral case index: unexpected identity or schema",
    )
    check(
        behavioral_index.get("toolkit_version") == portable.get("version")
        and behavioral_index.get("skill_tree_sha256") == native_historical_skill_tree,
        "historical behavioral case index: toolkit version or skill lineage is inconsistent",
    )
    indexed_results = {
        str(result.get("id", "")): result
        for result in behavioral_index.get("cases", [])
        if isinstance(result, dict)
    }
    check(
        len(indexed_results) == len(behavioral_index.get("cases", [])),
        "behavioral case index: duplicate or invalid case entries",
    )
    check(
        set(indexed_results) == set(case_by_id),
        "behavioral case index: indexed cases must exactly match the prompt matrix",
    )
    for case_id, case in case_by_id.items():
        result = indexed_results.get(case_id, {})
        check(
            result.get("prompt_sha256")
            == hashlib.sha256(str(case.get("prompt", "")).encode("utf-8")).hexdigest(),
            f"behavioral case index: prompt hash is stale for {case_id!r}",
        )
        check(
            result.get("assertion_count") == len(case.get("assertions", []))
            and result.get("assertions_passed") == len(case.get("assertions", []))
            and result.get("assertions_failed") == 0
            and result.get("status") == "pass_recorded",
            f"behavioral case index: recorded result is incomplete for {case_id!r}",
        )
        for field in ("selection", "mode", "journey", "expected_route", "mutation_ceiling"):
            check(
                result.get(field) == case.get(field),
                f"behavioral case index: {field} mismatch for {case_id!r}",
            )
    coverage = behavioral_index.get("coverage", {})
    check(
        coverage.get("case_count") == len(cases)
        and coverage.get("recorded_pass_count") == len(cases),
        "behavioral case index: recorded coverage must include every case",
    )
    check(
        coverage.get("native_complete_count") == 0
        and coverage.get("transcript_bound_count") == 0
        and coverage.get("tool_trace_bound_count") == 0
        and behavioral_index.get("formal_native_gate") == "BLOCKED",
        "behavioral case index: non-native evidence must not close the native gate",
    )
    for source in behavioral_index.get("sources", {}).values():
        source_path = ROOT / str(source.get("path", ""))
        check(source_path.is_file(), f"behavioral case index: missing source {source_path}")
        if source_path.is_file():
            check(
                hashlib.sha256(source_path.read_bytes()).hexdigest() == source.get("sha256"),
                f"behavioral case index: source fingerprint is stale for {source_path.relative_to(ROOT)}",
            )

for path in ROOT.rglob("*"):
    if not path.is_file() or ignored(path):
        continue
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    forbidden_patterns = (
        "[" + "TODO:",
        "BEGIN " + "PRIVATE KEY",
        "BEGIN " + "OPENSSH PRIVATE KEY",
    )
    for pattern in forbidden_patterns:
        check(pattern not in text, f"{path.relative_to(ROOT)}: forbidden placeholder or secret marker {pattern!r}")

if ERRORS:
    print(f"Validation failed with {len(ERRORS)} error(s):", file=sys.stderr)
    for error in ERRORS:
        print(f"- {error}", file=sys.stderr)
    sys.exit(1)

print(f"OCI Founder Toolkit validation passed ({CHECKS} checks).")
