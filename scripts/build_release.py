#!/usr/bin/env python3
"""Build and verify deterministic Founder Toolkit for OCI preview archives."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import re
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Sequence


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_SCHEMA_VERSION = "1.1"
PACKAGE_NAME = "oci-founder-toolkit"
PACKAGE_STATUS = "public-preview"
PACKAGE_LICENSE = "UPL-1.0"
PRIVATE_KEY_MARKERS = (
    b"-----BEGIN " + b"PRIVATE KEY-----",
    b"-----BEGIN RSA PRIVATE KEY-----",
    b"-----BEGIN EC PRIVATE KEY-----",
    b"-----BEGIN " + b"OPENSSH PRIVATE KEY-----",
)
PACKAGE_PUBLISHER = {
    "name": "Daniel Gandolfi",
    "url": "https://github.com/danielgandolfi1984",
}
FORBIDDEN_PARTS = {
    ".git",
    ".oci-founder",
    ".pptx-build",
    ".terraform",
    "__pycache__",
    "artifacts",
    "dist",
    "node_modules",
}
FORBIDDEN_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".tfplan",
    ".tfstate",
}
FORBIDDEN_GENERATED_PREFIXES = (
    "deployment-receipt",
    "teardown-receipt",
    "plan-summary",
    "smoke-result",
    "state-addresses",
    "build-metadata",
)
SKILL_PACKAGE_PATHS = (
    "skills/oci-founder/LICENSE",
    "skills/oci-founder/SKILL.md",
    "skills/oci-founder/agents/openai.yaml",
    "skills/oci-founder/references/container-api-preview.md",
    "skills/oci-founder/references/discovery.md",
    "skills/oci-founder/references/golden-paths.md",
    "skills/oci-founder/references/guardrails.md",
    "skills/oci-founder/references/service-map.md",
    "skills/oci-founder/references/upstream-oracle-skills.md",
    "skills/oci-founder/references/use-cases.md",
)
BLUEPRINT_PACKAGE_PATHS = (
    "blueprints/container-api/README.md",
    "blueprints/container-api/VERSION",
    "blueprints/container-api/app/.dockerignore",
    "blueprints/container-api/app/Dockerfile",
    "blueprints/container-api/app/app.py",
    "blueprints/container-api/terraform/bootstrap/.terraform.lock.hcl",
    "blueprints/container-api/terraform/bootstrap/README.md",
    "blueprints/container-api/terraform/bootstrap/main.tf",
    "blueprints/container-api/terraform/bootstrap/outputs.tf",
    "blueprints/container-api/terraform/bootstrap/terraform.tfvars.example.json",
    "blueprints/container-api/terraform/bootstrap/variables.tf",
    "blueprints/container-api/terraform/bootstrap/versions.tf",
    "blueprints/container-api/terraform/runtime/.terraform.lock.hcl",
    "blueprints/container-api/terraform/runtime/README.md",
    "blueprints/container-api/terraform/runtime/checks.tf",
    "blueprints/container-api/terraform/runtime/container.tf",
    "blueprints/container-api/terraform/runtime/data.tf",
    "blueprints/container-api/terraform/runtime/gateway.tf",
    "blueprints/container-api/terraform/runtime/locals.tf",
    "blueprints/container-api/terraform/runtime/network.tf",
    "blueprints/container-api/terraform/runtime/observability.tf",
    "blueprints/container-api/terraform/runtime/outputs.tf",
    "blueprints/container-api/terraform/runtime/terraform.tfvars.example.json",
    "blueprints/container-api/terraform/runtime/variables.tf",
    "blueprints/container-api/terraform/runtime/versions.tf",
    "blueprints/container-api/tools/founderctl.py",
)


@dataclass(frozen=True)
class PackageSpec:
    kind: str
    archive_file: str
    archive_root: str
    readme_source: Path
    exact_sources: tuple[Path, ...]
    tree_sources: tuple[tuple[Path, tuple[str, ...]], ...]


@dataclass(frozen=True)
class ContentEntry:
    archive_path: str
    source_path: str
    payload: bytes
    mode: int

    def manifest_value(self) -> dict[str, Any]:
        return {
            "path": self.archive_path,
            "source": self.source_path,
            "sha256": hashlib.sha256(self.payload).hexdigest(),
            "size": len(self.payload),
            "mode": f"{self.mode:04o}",
        }


def load_version() -> str:
    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    version = manifest.get("version")
    if not isinstance(version, str) or re.fullmatch(r"\d+\.\d+\.\d+", version) is None:
        raise ValueError("plugin.json must contain the reviewed strict-semver package version")
    return version


def load_blueprint_version() -> str:
    version = (ROOT / "blueprints/container-api/VERSION").read_text(encoding="utf-8").strip()
    if re.fullmatch(r"\d+\.\d+\.\d+-preview\.\d+", version) is None:
        raise ValueError("Container API must have a safe, explicit preview version")
    return version


def package_specs(version: str) -> tuple[PackageSpec, ...]:
    common = (
        ROOT / "LICENSE",
        ROOT / "THIRD_PARTY_NOTICES.md",
        ROOT / "SECURITY.md",
        ROOT / "SUPPORT.md",
        ROOT / "CONTRIBUTING.md",
        ROOT / "GOVERNANCE.md",
    )
    return (
        PackageSpec(
            kind="skill-only",
            archive_file=f"oci-founder-skill-{version}-preview.tar.gz",
            archive_root=f"oci-founder-skill-{version}-preview",
            readme_source=ROOT / "packaging/README.skill.md",
            exact_sources=(*common, *(ROOT / path for path in SKILL_PACKAGE_PATHS)),
            tree_sources=(),
        ),
        PackageSpec(
            kind="full-toolkit",
            archive_file=f"oci-founder-toolkit-{version}-container-api-{load_blueprint_version()}.tar.gz",
            archive_root=PACKAGE_NAME,
            readme_source=ROOT / "packaging/README.full.md",
            exact_sources=(
                *common,
                ROOT / "plugin.json",
                ROOT / ".codex-plugin/plugin.json",
                ROOT / ".claude-plugin/plugin.json",
                ROOT / "upstream/oracle-skills.lock.json",
                ROOT / "scripts/verify_oracle_skills_lock.py",
                *(ROOT / path for path in SKILL_PACKAGE_PATHS),
                *(ROOT / path for path in BLUEPRINT_PACKAGE_PATHS),
            ),
            tree_sources=(),
        ),
    )


def relative_source(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def is_forbidden_source(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if FORBIDDEN_PARTS.intersection(relative.parts):
        return True
    name = path.name
    if name == ".DS_Store" or name.startswith("~$"):
        return True
    if name == ".env" or (name.startswith(".env.") and name != ".env.example"):
        return True
    if name == "crash.log" or name == "founder-plan.local.md":
        return True
    if name.startswith("terraform-plan") and name.endswith(".json"):
        return True
    if name.endswith(".tfstate") or ".tfstate." in name:
        return True
    if (
        name.endswith(".tfvars")
        or name.endswith(".auto.tfvars")
        or name.endswith(".tfvars.json")
    ) and ".example" not in name:
        return True
    if any(name.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES):
        return True
    return any(name.startswith(prefix) for prefix in FORBIDDEN_GENERATED_PREFIXES)


def validated_payload(path: Path) -> bytes:
    if path.is_symlink():
        raise ValueError(f"refusing package symlink: {relative_source(path)}")
    if not path.is_file():
        raise ValueError(f"package source is not a regular file: {relative_source(path)}")
    if is_forbidden_source(path):
        raise ValueError(f"forbidden package source: {relative_source(path)}")
    payload = path.read_bytes()
    for marker in PRIVATE_KEY_MARKERS:
        if marker in payload:
            raise ValueError(f"private-key material found in package source: {relative_source(path)}")
    return payload


def source_mode(path: Path) -> int:
    return 0o755 if path.stat().st_mode & 0o111 else 0o644


def add_source_entry(
    entries: list[ContentEntry],
    *,
    spec: PackageSpec,
    path: Path,
    destination: str,
) -> None:
    pure_destination = PurePosixPath(destination)
    if pure_destination.is_absolute() or ".." in pure_destination.parts:
        raise ValueError(f"unsafe package destination: {destination}")
    entries.append(
        ContentEntry(
            archive_path=f"{spec.archive_root}/{pure_destination.as_posix()}",
            source_path=relative_source(path),
            payload=validated_payload(path),
            mode=source_mode(path),
        )
    )


def collect_entries(spec: PackageSpec) -> list[ContentEntry]:
    entries: list[ContentEntry] = []
    add_source_entry(entries, spec=spec, path=spec.readme_source, destination="README.md")
    for path in spec.exact_sources:
        add_source_entry(entries, spec=spec, path=path, destination=relative_source(path))
    for tree_root, excluded_first_parts in spec.tree_sources:
        if tree_root.is_symlink() or not tree_root.is_dir():
            raise ValueError(f"invalid package tree: {relative_source(tree_root)}")
        for path in sorted(tree_root.rglob("*")):
            relative_to_tree = path.relative_to(tree_root)
            if relative_to_tree.parts and relative_to_tree.parts[0] in excluded_first_parts:
                continue
            if path.is_symlink():
                raise ValueError(f"refusing package symlink: {relative_source(path)}")
            if not path.is_file():
                continue
            if is_forbidden_source(path):
                raise ValueError(f"forbidden file discovered in package tree: {relative_source(path)}")
            add_source_entry(
                entries,
                spec=spec,
                path=path,
                destination=relative_source(path),
            )
    paths = [entry.archive_path for entry in entries]
    if len(paths) != len(set(paths)):
        raise ValueError(f"duplicate archive path in {spec.kind} package")
    return sorted(entries, key=lambda entry: entry.archive_path)


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def content_fingerprint(files: Sequence[dict[str, Any]]) -> str:
    return hashlib.sha256(
        json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def tar_bytes(entries: Sequence[ContentEntry]) -> bytes:
    target = io.BytesIO()
    with gzip.GzipFile(fileobj=target, mode="wb", filename="", mtime=0, compresslevel=9) as compressed:
        with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
            for entry in entries:
                info = tarfile.TarInfo(entry.archive_path)
                info.size = len(entry.payload)
                info.mode = entry.mode
                info.mtime = 0
                info.uid = 0
                info.gid = 0
                info.uname = ""
                info.gname = ""
                info.pax_headers = {}
                archive.addfile(info, io.BytesIO(entry.payload))
    return target.getvalue()


def atomic_write(path: Path, payload: bytes, *, overwrite: bool) -> None:
    if path.is_symlink():
        raise ValueError(f"refusing to replace symlink: {path}")
    if path.exists() and not overwrite:
        raise FileExistsError(f"output exists; pass --overwrite to replace it: {path}")
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            os.fchmod(handle.fileno(), 0o644)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def prepare_output_dir(output_dir: Path) -> Path:
    candidate = output_dir.expanduser()
    if candidate.exists() and candidate.is_symlink():
        raise ValueError(f"output directory must not be a symlink: {candidate}")
    if not candidate.exists():
        if not candidate.parent.is_dir() or candidate.parent.is_symlink():
            raise ValueError(f"output parent must be an existing regular directory: {candidate.parent}")
        candidate.mkdir()
    if not candidate.is_dir():
        raise ValueError(f"output path is not a directory: {candidate}")
    return candidate.resolve()


def expected_output_names(spec: PackageSpec) -> tuple[str, str, str]:
    archive = spec.archive_file
    return archive, f"{archive}.manifest.json", f"{archive}.sha256"


def build_package(spec: PackageSpec, output_dir: Path, *, overwrite: bool) -> dict[str, Any]:
    entries = collect_entries(spec)
    file_values = [entry.manifest_value() for entry in entries]
    archive_payload = tar_bytes(entries)
    archive_sha256 = hashlib.sha256(archive_payload).hexdigest()
    archive_name, manifest_name, checksum_name = expected_output_names(spec)
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "kind": "oci-founder-package",
        "package_kind": spec.kind,
        "name": PACKAGE_NAME,
        "version": load_version(),
        "status": PACKAGE_STATUS,
        "license": PACKAGE_LICENSE,
        "publisher": PACKAGE_PUBLISHER,
        "archive_root": spec.archive_root,
        "archive": {
            "file": archive_name,
            "sha256": archive_sha256,
            "size": len(archive_payload),
            "format": "tar+gzip",
            "normalized_mtime": 0,
            "normalized_owner": "0:0",
        },
        "content_sha256": content_fingerprint(file_values),
        "files": file_values,
    }
    outputs = {
        output_dir / archive_name: archive_payload,
        output_dir / manifest_name: canonical_json(manifest),
        output_dir / checksum_name: f"{archive_sha256}  {archive_name}\n".encode("ascii"),
    }
    for path in outputs:
        if path.is_symlink():
            raise ValueError(f"refusing to replace symlink: {path}")
        if path.exists() and not overwrite:
            raise FileExistsError(f"output exists; pass --overwrite to replace it: {path}")
    for path, payload in outputs.items():
        atomic_write(path, payload, overwrite=overwrite)
    return manifest


def build_all(output_dir: Path, *, overwrite: bool = False) -> list[dict[str, Any]]:
    prepared = prepare_output_dir(output_dir)
    specs = package_specs(load_version())
    for spec in specs:
        for name in expected_output_names(spec):
            path = prepared / name
            if path.is_symlink():
                raise ValueError(f"refusing to replace symlink: {path}")
            if path.exists() and not overwrite:
                raise FileExistsError(f"output exists; pass --overwrite to replace it: {path}")
    return [build_package(spec, prepared, overwrite=overwrite) for spec in specs]


def safe_member_name(name: str) -> bool:
    path = PurePosixPath(name)
    return bool(path.parts) and not path.is_absolute() and ".." not in path.parts


def verify_package(spec: PackageSpec, output_dir: Path) -> dict[str, Any]:
    archive_name, manifest_name, checksum_name = expected_output_names(spec)
    archive_path = output_dir / archive_name
    manifest_path = output_dir / manifest_name
    checksum_path = output_dir / checksum_name
    for path in (archive_path, manifest_path, checksum_path):
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"missing or unsafe package artifact: {path}")
    archive_payload = archive_path.read_bytes()
    observed_archive_hash = hashlib.sha256(archive_payload).hexdigest()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError(f"manifest root must be an object: {manifest_path}")
    expected_manifest_keys = {
        "schema_version",
        "kind",
        "package_kind",
        "name",
        "version",
        "status",
        "license",
        "publisher",
        "archive_root",
        "archive",
        "content_sha256",
        "files",
    }
    if set(manifest) != expected_manifest_keys:
        raise ValueError(f"unexpected package manifest fields: {manifest_path}")
    expected_identity = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "kind": "oci-founder-package",
        "package_kind": spec.kind,
        "name": PACKAGE_NAME,
        "version": load_version(),
        "status": PACKAGE_STATUS,
        "license": PACKAGE_LICENSE,
        "publisher": PACKAGE_PUBLISHER,
        "archive_root": spec.archive_root,
    }
    if any(manifest.get(key) != value for key, value in expected_identity.items()):
        raise ValueError(f"package identity mismatch: {manifest_path}")
    archive_meta = manifest.get("archive", {})
    if not isinstance(archive_meta, dict) or set(archive_meta) != {
        "file",
        "sha256",
        "size",
        "format",
        "normalized_mtime",
        "normalized_owner",
    }:
        raise ValueError(f"unexpected archive metadata fields: {manifest_path}")
    if archive_meta.get("file") != archive_name or archive_meta.get("sha256") != observed_archive_hash:
        raise ValueError(f"archive hash mismatch: {archive_path}")
    if archive_meta.get("size") != len(archive_payload):
        raise ValueError(f"archive size mismatch: {archive_path}")
    if (
        archive_meta.get("format") != "tar+gzip"
        or archive_meta.get("normalized_mtime") != 0
        or archive_meta.get("normalized_owner") != "0:0"
    ):
        raise ValueError(f"archive normalization policy mismatch: {manifest_path}")
    checksum = checksum_path.read_text(encoding="ascii")
    if checksum != f"{observed_archive_hash}  {archive_name}\n":
        raise ValueError(f"checksum file mismatch: {checksum_path}")

    expected_files = manifest.get("files")
    if not isinstance(expected_files, list) or not all(isinstance(item, dict) for item in expected_files):
        raise ValueError(f"invalid files list: {manifest_path}")
    source_files = [entry.manifest_value() for entry in collect_entries(spec)]
    if expected_files != source_files:
        raise ValueError(f"manifest files do not match the current source allowlist: {manifest_path}")
    if manifest.get("content_sha256") != content_fingerprint(expected_files):
        raise ValueError(f"content fingerprint mismatch: {manifest_path}")
    expected_by_path = {str(item.get("path")): item for item in expected_files}
    if len(expected_by_path) != len(expected_files):
        raise ValueError(f"duplicate manifest paths: {manifest_path}")

    with tarfile.open(fileobj=io.BytesIO(archive_payload), mode="r:gz") as archive:
        members = archive.getmembers()
        observed_names = [member.name for member in members]
        if len(observed_names) != len(set(observed_names)):
            raise ValueError(f"archive contains duplicate members: {archive_path}")
        root_prefix = f"{spec.archive_root}/"
        if any(not name.startswith(root_prefix) for name in observed_names):
            raise ValueError(f"archive member is outside the reviewed root: {archive_path}")
        if set(observed_names) != set(expected_by_path):
            missing = sorted(set(expected_by_path) - set(observed_names))
            extra = sorted(set(observed_names) - set(expected_by_path))
            raise ValueError(f"archive member mismatch; missing={missing}, extra={extra}")
        for member in members:
            if not safe_member_name(member.name) or not member.isfile():
                raise ValueError(f"archive contains unsafe member: {member.name}")
            if (
                member.mtime != 0
                or member.uid != 0
                or member.gid != 0
                or member.uname != ""
                or member.gname != ""
                or member.pax_headers not in ({}, {"path": member.name})
            ):
                raise ValueError(f"archive metadata is not normalized: {member.name}")
            handle = archive.extractfile(member)
            if handle is None:
                raise ValueError(f"cannot read archive member: {member.name}")
            payload = handle.read()
            expected = expected_by_path[member.name]
            if hashlib.sha256(payload).hexdigest() != expected.get("sha256"):
                raise ValueError(f"member hash mismatch: {member.name}")
            if len(payload) != expected.get("size") or f"{member.mode:04o}" != expected.get("mode"):
                raise ValueError(f"member metadata mismatch: {member.name}")
    return manifest


def verify_all(output_dir: Path) -> list[dict[str, Any]]:
    prepared = output_dir.expanduser()
    if prepared.is_symlink() or not prepared.is_dir():
        raise ValueError(f"package output directory is missing or unsafe: {prepared}")
    return [verify_package(spec, prepared, ) for spec in package_specs(load_version())]


def deterministic_check() -> list[dict[str, Any]]:
    with tempfile.TemporaryDirectory(prefix="oci-founder-release-a-") as first_raw, tempfile.TemporaryDirectory(
        prefix="oci-founder-release-b-"
    ) as second_raw:
        first = Path(first_raw)
        second = Path(second_raw)
        first_manifests = build_all(first)
        build_all(second)
        verify_all(first)
        verify_all(second)
        first_files = {path.name: path.read_bytes() for path in first.iterdir() if path.is_file()}
        second_files = {path.name: path.read_bytes() for path in second.iterdir() if path.is_file()}
        if first_files != second_files:
            raise ValueError("two clean package builds were not byte-for-byte identical")
        return first_manifests


def render_summary(action: str, manifests: Iterable[dict[str, Any]]) -> str:
    rows = [f"Founder Toolkit for OCI package {action} passed"]
    for manifest in manifests:
        rows.append(
            f"- {manifest['package_kind']}: {manifest['archive']['file']} "
            f"sha256={manifest['archive']['sha256']} files={len(manifest['files'])}"
        )
    return "\n".join(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_parser = subparsers.add_parser("build", help="build both preview packages")
    build_parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    build_parser.add_argument("--overwrite", action="store_true")
    verify_parser = subparsers.add_parser("verify", help="verify both preview packages")
    verify_parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    subparsers.add_parser("check", help="prove two clean builds are byte-for-byte identical")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "build":
            manifests = build_all(args.output_dir, overwrite=args.overwrite)
            action = "build"
        elif args.command == "verify":
            manifests = verify_all(args.output_dir)
            action = "verification"
        else:
            manifests = deterministic_check()
            action = "determinism check"
    except (OSError, ValueError, json.JSONDecodeError, tarfile.TarError) as exc:
        print(f"package {args.command} failed: {exc}")
        return 1
    print(render_summary(action, manifests))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
