#!/usr/bin/env python3
"""Qualify the project-scoped OCI Founder skill installation lifecycle.

The runner creates one disposable Git project per supported agent, exercises
install/list/remove/reinstall/remove with a pinned Agent Skills CLI, compares
every copied skill with the reviewed source, and rejects stale residual files.
It never performs a global install or starts a host-native model session.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "oci-founder"
SKILLS_CLI_VERSION = "1.7.0"
AGENTS = ("codex", "cursor", "claude-code")
EXPECTED_INSTALL_LOCATIONS = {
    "codex": [".agents/skills/oci-founder"],
    "cursor": [".agents/skills/oci-founder"],
    "claude-code": [".claude/skills/oci-founder"],
}
EXPECTED_RESIDUAL_DIRECTORIES = {
    "codex": [".agents", ".agents/skills"],
    "cursor": [".agents", ".agents/skills"],
    "claude-code": [".claude", ".claude/skills"],
}
DEFAULT_TIMEOUT_SECONDS = 180
ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
SEMVER_OUTPUT = re.compile(r"^(\d+\.\d+\.\d+)$")
CLI_RUNTIME_SOURCE = ROOT / "scripts" / "skills-cli-runtime"
EXPECTED_RUNTIME_PACKAGE_JSON_SHA256 = "3a35717c49e02a025fdad96301cf2438c014ee941ee35008eb038ab376e5a09a"
EXPECTED_RUNTIME_LOCK_SHA256 = "2fbf496c854780bbf7be13d08c7806b0479c60483381d657d08755b563630701"
EXPECTED_SKILLS_DIST_INTEGRITY = "sha512-OfePnDft+Xt9/tCoHdCUe5fkM8i+Q3QOSQO53hm7mKtsXyvc+CKOAAliVWZ484HS3cWx+6r+ob0AArixs3jYXw=="

# Reviewed contents of the npm `skills@1.7.0` package. The npm acquisition
# step uses --ignore-scripts; none of these package files is executed unless
# every hash and the package manifest match.
EXPECTED_NPM_FILE_HASHES = {
    "package.json": "d912e2f2fa141ba3d65b80e7374827d92ac4c6b81fdd63dcb80fdd641809f5d2",
    "bin/cli.mjs": "cda9a4dd5cd209c6f1dc551feacbaef503cefb5d8986d3c4cab9a95e1bbc47e6",
    "dist/cli.mjs": "fde68534019765fb69510a0038ca7df2810a6ffed4c26fef9beabdcf6cc6701c",
}

INHERITED_ENV_ALLOWLIST = (
    "PATH",
    "HOME",
    "USER",
    "LOGNAME",
    "SHELL",
    "TMPDIR",
    "TMP",
    "TEMP",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "TERM",
    "COLORTERM",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "NODE_EXTRA_CA_CERTS",
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def tree_fingerprint(root: Path) -> str:
    if root.is_symlink():
        raise ValueError(f"refusing to fingerprint symlink root: {root}")
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"refusing to fingerprint symlink: {path}")
    digest = hashlib.sha256()
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update((path.stat().st_mode & 0o777).to_bytes(4, "big"))
        content = path.read_bytes()
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def redact_text(value: str, replacements: Sequence[tuple[Path, str]]) -> str:
    redacted = value
    candidates: set[tuple[str, str]] = set()
    for path, label in replacements:
        candidates.add((str(path), label))
        candidates.add((str(path.resolve(strict=False)), label))
    ordered = sorted(
        candidates,
        key=lambda item: len(item[0]),
        reverse=True,
    )
    for raw, label in ordered:
        redacted = redacted.replace(raw, label)
    return redacted


def command_result(
    argv: Sequence[str],
    *,
    cwd: Path,
    env: dict[str, str],
    replacements: Sequence[tuple[Path, str]],
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    started = datetime.now(timezone.utc)
    try:
        completed = subprocess.run(
            [str(argument) for argument in argv],
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        stdout = redact_text(completed.stdout, replacements)
        stderr = redact_text(completed.stderr, replacements)
        exit_code: int | None = completed.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        raw_stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        raw_stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        stdout = redact_text(raw_stdout, replacements)
        stderr = redact_text(raw_stderr, replacements)
        exit_code = None
        timed_out = True
    duration_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
    return {
        "argv": [redact_text(str(argument), replacements) for argument in argv],
        "exit_code": exit_code,
        "timed_out": timed_out,
        "duration_ms": duration_ms,
        "stdout_sha256": sha256_bytes(stdout.encode("utf-8")),
        "stderr_sha256": sha256_bytes(stderr.encode("utf-8")),
        "stdout_excerpt": stdout[:8_000],
        "stderr_excerpt": stderr[:4_000],
    }


def command_passed(result: Mapping[str, Any]) -> bool:
    return result.get("exit_code") == 0 and result.get("timed_out") is False


def parse_json_suffix(value: str) -> Any:
    clean = ANSI_ESCAPE.sub("", value).strip()
    for index, character in enumerate(clean):
        if character not in "[{":
            continue
        try:
            return json.loads(clean[index:])
        except json.JSONDecodeError:
            continue
    raise ValueError("command output did not contain a JSON suffix")


def parse_exact_version(value: str) -> str:
    lines = [line.strip() for line in ANSI_ESCAPE.sub("", value).splitlines() if line.strip()]
    if len(lines) != 1:
        raise ValueError("version output must contain exactly one non-empty line")
    match = SEMVER_OUTPUT.fullmatch(lines[0])
    if not match:
        raise ValueError("version output is not an exact semantic version")
    return match.group(1)


def installed_copies(project_root: Path) -> list[Path]:
    copies: list[Path] = []
    for path in project_root.rglob(SKILL_NAME):
        if ".git" in path.relative_to(project_root).parts:
            continue
        if path.is_dir() and (path / "SKILL.md").is_file():
            copies.append(path)
    return sorted(copies)


def global_target_map(user_home: Path | None = None) -> dict[str, Path]:
    root = user_home or Path.home()
    return {
        f"~/.agents/skills/{SKILL_NAME}": root / ".agents" / "skills" / SKILL_NAME,
        f"~/.cursor/skills/{SKILL_NAME}": root / ".cursor" / "skills" / SKILL_NAME,
        f"~/.codex/skills/{SKILL_NAME}": root / ".codex" / "skills" / SKILL_NAME,
        f"~/.claude/skills/{SKILL_NAME}": root / ".claude" / "skills" / SKILL_NAME,
    }


def global_snapshot(user_home: Path | None = None) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for label, path in global_target_map(user_home).items():
        exists = path.is_dir()
        is_symlink = path.is_symlink()
        result[label] = {
            "exists": exists,
            "is_symlink": is_symlink,
            "tree_sha256": tree_fingerprint(path) if exists and not is_symlink else None,
        }
    return result


def global_snapshots_acceptable(
    before: Mapping[str, Mapping[str, Any]],
    after: Mapping[str, Mapping[str, Any]],
) -> bool:
    snapshots_match = before == after
    contains_symlink = any(
        bool(entry.get("is_symlink"))
        for snapshot in (before, after)
        for entry in snapshot.values()
    )
    return snapshots_match and not contains_symlink


def sanitized_environment(
    qualification_root: Path,
    source: Mapping[str, str] | None = None,
) -> tuple[dict[str, str], dict[str, Any]]:
    source_env = source if source is not None else os.environ
    inherited = {
        key: source_env[key]
        for key in INHERITED_ENV_ALLOWLIST
        if key in source_env and source_env[key]
    }
    inherited.update(
        {
            "CI": "1",
            "DISABLE_TELEMETRY": "1",
            "DO_NOT_TRACK": "1",
            "NO_UPDATE_NOTIFIER": "1",
            "NODE_DISABLE_COMPILE_CACHE": "1",
            "npm_config_cache": str(qualification_root / "npm-cache"),
            "npm_config_userconfig": str(qualification_root / "npmrc"),
            "npm_config_globalconfig": str(qualification_root / "global-npmrc"),
            "npm_config_audit": "false",
            "npm_config_fund": "false",
            "npm_config_update_notifier": "false",
            "XDG_CACHE_HOME": str(qualification_root / "xdg-cache"),
            "XDG_CONFIG_HOME": str(qualification_root / "xdg-config"),
            "XDG_DATA_HOME": str(qualification_root / "xdg-data"),
        }
    )
    policy = {
        "strategy": "allowlist",
        "source_environment_copied": False,
        "inherited_keys": sorted(key for key in INHERITED_ENV_ALLOWLIST if key in source_env and source_env[key]),
        "cloud_token_or_password_named_variables_inherited": False,
        "proxy_variables_inherited": False,
        "user_npm_config_disabled": True,
        "home_redirected": False,
    }
    return inherited, policy


def reviewed_dependency_lock() -> dict[str, Any]:
    package_json = CLI_RUNTIME_SOURCE / "package.json"
    package_lock = CLI_RUNTIME_SOURCE / "package-lock.json"
    observed_package_hash = sha256_file(package_json) if package_json.is_file() else None
    observed_lock_hash = sha256_file(package_lock) if package_lock.is_file() else None
    lock: dict[str, Any] = {}
    parse_error: str | None = None
    try:
        lock = json.loads(package_lock.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        parse_error = str(exc)

    packages = lock.get("packages", {}) if isinstance(lock, dict) else {}
    root_package = packages.get("", {}) if isinstance(packages, dict) else {}
    skills_package = packages.get("node_modules/skills", {}) if isinstance(packages, dict) else {}
    dependency_integrities_complete = bool(packages) and all(
        relative == ""
        or (
            isinstance(metadata, dict)
            and isinstance(metadata.get("version"), str)
            and isinstance(metadata.get("integrity"), str)
        )
        for relative, metadata in packages.items()
    )
    semantic_match = (
        parse_error is None
        and lock.get("lockfileVersion") == 3
        and root_package.get("dependencies", {}).get("skills") == SKILLS_CLI_VERSION
        and skills_package.get("version") == SKILLS_CLI_VERSION
        and skills_package.get("integrity") == EXPECTED_SKILLS_DIST_INTEGRITY
        and dependency_integrities_complete
    )
    hashes_match = (
        observed_package_hash == EXPECTED_RUNTIME_PACKAGE_JSON_SHA256
        and observed_lock_hash == EXPECTED_RUNTIME_LOCK_SHA256
    )
    return {
        "expected_package_json_sha256": EXPECTED_RUNTIME_PACKAGE_JSON_SHA256,
        "observed_package_json_sha256": observed_package_hash,
        "expected_lock_sha256": EXPECTED_RUNTIME_LOCK_SHA256,
        "observed_lock_sha256": observed_lock_hash,
        "expected_skills_dist_integrity": EXPECTED_SKILLS_DIST_INTEGRITY,
        "observed_skills_dist_integrity": skills_package.get("integrity"),
        "dependency_integrities_complete": dependency_integrities_complete,
        "semantic_match": semantic_match,
        "hashes_match": hashes_match,
        "verified": semantic_match and hashes_match,
        "parse_error": parse_error,
    }


def npm_package_integrity(package_root: Path) -> dict[str, Any]:
    observed: dict[str, str | None] = {}
    for relative in EXPECTED_NPM_FILE_HASHES:
        path = package_root / relative
        observed[relative] = sha256_file(path) if path.is_file() else None

    manifest: dict[str, Any] = {}
    manifest_error: str | None = None
    try:
        manifest = json.loads((package_root / "package.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        manifest_error = str(exc)

    manifest_valid = (
        manifest_error is None
        and manifest.get("name") == "skills"
        and manifest.get("version") == SKILLS_CLI_VERSION
        and manifest.get("bin", {}).get("skills") == "./bin/cli.mjs"
    )
    hashes_match = observed == EXPECTED_NPM_FILE_HASHES
    return {
        "expected_file_sha256": dict(EXPECTED_NPM_FILE_HASHES),
        "observed_file_sha256": observed,
        "manifest_valid": manifest_valid,
        "manifest_error": manifest_error,
        "hashes_match": hashes_match,
        "verified_before_execution": manifest_valid and hashes_match,
    }


def seed_offline_npm_cache(source: Path, target: Path) -> dict[str, Any]:
    """Copy a reviewed npm cache into an isolated qualification directory."""

    candidate = source.expanduser()
    if candidate.is_symlink() or not candidate.is_dir():
        raise ValueError("offline npm cache must be an existing non-symlink directory")
    resolved = candidate.resolve()
    source_sha256 = tree_fingerprint(resolved)
    if target.exists() or target.is_symlink():
        raise ValueError("isolated npm cache target already exists")
    shutil.copytree(resolved, target)
    copied_sha256 = tree_fingerprint(target)
    if copied_sha256 != source_sha256:
        raise ValueError("offline npm cache copy fingerprint mismatch")
    return {
        "provided": True,
        "copied_before_npm_execution": True,
        "source_tree_sha256": source_sha256,
        "copied_tree_sha256": copied_sha256,
        "source_path_recorded": False,
    }


def acquire_cli(
    args: argparse.Namespace,
    qualification_root: Path,
    env: dict[str, str],
    replacements: Sequence[tuple[Path, str]],
) -> tuple[list[str] | None, dict[str, Any], dict[str, Any]]:
    npm = args.npm or shutil.which("npm")
    node = args.node or shutil.which("node")
    offline_cache = getattr(args, "offline_npm_cache", None)
    metadata: dict[str, Any] = {
        "package": "skills",
        "expected_version": SKILLS_CLI_VERSION,
        "source": (
            "npm-pinned-reviewed-files-offline-cache"
            if offline_cache is not None
            else "npm-pinned-reviewed-files"
        ),
    }
    if not (args.allow_download or offline_cache is not None) or not npm or not node:
        metadata["blocked_reason"] = (
            "use --allow-download or --offline-npm-cache with npm and node available"
        )
        return None, metadata, {}

    lock_integrity = reviewed_dependency_lock()
    metadata["dependency_lock"] = lock_integrity
    if not lock_integrity["verified"]:
        return None, metadata, {}

    if offline_cache is not None:
        try:
            metadata["offline_cache"] = seed_offline_npm_cache(
                Path(offline_cache), qualification_root / "npm-cache"
            )
        except (OSError, ValueError) as exc:
            metadata["blocked_reason"] = str(exc)
            return None, metadata, {}

    runtime_root = qualification_root / "cli-runtime"
    runtime_root.mkdir()
    shutil.copy2(CLI_RUNTIME_SOURCE / "package.json", runtime_root / "package.json")
    shutil.copy2(CLI_RUNTIME_SOURCE / "package-lock.json", runtime_root / "package-lock.json")
    npm_argv = [
        str(npm),
        "ci",
        "--ignore-scripts",
        "--no-audit",
        "--no-fund",
    ]
    if offline_cache is not None:
        npm_argv.append("--offline")
    acquisition = command_result(
        npm_argv,
        cwd=runtime_root,
        env=env,
        replacements=replacements,
    )
    package_root = runtime_root / "node_modules" / "skills"
    integrity = npm_package_integrity(package_root)
    runtime_lock_hash = sha256_file(runtime_root / "package-lock.json")
    lock_integrity["runtime_lock_sha256"] = runtime_lock_hash
    lock_integrity["runtime_lock_matches_reviewed"] = (
        runtime_lock_hash == EXPECTED_RUNTIME_LOCK_SHA256
    )
    metadata["integrity"] = integrity
    if (
        not command_passed(acquisition)
        or not integrity["verified_before_execution"]
        or not lock_integrity["runtime_lock_matches_reviewed"]
    ):
        return None, metadata, {"npm_ci_ignore_scripts": acquisition}
    return (
        [str(node), str(package_root / "bin" / "cli.mjs")],
        metadata,
        {"npm_ci_ignore_scripts": acquisition},
    )


def verify_install(
    project_root: Path,
    source_hash: str,
    expected_locations: Sequence[str] | None = None,
) -> dict[str, Any]:
    copies = installed_copies(project_root)
    copy_hashes: dict[str, str] = {}
    copy_errors: dict[str, str] = {}
    for path in copies:
        relative = path.relative_to(project_root).as_posix()
        try:
            copy_hashes[relative] = tree_fingerprint(path)
        except ValueError as exc:
            copy_errors[relative] = str(exc)
    observed_locations = sorted(
        path.relative_to(project_root).as_posix() for path in copies
    )
    exact_location_set = (
        set(observed_locations) == set(expected_locations)
        if expected_locations is not None
        else None
    )
    return {
        "locations": observed_locations,
        "expected_locations": sorted(expected_locations) if expected_locations is not None else None,
        "exact_location_set": exact_location_set,
        "tree_sha256": copy_hashes,
        "copy_errors": copy_errors,
        "source_tree_sha256": source_hash,
        "copy_count": len(copies),
        "regular_copy": bool(copies) and not copy_errors,
        "all_copies_match_source": bool(copy_hashes)
        and not copy_errors
        and all(value == source_hash for value in copy_hashes.values()),
    }


def lockfile_is_empty(path: Path) -> tuple[bool, Any]:
    if not path.exists():
        return True, None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return False, {"error": str(exc)}
    valid = (
        isinstance(value, dict)
        and set(value) <= {"version", "skills"}
        and value.get("version") == 1
        and value.get("skills") == {}
    )
    return valid, value


def audit_residuals(
    project_root: Path,
    allowed_directories: Sequence[str] = (),
) -> dict[str, Any]:
    files: list[str] = []
    directories: list[str] = []
    symlinks: list[str] = []
    empty_directories: list[str] = []
    for path in sorted(project_root.rglob("*")):
        relative = path.relative_to(project_root)
        if relative.parts and relative.parts[0] == ".git":
            continue
        label = relative.as_posix()
        if path.is_symlink():
            symlinks.append(label)
        elif path.is_file():
            files.append(label)
        elif path.is_dir():
            directories.append(label)
            if not any(path.iterdir()):
                empty_directories.append(label)

    allowed_files = {"skills-lock.json"}
    unexpected_files = sorted(set(files) - allowed_files)
    unexpected_directories = sorted(set(directories) - set(allowed_directories))
    lock_valid, lock_value = lockfile_is_empty(project_root / "skills-lock.json")
    remaining_copies = [
        path.relative_to(project_root).as_posix()
        for path in installed_copies(project_root)
    ]
    clean = (
        not unexpected_files
        and not unexpected_directories
        and not symlinks
        and lock_valid
        and not remaining_copies
    )
    return {
        "clean": clean,
        "remaining_skill_copies": remaining_copies,
        "unexpected_files": unexpected_files,
        "unexpected_directories": unexpected_directories,
        "symlinks": symlinks,
        "allowed_residual_files": sorted(set(files) & allowed_files),
        "allowed_residual_directories": sorted(set(directories) & set(allowed_directories)),
        "empty_directories": empty_directories,
        "skills_lock_empty_or_absent": lock_valid,
        "skills_lock": lock_value,
    }


def list_contains_skill(step: Mapping[str, Any]) -> bool:
    try:
        listed = parse_json_suffix(str(step.get("stdout_excerpt", "")))
    except ValueError:
        return False
    return isinstance(listed, list) and any(
        isinstance(item, dict) and item.get("name") == SKILL_NAME
        for item in listed
    )


def prepare_universal_agent_detection_fixture(
    qualification_root: Path,
) -> dict[str, Any]:
    """Create an isolated second consumer of the universal `.agents` target."""

    fixture = qualification_root / "xdg-config" / "opencode"
    if fixture.exists() or fixture.is_symlink():
        raise ValueError("universal agent detection fixture already exists")
    fixture.mkdir(parents=True)
    return {
        "agent": "opencode",
        "path": "$QUALIFICATION_ROOT/xdg-config/opencode",
        "kind": "empty-config-directory",
        "scope": "disposable-qualification-root",
        "purpose": "exercise shared universal .agents removal semantics",
        "model_session_started": False,
    }


def run_agent_case(
    agent: str,
    *,
    source_root: Path,
    qualification_root: Path,
    cli_prefix: Sequence[str],
    env: dict[str, str],
    replacements: Sequence[tuple[Path, str]],
    source_hash: str,
) -> dict[str, Any]:
    project_root = qualification_root / f"backend-{agent}"
    project_root.mkdir()
    git = shutil.which("git")
    if not git:
        return {"agent": agent, "passed": False, "blocked_reason": "git is required"}

    install_argv = [
        *cli_prefix,
        "add",
        str(source_root),
        "--skill",
        SKILL_NAME,
        "-a",
        agent,
        "--copy",
        "-y",
        "--json",
    ]
    remove_argv = [
        *cli_prefix,
        "remove",
        SKILL_NAME,
        "-y",
    ]
    list_argv = [*cli_prefix, "list", "-a", agent, "--json"]

    steps: dict[str, dict[str, Any]] = {}
    steps["git_init"] = command_result(
        [git, "init", "-q"], cwd=project_root, env=env, replacements=replacements
    )
    steps["install"] = command_result(
        install_argv, cwd=project_root, env=env, replacements=replacements
    )
    first_install = verify_install(
        project_root, source_hash, EXPECTED_INSTALL_LOCATIONS[agent]
    )
    steps["list"] = command_result(
        list_argv, cwd=project_root, env=env, replacements=replacements
    )
    first_list_pass = list_contains_skill(steps["list"])

    filtered_remove_probe: dict[str, Any]
    if agent in {"codex", "cursor"}:
        steps["agent_filtered_remove_probe"] = command_result(
            [*cli_prefix, "remove", SKILL_NAME, "-a", agent, "-y"],
            cwd=project_root,
            env=env,
            replacements=replacements,
        )
        remaining_after_probe = verify_install(
            project_root, source_hash, EXPECTED_INSTALL_LOCATIONS[agent]
        )
        lock_empty_after_probe, lock_after_probe = lockfile_is_empty(
            project_root / "skills-lock.json"
        )
        probe_confirmed = all(
            (
                command_passed(steps["agent_filtered_remove_probe"]),
                remaining_after_probe["all_copies_match_source"],
                remaining_after_probe["exact_location_set"],
                not lock_empty_after_probe,
                isinstance(lock_after_probe, dict),
                SKILL_NAME in lock_after_probe.get("skills", {}),
            )
        )
        filtered_remove_probe = {
            "required": True,
            "performed": True,
            "confirmed": probe_confirmed,
            "command_reported_success": command_passed(
                steps["agent_filtered_remove_probe"]
            ),
            "remaining_install": remaining_after_probe,
            "active_lock_entry_remained": not lock_empty_after_probe,
        }
    else:
        filtered_remove_probe = {
            "required": False,
            "performed": False,
            "confirmed": None,
            "reason": "Claude Code uses its dedicated .claude destination.",
        }

    steps["remove"] = command_result(
        remove_argv, cwd=project_root, env=env, replacements=replacements
    )
    first_residuals = audit_residuals(
        project_root, EXPECTED_RESIDUAL_DIRECTORIES[agent]
    )

    steps["reinstall"] = command_result(
        install_argv, cwd=project_root, env=env, replacements=replacements
    )
    second_install = verify_install(
        project_root, source_hash, EXPECTED_INSTALL_LOCATIONS[agent]
    )
    steps["relist"] = command_result(
        list_argv, cwd=project_root, env=env, replacements=replacements
    )
    second_list_pass = list_contains_skill(steps["relist"])
    steps["final_remove"] = command_result(
        remove_argv, cwd=project_root, env=env, replacements=replacements
    )
    final_residuals = audit_residuals(
        project_root, EXPECTED_RESIDUAL_DIRECTORIES[agent]
    )

    steps_pass = all(command_passed(step) for step in steps.values())
    passed = all(
        (
            steps_pass,
            first_install["all_copies_match_source"],
            first_install["exact_location_set"],
            second_install["all_copies_match_source"],
            second_install["exact_location_set"],
            first_list_pass,
            second_list_pass,
            filtered_remove_probe.get("confirmed") is True
            if filtered_remove_probe["required"]
            else True,
            first_residuals["clean"],
            final_residuals["clean"],
        )
    )
    return {
        "agent": agent,
        "passed": passed,
        "mode": "copy",
        "remove_agent_filter_omitted": True,
        "first_install": first_install,
        "first_list_contains_skill": first_list_pass,
        "agent_filtered_remove_probe": filtered_remove_probe,
        "first_remove_residuals": first_residuals,
        "second_install": second_install,
        "second_list_contains_skill": second_list_pass,
        "final_remove_residuals": final_residuals,
        "steps": steps,
    }


def emit_evidence(
    evidence: dict[str, Any],
    output: str | None,
    *,
    overwrite: bool = False,
    forbidden_root: Path | None = None,
) -> None:
    payload = json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    print(payload, end="")
    if not output or output == "-":
        return
    target = Path(output).expanduser().resolve()
    if forbidden_root is not None:
        try:
            target.relative_to(forbidden_root.resolve())
        except ValueError:
            pass
        else:
            raise ValueError("output must not be inside the disposable qualification root")
    if not target.parent.is_dir():
        raise FileNotFoundError(f"output directory does not exist: {target.parent}")
    if target.exists() and not overwrite:
        raise FileExistsError(f"output exists; pass --overwrite to replace it: {target}")
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--allow-download",
        action="store_true",
        help=(
            f"download skills@{SKILLS_CLI_VERSION} with npm --ignore-scripts, verify "
            "the reviewed package files, then execute it"
        ),
    )
    parser.add_argument("--node", help="Node.js executable for a JavaScript skills CLI")
    parser.add_argument("--npm", help="npm executable to use with --allow-download")
    parser.add_argument(
        "--offline-npm-cache",
        type=Path,
        help=(
            "seed the isolated npm cache from an existing non-symlink cache and run npm ci "
            "with --offline; package files and the dependency lock are still verified"
        ),
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=ROOT,
        help="Toolkit/plugin root to install; defaults to the current source checkout.",
    )
    parser.add_argument("--output", help="write the exact JSON receipt to this path; '-' means stdout only")
    parser.add_argument("--overwrite", action="store_true", help="replace an existing --output file")
    parser.add_argument("--keep", action="store_true", help="keep the disposable directory")
    args = parser.parse_args()

    if not args.allow_download and args.offline_npm_cache is None:
        parser.error(
            "--allow-download or --offline-npm-cache is required for the canonical locked qualification"
        )

    source_input = args.source.expanduser()
    if source_input.is_symlink() or not source_input.is_dir():
        parser.error("--source must be an existing non-symlink directory")
    source_root = source_input.resolve()
    skill_root = source_root / "skills" / SKILL_NAME
    if skill_root.is_symlink() or not (skill_root / "SKILL.md").is_file():
        parser.error("--source must contain a regular skills/oci-founder/SKILL.md")

    qualification_root = Path(tempfile.mkdtemp(prefix="oci-founder-skill-install-"))
    replacements = (
        (source_root, "$TOOLKIT_ROOT"),
        (qualification_root, "$QUALIFICATION_ROOT"),
    )
    env, environment_policy = sanitized_environment(qualification_root)
    source_before = tree_fingerprint(skill_root)
    global_before = global_snapshot()

    try:
        environment_policy["universal_agent_detection_fixture"] = (
            prepare_universal_agent_detection_fixture(qualification_root)
        )
        cli_prefix, cli_metadata, acquisition_steps = acquire_cli(
            args, qualification_root, env, replacements
        )
        if cli_prefix is None:
            evidence = {
                "kind": "oci-founder-skill-install-lifecycle",
                "schema_version": "2.0",
                "observed_at_utc": datetime.now(timezone.utc).isoformat(),
                "status": "blocked",
                "scope": "three-isolated-projects",
                "skills_cli": cli_metadata,
                "environment_policy": environment_policy,
                "steps": acquisition_steps,
                "release_qualified": False,
            }
            emit_evidence(
                evidence,
                args.output,
                overwrite=args.overwrite,
                forbidden_root=qualification_root,
            )
            return 2

        version_step = command_result(
            [*cli_prefix, "--version"],
            cwd=qualification_root,
            env=env,
            replacements=replacements,
        )
        try:
            observed_version = parse_exact_version(version_step["stdout_excerpt"])
        except ValueError:
            observed_version = None
        cli_metadata["observed_version"] = observed_version
        cli_metadata["version_parse_mode"] = "strict-semver-fullmatch"
        exact_version = observed_version == SKILLS_CLI_VERSION
        cli_metadata["version_exact_match"] = exact_version

        cases = [
            run_agent_case(
                agent,
                source_root=source_root,
                qualification_root=qualification_root,
                cli_prefix=cli_prefix,
                env=env,
                replacements=replacements,
                source_hash=source_before,
            )
            for agent in AGENTS
        ] if command_passed(version_step) and exact_version else []

        source_after = tree_fingerprint(skill_root)
        global_after = global_snapshot()
        observed_targets_unchanged = global_before == global_after
        observed_targets_contain_symlink = any(
            bool(entry.get("is_symlink"))
            for snapshot in (global_before, global_after)
            for entry in snapshot.values()
        )
        observed_targets_acceptable = global_snapshots_acceptable(
            global_before, global_after
        )
        source_unchanged = source_before == source_after
        passed = all(
            (
                command_passed(version_step),
                exact_version,
                len(cases) == len(AGENTS),
                all(case.get("passed") is True for case in cases),
                observed_targets_acceptable,
                source_unchanged,
            )
        )

        evidence = {
            "kind": "oci-founder-skill-install-lifecycle",
            "schema_version": "2.0",
            "observed_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "pass_with_reservations" if passed else "fail",
            "scope": "three-isolated-projects",
            "skills_cli": cli_metadata,
            "runner": {
                "script_sha256": sha256_file(Path(__file__)),
                "python_version": sys.version.split()[0],
                "output_mode": "direct-json",
            },
            "toolkit": {
                "source": "$TOOLKIT_ROOT",
                "skill_tree_sha256_before": source_before,
                "skill_tree_sha256_after": source_after,
                "skill_source_unchanged": source_unchanged,
            },
            "environment_policy": environment_policy,
            "policy": {
                "agents": list(AGENTS),
                "expected_install_locations": EXPECTED_INSTALL_LOCATIONS,
                "allowed_residual_directories": EXPECTED_RESIDUAL_DIRECTORIES,
                "allowed_residual_files": ["skills-lock.json"],
            },
            "cases": cases,
            "profile_safety": {
                "observed_global_skill_targets": sorted(global_before),
                "observed_global_skill_targets_unchanged": observed_targets_unchanged,
                "observed_global_skill_targets_contain_symlink": observed_targets_contain_symlink,
                "observed_global_skill_targets_acceptable": observed_targets_acceptable,
                "global_install_attempted": False,
                "user_home_redirected": False,
            },
            "effects": {
                "toolkit_skill_source_changed": not source_unchanged,
                "model_session_started": False,
                "oci_command_executed": False,
                "cloud_mutation_attempted": False,
            },
            "steps": {
                **acquisition_steps,
                "version": version_step,
            },
            "reservations": [
                "Only the four named global skill targets were snapshotted; no claim is made about the entire user profile.",
                "A symlink at any observed global skill target blocks qualification rather than following an arbitrary target.",
                "Global installation syntax was not executed against the user profile.",
                "Cursor can discover universal, Cursor, Claude, and Codex skill directories; duplicate-name runtime behavior remains a native Cursor gate.",
                "A disposable OpenCode config-directory fixture under the isolated XDG_CONFIG_HOME provides a second universal .agents consumer, so skills@1.7.0 agent-filtered removal must preserve the intact source-matched shared copy and active lock entry; no OpenCode session is started.",
                "The local-checkout update path is remove plus reinstall; skills update is not qualified for this source type.",
                "This test proves package lifecycle only, not host-native discovery or agent behavior.",
            ],
            "release_qualified": False,
        }
        emit_evidence(
            evidence,
            args.output,
            overwrite=args.overwrite,
            forbidden_root=qualification_root,
        )
        return 0 if passed else 1
    finally:
        if args.keep:
            print(f"Qualification directory retained: {qualification_root}", file=sys.stderr)
        else:
            shutil.rmtree(qualification_root)


if __name__ == "__main__":
    raise SystemExit(main())
