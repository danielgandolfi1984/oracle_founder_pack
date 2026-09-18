#!/usr/bin/env python3
"""Read-only host preflight for OCI Founder Toolkit.

This command inventories the local Codex, Cursor, and Claude surfaces, records
toolkit fingerprints, and can run validators that are already installed. It
does not install plugins, alter host configuration, contact OCI, or invoke an
agent/model session.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "1.0"
DEFAULT_TIMEOUT_SECONDS = 20
MAX_STDOUT_CHARS = 4_000
MAX_STDERR_CHARS = 2_000
SAFE_ENVIRONMENT_NAMES = (
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "PATH",
    "SYSTEMROOT",
    "TEMP",
    "TERM",
    "TMP",
    "TMPDIR",
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def tree_fingerprint(root: Path) -> str:
    """Hash relative paths, modes, and bytes for a regular-file tree."""

    digest = hashlib.sha256()
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        if path.is_symlink():
            raise ValueError(f"refusing to fingerprint symlink: {path}")
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update((path.stat().st_mode & 0o777).to_bytes(4, "big"))
        content = path.read_bytes()
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def redact_path(path: Path | str, toolkit_root: Path = ROOT) -> str:
    resolved = Path(path).expanduser().resolve(strict=False)
    roots = (
        (toolkit_root.resolve(strict=False), "$TOOLKIT_ROOT"),
        (Path.home().resolve(strict=False), "$HOME"),
    )
    for prefix, label in roots:
        try:
            relative = resolved.relative_to(prefix)
        except ValueError:
            continue
        return label if not relative.parts else f"{label}/{relative.as_posix()}"
    return str(resolved)


def redact_text(value: str, toolkit_root: Path = ROOT) -> str:
    replacements = (
        (str(toolkit_root.resolve(strict=False)), "$TOOLKIT_ROOT"),
        (str(Path.home().resolve(strict=False)), "$HOME"),
    )
    redacted = value
    for raw, replacement in sorted(replacements, key=lambda item: len(item[0]), reverse=True):
        redacted = redacted.replace(raw, replacement)
    return redacted


def sanitized_environment() -> dict[str, str]:
    """Return the non-secret environment allowlist used by every child process."""

    environment = {
        name: os.environ[name]
        for name in SAFE_ENVIRONMENT_NAMES
        if name in os.environ and os.environ[name]
    }
    environment.setdefault("PATH", os.defpath)
    environment["NO_COLOR"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


def command_result(
    argv: Sequence[str],
    *,
    toolkit_root: Path = ROOT,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    validator_pythonpath: Path | None = None,
) -> dict[str, Any]:
    """Run a bounded, non-interactive probe and return redacted evidence."""

    safe_argv = [redact_text(str(argument), toolkit_root) for argument in argv]
    started = datetime.now(timezone.utc)
    try:
        environment = sanitized_environment()
        if validator_pythonpath is not None:
            environment["PYTHONPATH"] = str(validator_pythonpath)
        completed = subprocess.run(
            [str(argument) for argument in argv],
            cwd=toolkit_root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_seconds,
            check=False,
            env=environment,
        )
        stdout = redact_text(completed.stdout, toolkit_root)
        stderr = redact_text(completed.stderr, toolkit_root)
        exit_code: int | None = completed.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        raw_stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        raw_stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        stdout = redact_text(raw_stdout, toolkit_root)
        stderr = redact_text(raw_stderr, toolkit_root)
        exit_code = None
        timed_out = True
    duration_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
    return {
        "argv": safe_argv,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "duration_ms": duration_ms,
        "stdout_sha256": sha256_bytes(stdout.encode("utf-8")),
        "stderr_sha256": sha256_bytes(stderr.encode("utf-8")),
        "stdout_excerpt": stdout[:MAX_STDOUT_CHARS],
        "stderr_excerpt": stderr[:MAX_STDERR_CHARS],
    }


def locate_executable(name: str, candidates: Sequence[Path]) -> Path | None:
    located = shutil.which(name)
    if located:
        return Path(located).resolve(strict=False)
    for candidate in candidates:
        expanded = candidate.expanduser()
        if expanded.is_file() and os.access(expanded, os.X_OK):
            return expanded.resolve(strict=False)
    return None


def bundle_info(path: Path) -> dict[str, Any]:
    info_path = path / "Contents/Info.plist"
    result: dict[str, Any] = {
        "installed": path.is_dir(),
        "path": redact_path(path),
        "version": None,
        "build": None,
        "bundle_id": None,
    }
    if not info_path.is_file():
        return result
    try:
        with info_path.open("rb") as handle:
            info = plistlib.load(handle)
    except (OSError, plistlib.InvalidFileException):
        result["metadata_status"] = "unreadable"
        return result
    result.update(
        {
            "version": info.get("CFBundleShortVersionString"),
            "build": info.get("CFBundleVersion"),
            "bundle_id": info.get("CFBundleIdentifier"),
            "metadata_status": "read",
        }
    )
    return result


def first_nonempty_line(result: dict[str, Any]) -> str | None:
    for stream in (result.get("stdout_excerpt", ""), result.get("stderr_excerpt", "")):
        for line in str(stream).splitlines():
            if line.strip() and not line.startswith("WARNING:"):
                return line.strip()
    return None


def probe_codex(
    run_validators: bool,
    *,
    validator_pythonpath: Path | None = None,
) -> dict[str, Any]:
    executable = locate_executable(
        "codex",
        (
            Path("/Applications/ChatGPT.app/Contents/Resources/codex"),
            Path("/Applications/Codex.app/Contents/Resources/codex"),
        ),
    )
    result: dict[str, Any] = {
        "surface": "codex-cli",
        "available": executable is not None,
        "executable": redact_path(executable) if executable else None,
        "app": bundle_info(Path("/Applications/ChatGPT.app")),
        "version": None,
        "plugin_cli": "not_probed",
        "native_manifest_validator": "not_probed",
        "development_validators": {},
    }
    if executable:
        version_probe = command_result((str(executable), "--version"))
        plugin_help = command_result((str(executable), "plugin", "--help"))
        help_text = str(plugin_help.get("stdout_excerpt", ""))
        result.update(
            {
                "version": first_nonempty_line(version_probe),
                "version_probe": version_probe,
                "plugin_cli": "available" if plugin_help.get("exit_code") == 0 else "probe_failed",
                "native_manifest_validator": (
                    "available"
                    if re.search(r"(?m)^\s{2}validate\b", help_text)
                    else "not_exposed_by_cli"
                ),
                "plugin_help_probe": plugin_help,
            }
        )

    validator_specs = {
        "codex_plugin_creator": (
            Path.home() / ".codex/skills/.system/plugin-creator/scripts/validate_plugin.py",
            ROOT,
        ),
        "portable_skill": (
            Path.home() / ".codex/skills/.system/skill-creator/scripts/quick_validate.py",
            ROOT / "skills/oci-founder",
        ),
    }
    for name, (validator, target) in validator_specs.items():
        evidence: dict[str, Any] = {
            "available": validator.is_file(),
            "validator": redact_path(validator),
            "status": "not_run",
        }
        if run_validators and validator.is_file():
            probe = command_result(
                (sys.executable, str(validator), str(target)),
                validator_pythonpath=validator_pythonpath,
            )
            combined_output = f"{probe.get('stdout_excerpt', '')}\n{probe.get('stderr_excerpt', '')}"
            if probe.get("exit_code") == 0:
                evidence["status"] = "passed"
            elif "No module named 'yaml'" in combined_output:
                evidence["status"] = "blocked_missing_pyyaml"
            else:
                evidence["status"] = "failed"
            evidence["probe"] = probe
        result["development_validators"][name] = evidence
    return result


def probe_cursor() -> dict[str, Any]:
    editor_cli = locate_executable(
        "cursor",
        (Path("/Applications/Cursor.app/Contents/Resources/app/bin/cursor"),),
    )
    agent_cli = locate_executable(
        "cursor-agent",
        (Path.home() / ".local/bin/cursor-agent",),
    )
    result: dict[str, Any] = {
        "surface": "cursor",
        "app": bundle_info(Path("/Applications/Cursor.app")),
        "editor_cli_available": editor_cli is not None,
        "editor_cli": redact_path(editor_cli) if editor_cli else None,
        "agent_cli_available": agent_cli is not None,
        "agent_cli": redact_path(agent_cli) if agent_cli else None,
        "native_manifest_validator": "not_exposed_by_editor_cli",
        "safety_note": "The preflight never invokes `cursor agent`; this app wrapper may install cursor-agent.",
    }
    if editor_cli:
        version_probe = command_result((str(editor_cli), "--version"))
        result["editor_version"] = first_nonempty_line(version_probe)
        result["editor_version_probe"] = version_probe
    return result


def probe_claude(run_validators: bool) -> dict[str, Any]:
    executable = locate_executable(
        "claude",
        (
            Path.home() / ".local/bin/claude",
            Path("/opt/homebrew/bin/claude"),
            Path("/usr/local/bin/claude"),
        ),
    )
    result: dict[str, Any] = {
        "surface": "claude-code",
        "available": executable is not None,
        "executable": redact_path(executable) if executable else None,
        "desktop_app": bundle_info(Path("/Applications/Claude.app")),
        "version": None,
        "native_manifest_validator": "available" if executable else "blocked_cli_missing",
        "validation": {"status": "not_run"},
    }
    if executable:
        version_probe = command_result((str(executable), "--version"))
        result["version"] = first_nonempty_line(version_probe)
        result["version_probe"] = version_probe
        if run_validators:
            validation_probe = command_result(
                (str(executable), "plugin", "validate", str(ROOT), "--strict")
            )
            result["validation"] = {
                "status": "passed" if validation_probe.get("exit_code") == 0 else "failed",
                "probe": validation_probe,
            }
    return result


def toolkit_evidence() -> dict[str, Any]:
    manifests = (
        "plugin.json",
        ".codex-plugin/plugin.json",
        ".claude-plugin/plugin.json",
    )
    manifest_hashes = {relative: sha256_file(ROOT / relative) for relative in manifests}
    combined = hashlib.sha256()
    for relative, digest in sorted(manifest_hashes.items()):
        combined.update(relative.encode("utf-8"))
        combined.update(digest.encode("ascii"))
    skill_hash = tree_fingerprint(ROOT / "skills/oci-founder")
    combined.update(skill_hash.encode("ascii"))
    return {
        "root": "$TOOLKIT_ROOT",
        "manifest_sha256": manifest_hashes,
        "skill_tree_sha256": skill_hash,
        "container_api_blueprint_sha256": tree_fingerprint(ROOT / "blueprints/container-api"),
        "validation_tool_sha256": {
            "scripts/qualify_hosts.py": sha256_file(ROOT / "scripts/qualify_hosts.py"),
            "scripts/validate.py": sha256_file(ROOT / "scripts/validate.py"),
        },
        "source_fingerprint": combined.hexdigest(),
    }


def validator_dependency_evidence(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "status": "not_provided",
            "pyyaml_version": None,
            "tree_sha256": None,
        }
    candidate = path.expanduser()
    if candidate.is_symlink() or not candidate.is_dir():
        return {
            "status": "invalid",
            "path": redact_path(candidate),
            "reason": "path_missing_not_directory_or_symlink",
        }
    resolved = candidate.resolve()
    metadata_files = sorted(resolved.glob("PyYAML-*.dist-info/METADATA"))
    yaml_entrypoint = resolved / "yaml/__init__.py"
    if len(metadata_files) != 1 or not yaml_entrypoint.is_file():
        return {
            "status": "invalid",
            "path": redact_path(resolved),
            "reason": "expected_exactly_one_pyyaml_distribution",
        }
    metadata = metadata_files[0].read_text(encoding="utf-8")
    version_match = re.search(r"(?m)^Version:\s*([^\s]+)\s*$", metadata)
    version = version_match.group(1) if version_match else None
    if version != "6.0.2":
        return {
            "status": "invalid",
            "path": redact_path(resolved),
            "reason": "unexpected_pyyaml_version",
            "pyyaml_version": version,
        }
    try:
        fingerprint = tree_fingerprint(resolved)
    except ValueError as exc:
        return {
            "status": "invalid",
            "path": redact_path(resolved),
            "reason": redact_text(str(exc)),
            "pyyaml_version": version,
        }
    return {
        "status": "passed",
        "path": redact_path(resolved),
        "pyyaml_version": version,
        "tree_sha256": fingerprint,
        "requirements_sha256": sha256_file(ROOT / "requirements-validation.txt"),
    }


def repo_validation(skip: bool) -> dict[str, Any]:
    if skip:
        return {"status": "not_run"}
    probe = command_result(
        (
            sys.executable,
            str(ROOT / "scripts/validate.py"),
            "--skip-host-preflight-evidence",
        )
    )
    return {
        "status": "passed" if probe.get("exit_code") == 0 else "failed",
        "mode": "source-without-host-preflight-evidence",
        "probe": probe,
    }


def build_report(
    hosts: Sequence[str],
    *,
    run_validators: bool,
    skip_repo_validation: bool,
    validator_pythonpath: Path | None = None,
) -> dict[str, Any]:
    dependency_evidence = validator_dependency_evidence(validator_pythonpath)
    validated_pythonpath = (
        validator_pythonpath.expanduser().resolve()
        if validator_pythonpath is not None and dependency_evidence.get("status") == "passed"
        else None
    )
    probes: dict[str, Any] = {}
    if "codex" in hosts:
        probes["codex"] = probe_codex(
            run_validators,
            validator_pythonpath=validated_pythonpath,
        )
    if "cursor" in hosts:
        probes["cursor"] = probe_cursor()
    if "claude" in hosts:
        probes["claude"] = probe_claude(run_validators)

    blockers: list[str] = []
    if probes.get("codex", {}).get("native_manifest_validator") == "not_exposed_by_cli":
        blockers.append("Codex CLI exposes plugin management but no native manifest validator.")
    for name, validator in probes.get("codex", {}).get("development_validators", {}).items():
        if run_validators and validator.get("status") != "passed":
            blockers.append(
                f"Codex development validator {name} did not pass: {validator.get('status')}."
            )
    if run_validators and validator_pythonpath is not None and dependency_evidence.get("status") != "passed":
        blockers.append(
            "The explicit development-validator dependency directory did not pass validation."
        )
    if "cursor" in probes:
        if not probes["cursor"].get("agent_cli_available"):
            blockers.append("Cursor Agent CLI is missing; native behavioral replay is blocked.")
        blockers.append("Cursor editor CLI exposes no native plugin validator in this environment.")
    if "claude" in probes and not probes["claude"].get("available"):
        blockers.append("Claude Desktop is not Claude Code; the Claude Code CLI is missing.")

    return {
        "schema_version": SCHEMA_VERSION,
        "kind": "oci-founder-host-preflight",
        "scope": "read_only",
        "run_validators_requested": run_validators,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "toolkit": toolkit_evidence(),
        "environment": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "python_executable": redact_path(sys.executable),
            "subprocess_policy": {
                "strategy": "allowlist",
                "inherited_names": sorted(
                    name for name in SAFE_ENVIRONMENT_NAMES if name in os.environ
                ),
                "cloud_token_or_password_named_variables_inherited": False,
                "raw_environment_recorded": False,
            },
        },
        "development_validator_runtime": dependency_evidence,
        "repo_validation": repo_validation(skip_repo_validation),
        "hosts": probes,
        "summary": {
            "release_qualified": False,
            "blockers": blockers,
            "installation_attempted": False,
            "host_configuration_changed": False,
            "model_session_started": False,
            "oci_command_executed": False,
            "cloud_mutation_attempted": False,
        },
    }


def presence_failures(report: dict[str, Any], required: Sequence[str]) -> list[str]:
    failures: list[str] = []
    for host in required:
        evidence = report["hosts"].get(host, {})
        if host == "codex" and not evidence.get("available"):
            failures.append("codex CLI is missing")
        elif host == "cursor" and not evidence.get("app", {}).get("installed"):
            failures.append("Cursor app is missing")
        elif host == "claude" and not evidence.get("available"):
            failures.append("Claude Code CLI is missing")
    return failures


def render_text(report: dict[str, Any]) -> str:
    rows = [
        "OCI Founder Toolkit host preflight (read-only)",
        f"Toolkit fingerprint: {report['toolkit']['source_fingerprint']}",
        f"Repository validation: {report['repo_validation']['status']}",
    ]
    hosts = report["hosts"]
    if "codex" in hosts:
        item = hosts["codex"]
        rows.append(
            f"Codex: {'available' if item['available'] else 'missing'}"
            f"; version={item.get('version') or 'unknown'}"
            f"; native-validator={item['native_manifest_validator']}"
        )
    if "cursor" in hosts:
        item = hosts["cursor"]
        rows.append(
            f"Cursor: app={'available' if item['app']['installed'] else 'missing'}"
            f"; editor={item.get('editor_version') or 'unknown'}"
            f"; agent-cli={'available' if item['agent_cli_available'] else 'missing'}"
        )
    if "claude" in hosts:
        item = hosts["claude"]
        rows.append(
            f"Claude: desktop={'available' if item['desktop_app']['installed'] else 'missing'}"
            f"; code-cli={'available' if item['available'] else 'missing'}"
            f"; version={item.get('version') or 'unknown'}"
        )
    rows.append("Release qualified: no")
    rows.append("No installation, model session, OCI command, or cloud mutation was attempted.")
    return "\n".join(rows)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inventory Codex, Cursor, and Claude host readiness without installing anything."
    )
    parser.add_argument(
        "--host",
        action="append",
        choices=("codex", "cursor", "claude"),
        help="Host to inspect. Repeat to select multiple; default: all.",
    )
    parser.add_argument(
        "--run-validators",
        action="store_true",
        help="Run already-installed development/native validators; never installs a validator.",
    )
    parser.add_argument(
        "--validator-pythonpath",
        type=Path,
        help=(
            "Explicit PyYAML 6.0.2 target directory for installed development validators. "
            "It is passed only to validator subprocesses and must match requirements-validation.txt."
        ),
    )
    parser.add_argument(
        "--skip-repo-validation",
        action="store_true",
        help="Skip scripts/validate.py (useful only for focused diagnostics).",
    )
    parser.add_argument(
        "--require",
        action="append",
        choices=("codex", "cursor", "claude"),
        default=[],
        help="Exit 2 if the selected primary host surface is absent. Repeat as needed.",
    )
    parser.add_argument(
        "--fail-on-blocked",
        action="store_true",
        help="Exit 2 when any selected qualification gate is blocked.",
    )
    parser.add_argument("--json", action="store_true", help="Print the full JSON report.")
    parser.add_argument("--output", type=Path, help="Write the full JSON report to this path.")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing --output file; the default is to fail closed.",
    )
    return parser.parse_args(argv)


def write_report(path: Path, report: dict[str, Any], *, overwrite: bool = False) -> None:
    candidate = path.expanduser()
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    if candidate.parent.is_symlink():
        raise ValueError(f"refusing output through a symlink parent: {candidate.parent}")
    if not candidate.parent.is_dir():
        raise ValueError(f"output parent does not exist: {candidate.parent}")
    target = candidate.parent.resolve() / candidate.name
    if target.is_symlink():
        raise ValueError(f"refusing to replace symlink: {target}")
    if target.exists() and not overwrite:
        raise FileExistsError(f"output exists; pass --overwrite to replace it: {target}")
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
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


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    hosts = tuple(dict.fromkeys(args.host or ("codex", "cursor", "claude")))
    report = build_report(
        hosts,
        run_validators=args.run_validators,
        skip_repo_validation=args.skip_repo_validation,
        validator_pythonpath=args.validator_pythonpath,
    )
    if args.output:
        write_report(args.output, report, overwrite=args.overwrite)
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else render_text(report))
    failures = presence_failures(report, args.require)
    if failures:
        for failure in failures:
            print(f"required host unavailable: {failure}", file=sys.stderr)
        return 2
    if args.fail_on_blocked and report["summary"]["blockers"]:
        return 2
    if report["repo_validation"]["status"] == "failed":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
