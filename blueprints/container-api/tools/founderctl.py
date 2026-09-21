#!/usr/bin/env python3
"""Offline safety helpers for the Founder Toolkit for OCI Container API preview.

This tool invokes only the read-only ``terraform show -json`` operation, using
an argument array and no shell, to bind reviews to exact saved plans. It never
invokes apply/destroy, the OCI CLI, or Docker, and emits strict, redacted JSON.
"""

from __future__ import annotations

import argparse
import datetime as dt
import email.utils
import hashlib
import ipaddress
import json
import os
import re
import shutil
import ssl
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
import zipfile
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple
from urllib.parse import urlsplit


SCHEMA_VERSION = "1.2"
BLUEPRINT_VERSION = "0.2.0-preview.4"
TERRAFORM_VERSION = "1.16.3"
MAX_JSON_BYTES = 50 * 1024 * 1024
MAX_HTTP_BODY_BYTES = 8192
MAX_IAC_SOURCE_BYTES = 5 * 1024 * 1024
IMAGE_DIGEST_RE = re.compile(r"@sha256:([0-9a-f]{64})$")
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
OCID_RE = re.compile(r"^ocid1\.[a-z0-9-]+\.")
REGION_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)+-[0-9]+$")
OCI_PROFILE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
REVISION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/@:+-]{0,127}$")
SECRET_NAME_RE = re.compile(
    r"secret|password|passwd|token|api[_-]?key|private[_-]?key", re.IGNORECASE
)
EXPECTED_HEALTH_BODY = b'{"status":"ok"}'
EXPECTED_HEALTH_BODY_SHA256 = hashlib.sha256(EXPECTED_HEALTH_BODY).hexdigest()
BLUEPRINT_ROOT = Path(__file__).resolve().parents[1]

KNOWN_RESOURCE_TYPES = {
    "oci_apigateway_deployment",
    "oci_apigateway_gateway",
    "oci_artifacts_container_repository",
    "oci_budget_alert_rule",
    "oci_budget_budget",
    "oci_container_instances_container_instance",
    "oci_core_internet_gateway",
    "oci_core_network_security_group",
    "oci_core_network_security_group_security_rule",
    "oci_core_route_table",
    "oci_core_security_list",
    "oci_core_service_gateway",
    "oci_core_subnet",
    "oci_core_vcn",
    "oci_identity_dynamic_group",
    "oci_identity_policy",
    "oci_logging_log",
    "oci_logging_log_group",
    "oci_monitoring_alarm",
    "oci_ons_notification_topic",
    "oci_ons_subscription",
}

BOOTSTRAP_ADDRESS_TYPES = {
    "oci_artifacts_container_repository.api": "oci_artifacts_container_repository",
    "oci_budget_alert_rule.actual": "oci_budget_alert_rule",
    "oci_budget_budget.sandbox": "oci_budget_budget",
    "oci_identity_dynamic_group.container_instances": "oci_identity_dynamic_group",
    "oci_identity_policy.container_instances_pull": "oci_identity_policy",
}

RUNTIME_ADDRESS_TYPES = {
    "oci_apigateway_deployment.api": "oci_apigateway_deployment",
    "oci_apigateway_gateway.api": "oci_apigateway_gateway",
    "oci_container_instances_container_instance.api": "oci_container_instances_container_instance",
    "oci_core_internet_gateway.public[0]": "oci_core_internet_gateway",
    "oci_core_network_security_group.app": "oci_core_network_security_group",
    "oci_core_network_security_group.gateway": "oci_core_network_security_group",
    "oci_core_network_security_group_security_rule.app_dns_tcp": "oci_core_network_security_group_security_rule",
    "oci_core_network_security_group_security_rule.app_dns_udp": "oci_core_network_security_group_security_rule",
    "oci_core_network_security_group_security_rule.app_from_gateway": "oci_core_network_security_group_security_rule",
    "oci_core_network_security_group_security_rule.app_to_oracle_services": "oci_core_network_security_group_security_rule",
    "oci_core_network_security_group_security_rule.gateway_to_app": "oci_core_network_security_group_security_rule",
    "oci_core_route_table.app": "oci_core_route_table",
    "oci_core_route_table.gateway": "oci_core_route_table",
    "oci_core_security_list.empty": "oci_core_security_list",
    "oci_core_service_gateway.oracle_services": "oci_core_service_gateway",
    "oci_core_subnet.app": "oci_core_subnet",
    "oci_core_subnet.gateway": "oci_core_subnet",
    "oci_core_vcn.sandbox": "oci_core_vcn",
    "oci_logging_log.gateway_access": "oci_logging_log",
    "oci_logging_log.gateway_execution": "oci_logging_log",
    "oci_logging_log_group.api": "oci_logging_log_group",
    "oci_monitoring_alarm.high_cpu": "oci_monitoring_alarm",
    "oci_monitoring_alarm.high_memory": "oci_monitoring_alarm",
    "oci_ons_notification_topic.alarms": "oci_ons_notification_topic",
    "oci_ons_subscription.email": "oci_ons_subscription",
}

RUNTIME_DATA_ADDRESS_TYPES = {
    "data.oci_core_services.oracle_services": "oci_core_services",
    "data.oci_identity_availability_domains.available": "oci_identity_availability_domains",
}

GATEWAY_INGRESS_ADDRESS_RE = re.compile(
    r'^oci_core_network_security_group_security_rule\.gateway_https_ingress\["([^"\\]+)"\]$'
)

COST_DRIVERS = {
    "oci_apigateway_deployment": "API Gateway requests and data processing",
    "oci_apigateway_gateway": "API Gateway capacity and usage",
    "oci_artifacts_container_repository": "OCIR image storage and transfer",
    "oci_container_instances_container_instance": "Container Instance OCPU and memory while active",
    "oci_logging_log": "Logging ingestion and retention",
    "oci_monitoring_alarm": "Monitoring alarm evaluation",
    "oci_ons_notification_topic": "Notification delivery",
}

BOOTSTRAP_CONFIG_KEYS = {
    "tenancy_ocid",
    "compartment_id",
    "home_region",
    "target_region",
    "oci_profile",
    "project_slug",
    "owner",
    "expires_at",
    "repository_name",
    "ocir_registry_endpoint",
    "monthly_budget_amount",
    "budget_alert_percentage",
    "budget_recipients",
    "budget_target_verified_without_existing_budget",
    "extra_freeform_tags",
}

RUNTIME_CONFIG_KEYS = {
    "tenancy_ocid",
    "compartment_id",
    "region",
    "oci_profile",
    "environment_class",
    "project_slug",
    "release_id",
    "owner",
    "expires_at",
    "container_image_url",
    "approved_repository_path",
    "availability_domain",
    "container_shape",
    "ocpus",
    "memory_in_gbs",
    "container_port",
    "environment_variables",
    "vcn_cidr",
    "gateway_subnet_cidr",
    "app_subnet_cidr",
    "gateway_endpoint_type",
    "allowed_ingress_cidrs",
    "api_path_prefix",
    "rate_limit_requests_per_second",
    "notification_email",
    "api_gateway_logging_service_name",
    "cpu_alarm_threshold",
    "memory_alarm_threshold",
    "extra_freeform_tags",
}

RECEIPT_OUTPUT_KEYS = {
    "bootstrap": {
        "repository_id",
        "repository_path",
        "dynamic_group_id",
        "image_pull_policy_id",
        "budget_id",
        "budget_alert_rule_id",
    },
    "runtime": {
        "endpoint",
        "healthcheck_url",
        "gateway_endpoint_type",
        "container_image_url",
        "container_instance_id",
        "container_id",
        "container_vnic_id",
        "gateway_id",
        "deployment_id",
        "log_group_id",
        "gateway_access_log_id",
        "gateway_execution_log_id",
        "notification_topic_id",
        "notification_subscription_id",
        "notification_subscription_state",
        "cpu_alarm_id",
        "memory_alarm_id",
    },
}

RUNTIME_CHILD_READBACK_OUTPUTS = {
    "oci_container_instances_container_instance.api#container": "container_id",
    "oci_container_instances_container_instance.api#vnic": "container_vnic_id",
}


class ContractError(ValueError):
    """A safe, user-facing contract failure without embedded artifact values."""


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def iso_now() -> str:
    return utc_now().isoformat().replace("+00:00", "Z")


def load_json(path: Path, max_bytes: int = MAX_JSON_BYTES) -> Any:
    size = path.stat().st_size
    if size > max_bytes:
        raise ContractError(f"{path.name}: JSON exceeds the {max_bytes}-byte safety limit")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContractError(f"{path.name}: invalid JSON at line {exc.lineno}, column {exc.colno}")


def load_json_source(source: str, label: str) -> Tuple[Any, str]:
    """Load JSON from a file or bounded stdin and return its SHA-256."""
    if source == "-":
        raw = sys.stdin.buffer.read(MAX_JSON_BYTES + 1)
        if len(raw) > MAX_JSON_BYTES:
            raise ContractError(f"{label}: stdin exceeds the {MAX_JSON_BYTES}-byte safety limit")
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ContractError(f"{label}: stdin is not valid UTF-8 JSON")
        return value, hashlib.sha256(raw).hexdigest()
    path = Path(source)
    return load_json(path), sha256_file(path)


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def write_private_json(path: Path, value: Any) -> None:
    requested_path = path.absolute()
    normalized_text = str(requested_path)
    for system_alias in ("/var", "/tmp"):
        alias_path = Path(system_alias)
        if (
            (normalized_text == system_alias or normalized_text.startswith(system_alias + "/"))
            and alias_path.is_symlink()
            and alias_path.resolve() == Path("/private" + system_alias)
        ):
            normalized_text = "/private" + normalized_text
            break
    normalized_path = Path(normalized_text)
    path = normalized_path
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    if not getattr(os, "O_NOFOLLOW", 0) or os.open not in os.supports_dir_fd:
        raise ContractError("secure artifact writing requires O_NOFOLLOW and dirfd support")
    parent_descriptor = os.open(path.anchor, directory_flags)
    temporary_name: Optional[str] = None
    try:
        for component in path.parent.parts[1:]:
            if component in ("", ".", ".."):
                raise ContractError(f"{path.name}: output path contains an unsafe component")
            try:
                child_descriptor = os.open(component, directory_flags, dir_fd=parent_descriptor)
            except FileNotFoundError:
                try:
                    os.mkdir(component, mode=0o700, dir_fd=parent_descriptor)
                    child_descriptor = os.open(component, directory_flags, dir_fd=parent_descriptor)
                except OSError as exc:
                    raise ContractError(f"{path.name}: output directory could not be created safely") from exc
            except OSError as exc:
                raise ContractError(f"{path.name}: output path must not traverse a symlink") from exc
            os.close(parent_descriptor)
            parent_descriptor = child_descriptor

        try:
            target_status = os.stat(path.name, dir_fd=parent_descriptor, follow_symlinks=False)
        except FileNotFoundError:
            target_status = None
        if target_status is not None and not stat.S_ISREG(target_status.st_mode):
            raise ContractError(f"{path.name}: output target must be a regular file, not a symlink")

        temporary_name = f".{path.name}.{uuid.uuid4().hex}.tmp"
        descriptor = os.open(
            temporary_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
            dir_fd=parent_descriptor,
        )
        with os.fdopen(descriptor, "wb") as handle:
            os.fchmod(handle.fileno(), 0o600)
            handle.write(canonical_bytes(value))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(
            temporary_name,
            path.name,
            src_dir_fd=parent_descriptor,
            dst_dir_fd=parent_descriptor,
        )
        temporary_name = None
        os.fsync(parent_descriptor)
    except Exception:
        if temporary_name is not None:
            try:
                os.unlink(temporary_name, dir_fd=parent_descriptor)
            except FileNotFoundError:
                pass
        raise
    finally:
        os.close(parent_descriptor)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iac_source_snapshot(
    stack: str,
) -> Tuple[str, List[Dict[str, str]], Dict[str, bytes]]:
    if stack not in ("bootstrap", "runtime"):
        raise ContractError("unsupported Terraform source stack")
    source_root = BLUEPRINT_ROOT / "terraform" / stack
    paths = sorted(
        set(source_root.glob("*.tf"))
        | set(source_root.glob("*.tf.json"))
        | {source_root / ".terraform.lock.hcl"},
        key=lambda item: item.name,
    )
    if not paths:
        raise ContractError("Terraform source manifest is empty")
    digest = hashlib.sha256()
    manifest: List[Dict[str, str]] = []
    payloads: Dict[str, bytes] = {}
    total_bytes = 0
    for path in paths:
        if path.is_symlink() or not path.is_file():
            raise ContractError("Terraform source manifest contains a non-regular file")
        payload = path.read_bytes()
        total_bytes += len(payload)
        if total_bytes > MAX_IAC_SOURCE_BYTES:
            raise ContractError("Terraform source manifest exceeds the safety limit")
        file_hash = hashlib.sha256(payload).hexdigest()
        manifest.append({"path": path.name, "sha256": file_hash})
        payloads[path.name] = payload
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_hash.encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest(), manifest, payloads


def iac_source_evidence(stack: str) -> Tuple[str, List[Dict[str, str]]]:
    source_hash, manifest, _payloads = iac_source_snapshot(stack)
    return source_hash, manifest


def saved_plan_source_evidence(
    saved_plan_path: Path, stack: str, expected_saved_plan_hash: str
) -> Tuple[str, List[Dict[str, str]]]:
    if saved_plan_path.is_symlink() or not saved_plan_path.is_file():
        raise ContractError("saved plan must be an existing regular file, not a symlink")
    if not HASH_RE.fullmatch(expected_saved_plan_hash):
        raise ContractError("saved plan hash is malformed")
    hash_before = sha256_file(saved_plan_path)
    if hash_before != expected_saved_plan_hash:
        raise ContractError("saved plan changed before source provenance validation")

    source_hash, manifest, source_payloads = iac_source_snapshot(stack)
    expected_members = {
        (
            ".terraform.lock.hcl"
            if entry["path"] == ".terraform.lock.hcl"
            else f"tfconfig/m-/{entry['path']}"
        ): source_payloads[entry["path"]]
        for entry in manifest
    }
    try:
        with zipfile.ZipFile(saved_plan_path, "r") as archive:
            members = archive.infolist()
            member_names = [member.filename for member in members]
            if len(member_names) != len(set(member_names)):
                raise ContractError("saved plan source snapshot contains duplicate members")
            embedded_source_names = {
                name
                for name in member_names
                if name.startswith("tfconfig/m-/")
                and (name.endswith(".tf") or name.endswith(".tf.json"))
            }
            expected_source_names = {
                name for name in expected_members if name.startswith("tfconfig/m-/")
            }
            if (
                embedded_source_names != expected_source_names
                or ".terraform.lock.hcl" not in member_names
            ):
                raise ContractError(
                    "saved plan source snapshot does not match the reviewed Terraform file set"
                )
            info_by_name = {member.filename: member for member in members}
            for name, expected_bytes in expected_members.items():
                info = info_by_name[name]
                if info.is_dir() or info.file_size != len(expected_bytes):
                    raise ContractError(
                        "saved plan source snapshot does not match the reviewed Terraform sources"
                    )
                with archive.open(info, "r") as handle:
                    embedded_bytes = handle.read(len(expected_bytes) + 1)
                if embedded_bytes != expected_bytes:
                    raise ContractError(
                        "saved plan source snapshot does not match the reviewed Terraform sources"
                    )
    except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
        raise ContractError("saved plan lacks a readable Terraform source snapshot") from exc

    if sha256_file(saved_plan_path) != hash_before:
        raise ContractError("saved plan changed during source provenance validation")
    return source_hash, manifest


def terraform_environment() -> Dict[str, str]:
    environment = os.environ.copy()
    for name in ("TF_CLI_ARGS", "TF_CLI_ARGS_show", "TF_LOG", "TF_LOG_PATH"):
        environment.pop(name, None)
    environment.update({"TF_IN_AUTOMATION": "1", "TF_INPUT": "0"})
    return environment


def resolve_terraform_executable(terraform_bin: str) -> Path:
    if not terraform_bin or "\x00" in terraform_bin:
        raise ContractError("terraform executable is invalid")
    executable = shutil.which(terraform_bin)
    if executable is None:
        raise ContractError("Terraform executable was not found")
    executable_path = Path(executable).resolve()
    if executable_path.name not in ("terraform", "terraform.exe") or not executable_path.is_file():
        raise ContractError("terraform executable must resolve to a regular binary named terraform")
    try:
        version_result = subprocess.run(
            [str(executable_path), "version", "-json"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=15,
            env=terraform_environment(),
        )
        version_payload = json.loads(version_result.stdout.decode("utf-8"))
    except (OSError, subprocess.TimeoutExpired, UnicodeDecodeError, json.JSONDecodeError):
        raise ContractError("Terraform version could not be verified")
    if version_result.returncode != 0 or version_payload.get("terraform_version") != TERRAFORM_VERSION:
        raise ContractError(f"Terraform {TERRAFORM_VERSION} is required")
    return executable_path


def decode_terraform_file(path: Path, terraform_bin: str, label: str) -> Tuple[Dict[str, Any], str, str]:
    if path.is_symlink() or not path.is_file():
        raise ContractError(f"{label} must be an existing regular file, not a symlink")
    executable_path = resolve_terraform_executable(terraform_bin)
    file_hash_before = sha256_file(path)
    try:
        completed = subprocess.run(
            [str(executable_path), "show", "-json", str(path)],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=120,
            env=terraform_environment(),
        )
    except (OSError, subprocess.TimeoutExpired):
        raise ContractError(f"terraform show could not decode the {label} safely")
    file_hash_after = sha256_file(path)
    if file_hash_before != file_hash_after:
        raise ContractError(f"{label} changed while it was being decoded")
    if completed.returncode != 0:
        raise ContractError(f"terraform show rejected the {label}")
    raw = completed.stdout
    if len(raw) > MAX_JSON_BYTES:
        raise ContractError(f"Terraform {label} JSON exceeds the {MAX_JSON_BYTES}-byte safety limit")
    try:
        decoded = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ContractError("terraform show returned invalid UTF-8 JSON")
    return require_object(decoded, f"Terraform {label} JSON"), hashlib.sha256(raw).hexdigest(), file_hash_before


def decode_saved_plan(saved_plan_path: Path, terraform_bin: str) -> Tuple[Dict[str, Any], str, str]:
    """Decode exactly one saved Terraform plan with argv-safe, read-only execution."""
    return decode_terraform_file(saved_plan_path, terraform_bin, "saved plan")


def decode_saved_state(
    state_path: Path, terraform_bin: str
) -> Tuple[Dict[str, Any], str, str, int]:
    """Decode an exact raw Terraform state snapshot without printing its values."""
    raw_state = require_object(load_json(state_path), "raw Terraform state")
    lineage = raw_state.get("lineage")
    serial = raw_state.get("serial")
    if (
        raw_state.get("version") != 4
        or not isinstance(lineage, str)
        or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{7,127}", lineage)
        or not isinstance(serial, int)
        or isinstance(serial, bool)
        or serial < 0
    ):
        raise ContractError("raw Terraform state lacks a supported lineage and serial")
    decoded, _rendered_hash, state_hash = decode_terraform_file(
        state_path, terraform_bin, "state snapshot"
    )
    return decoded, state_hash, lineage, serial


def validate_target(
    principal: Any,
    tenancy: Any,
    region: Any,
    compartment: Any,
    home_region: Any = None,
    oci_profile: Any = "DEFAULT",
) -> None:
    if not isinstance(principal, str) or not OCID_RE.match(principal):
        raise ContractError("principal must be an OCI resource identifier")
    if not isinstance(tenancy, str) or not tenancy.startswith("ocid1.tenancy."):
        raise ContractError("tenancy must be a tenancy OCID")
    if not isinstance(compartment, str) or not compartment.startswith("ocid1.compartment."):
        raise ContractError("compartment must be a non-root compartment OCID")
    if tenancy == compartment:
        raise ContractError("target compartment must not be the tenancy root")
    if not isinstance(region, str) or not REGION_RE.fullmatch(region):
        raise ContractError("region must be an explicit OCI region identifier")
    if home_region is not None and (not isinstance(home_region, str) or not REGION_RE.fullmatch(home_region)):
        raise ContractError("home_region must be an explicit OCI region identifier")
    if not isinstance(oci_profile, str) or not OCI_PROFILE_RE.fullmatch(oci_profile):
        raise ContractError("oci_profile must be an explicit OCI CLI profile name")


def parse_rfc3339_utc(raw: Any, label: str) -> dt.datetime:
    if not isinstance(raw, str):
        raise ContractError(f"{label} must be a UTC timestamp")
    try:
        return dt.datetime.strptime(raw, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    except ValueError:
        raise ContractError(f"{label} must use UTC RFC 3339 form YYYY-MM-DDTHH:MM:SSZ")


def fingerprint(
    principal: str,
    tenancy: str,
    region: str,
    compartment: str,
    home_region: Optional[str] = None,
    oci_profile: str = "DEFAULT",
) -> str:
    fields = (principal, tenancy, region, compartment, oci_profile)
    if home_region is not None:
        fields += (home_region,)
    material = "\0".join(fields).encode("utf-8")
    return hashlib.sha256(material).hexdigest()[:16]


def require_object(value: Any, label: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be a JSON object")
    return value


def require_keys(value: Mapping[str, Any], required: Iterable[str], label: str) -> None:
    missing = sorted(set(required) - set(value))
    if missing:
        raise ContractError(f"{label} is missing required fields: {', '.join(missing)}")


def contains_sensitive_marker(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, dict):
        return any(contains_sensitive_marker(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_sensitive_marker(item) for item in value)
    return False


def nested_unknown(value: Any, key_names: Set[str]) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in key_names and contains_sensitive_marker(item):
                return True
            if nested_unknown(item, key_names):
                return True
    elif isinstance(value, list):
        return any(nested_unknown(item, key_names) for item in value)
    return False


def parse_expiry(raw: Any) -> dt.datetime:
    if not isinstance(raw, str):
        raise ContractError("expires_at must be a string")
    try:
        parsed = dt.datetime.strptime(raw, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    except ValueError:
        raise ContractError("expires_at must use UTC RFC 3339 form YYYY-MM-DDTHH:MM:SSZ")
    now = utc_now()
    if parsed <= now:
        raise ContractError("expires_at must be in the future")
    if parsed > now + dt.timedelta(days=90):
        raise ContractError("sandbox expires_at must be within 90 days")
    return parsed


def reject_placeholders(value: Mapping[str, Any], fields: Sequence[str]) -> None:
    """Reject unfilled examples, not validate or authorize network destinations.

    Domain examples are identified in a parsed hostname/email domain, never in
    an unrelated path, query, display name, or similarly named real domain.
    Field-specific URL, repository, and email validation remains separate.
    """
    for field in fields:
        raw = value.get(field)
        if not isinstance(raw, str):
            continue
        if "replace" in raw.lower():
            raise ContractError(f"{field} still contains an example placeholder")
        domains: Iterable[Optional[str]]
        if field in {"budget_recipients", "notification_email"}:
            # Parsing only locates the example domain; it does not certify an
            # address/list as valid or authorize a notification recipient.
            try:
                domains = [address.rpartition("@")[2] for _name, address in email.utils.getaddresses([raw])]
            except (ValueError, IndexError):
                domains = []
        else:
            try:
                parsed = urlsplit(raw if "://" in raw else "//" + raw)
                domains = [parsed.hostname]
            except ValueError:
                # Let the relevant field validator reject malformed input.
                domains = []
        for domain in domains:
            if domain is None:
                continue
            normalized = domain.lower().rstrip(".")
            if normalized == "example.com" or normalized.endswith(".example.com"):
                raise ContractError(f"{field} still contains an example placeholder")


def validate_nonsecret_tags(raw: Any) -> None:
    if raw is None:
        return
    if not isinstance(raw, dict) or not all(isinstance(key, str) and isinstance(value, str) for key, value in raw.items()):
        raise ContractError("extra_freeform_tags must be a string map")
    if any(SECRET_NAME_RE.search(key) for key in raw):
        raise ContractError("extra_freeform_tags contains a secret-like key")
    if any(not key or len(key) > 100 or len(value) > 256 for key, value in raw.items()):
        raise ContractError("extra_freeform_tags contains an empty or oversized key/value")


def validate_common_config(config: Mapping[str, Any]) -> None:
    tenancy = config.get("tenancy_ocid")
    compartment = config.get("compartment_id")
    if not isinstance(tenancy, str) or not tenancy.startswith("ocid1.tenancy."):
        raise ContractError("tenancy_ocid must be a tenancy OCID")
    if not isinstance(compartment, str) or not compartment.startswith("ocid1.compartment."):
        raise ContractError("compartment_id must be a compartment OCID")
    if tenancy == compartment:
        raise ContractError("the workload compartment must not be the tenancy root")
    slug = config.get("project_slug")
    if not isinstance(slug, str) or not re.fullmatch(r"[a-z][a-z0-9-]{2,23}", slug):
        raise ContractError("project_slug does not satisfy the blueprint contract")
    owner = config.get("owner")
    if not isinstance(owner, str) or not owner.strip() or len(owner) > 100:
        raise ContractError("owner must be a non-empty label of at most 100 characters")
    parse_expiry(config.get("expires_at"))
    validate_nonsecret_tags(config.get("extra_freeform_tags"))
    profile = config.get("oci_profile", "DEFAULT")
    if not isinstance(profile, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", profile):
        raise ContractError("oci_profile contains unsupported characters")


def validate_bootstrap_config(config: Mapping[str, Any]) -> List[str]:
    unknown = sorted(set(config) - BOOTSTRAP_CONFIG_KEYS)
    if unknown:
        raise ContractError(f"bootstrap config contains unknown fields: {', '.join(unknown)}")
    required = BOOTSTRAP_CONFIG_KEYS - {"extra_freeform_tags", "oci_profile"}
    require_keys(config, required, "bootstrap config")
    reject_placeholders(
        config,
        ("tenancy_ocid", "compartment_id", "home_region", "target_region", "ocir_registry_endpoint", "budget_recipients"),
    )
    validate_common_config(config)
    amount = config.get("monthly_budget_amount")
    if not isinstance(amount, (int, float)) or isinstance(amount, bool) or amount <= 0:
        raise ContractError("monthly_budget_amount must be greater than zero")
    threshold = config.get("budget_alert_percentage")
    if not isinstance(threshold, (int, float)) or isinstance(threshold, bool) or not 0 < threshold <= 100:
        raise ContractError("budget_alert_percentage must be greater than 0 and at most 100")
    endpoint = config.get("ocir_registry_endpoint")
    if not isinstance(endpoint, str) or "://" in endpoint or "/" in endpoint:
        raise ContractError("ocir_registry_endpoint must be a hostname without scheme or path")
    if config.get("budget_target_verified_without_existing_budget") is not True:
        raise ContractError("confirm that no existing budget targets the project compartment")
    repository_name = config.get("repository_name")
    if not isinstance(repository_name, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._/-]{1,254}", repository_name):
        raise ContractError("repository_name does not satisfy the lowercase OCIR contract")
    if "//" in repository_name:
        raise ContractError("repository_name must not contain an empty path segment")
    for region_field in ("home_region", "target_region"):
        if not isinstance(config.get(region_field), str) or not REGION_RE.fullmatch(config[region_field]):
            raise ContractError(f"{region_field} must be an explicit OCI region identifier")
    return ["budget is an alert, not a hard spending cap"]


def validate_runtime_config(config: Mapping[str, Any]) -> List[str]:
    unknown = sorted(set(config) - RUNTIME_CONFIG_KEYS)
    if unknown:
        raise ContractError(f"runtime config contains unknown fields: {', '.join(unknown)}")
    optional = {
        "environment_variables",
        "extra_freeform_tags",
        "vcn_cidr",
        "gateway_subnet_cidr",
        "app_subnet_cidr",
        "api_path_prefix",
        "rate_limit_requests_per_second",
        "cpu_alarm_threshold",
        "memory_alarm_threshold",
        "container_shape",
        "ocpus",
        "memory_in_gbs",
        "container_port",
        "oci_profile",
        "api_gateway_logging_service_name",
    }
    require_keys(config, RUNTIME_CONFIG_KEYS - optional, "runtime config")
    reject_placeholders(
        config,
        (
            "tenancy_ocid",
            "compartment_id",
            "region",
            "release_id",
            "approved_repository_path",
            "container_image_url",
            "availability_domain",
            "notification_email",
        ),
    )
    validate_common_config(config)
    if config.get("environment_class") != "sandbox":
        raise ContractError("Container API 0.2 preview refuses production environments")
    approved_repository_path = config.get("approved_repository_path")
    if (
        not isinstance(approved_repository_path, str)
        or "://" in approved_repository_path
        or "@" in approved_repository_path
        or not re.fullmatch(r"[A-Za-z0-9.-]+/[A-Za-z0-9._/-]+", approved_repository_path)
    ):
        raise ContractError("approved_repository_path must be the exact bootstrap repository path")
    image = config.get("container_image_url")
    match = IMAGE_DIGEST_RE.search(image) if isinstance(image, str) else None
    if (
        not match
        or match.group(1) == "0" * 64
        or not image.startswith(f"{approved_repository_path}@sha256:")
    ):
        raise ContractError("container_image_url must use approved_repository_path and a non-placeholder immutable digest")
    env = config.get("environment_variables", {})
    if not isinstance(env, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in env.items()):
        raise ContractError("environment_variables must be a string map")
    secret_names = sorted(name for name in env if SECRET_NAME_RE.search(name))
    if secret_names:
        raise ContractError("environment_variables contains secret-like names; use runtime secret retrieval")

    defaults = {
        "vcn_cidr": "10.42.0.0/16",
        "gateway_subnet_cidr": "10.42.0.0/24",
        "app_subnet_cidr": "10.42.1.0/24",
    }
    networks: Dict[str, ipaddress.IPv4Network] = {}
    for field, default in defaults.items():
        raw = config.get(field, default)
        try:
            network = ipaddress.ip_network(raw, strict=True)
        except (TypeError, ValueError):
            raise ContractError(f"{field} must be a canonical IPv4 CIDR")
        if not isinstance(network, ipaddress.IPv4Network):
            raise ContractError(f"{field} must be IPv4")
        networks[field] = network
    if not networks["gateway_subnet_cidr"].subnet_of(networks["vcn_cidr"]):
        raise ContractError("gateway_subnet_cidr must be inside vcn_cidr")
    if not networks["app_subnet_cidr"].subnet_of(networks["vcn_cidr"]):
        raise ContractError("app_subnet_cidr must be inside vcn_cidr")
    if networks["gateway_subnet_cidr"].overlaps(networks["app_subnet_cidr"]):
        raise ContractError("gateway and app subnet CIDRs must not overlap")
    if networks["gateway_subnet_cidr"].prefixlen > 24 or networks["app_subnet_cidr"].prefixlen > 24:
        raise ContractError("gateway and app subnets must be /24 or larger in this preview")

    endpoint_type = config.get("gateway_endpoint_type")
    if endpoint_type not in ("PUBLIC", "PRIVATE"):
        raise ContractError("gateway_endpoint_type must be PUBLIC or PRIVATE")
    ingress = config.get("allowed_ingress_cidrs")
    if not isinstance(ingress, list) or not ingress:
        raise ContractError("allowed_ingress_cidrs must be a non-empty list")
    parsed_ingress: List[ipaddress.IPv4Network] = []
    for raw in ingress:
        try:
            network = ipaddress.ip_network(raw, strict=True)
        except (TypeError, ValueError):
            raise ContractError("allowed_ingress_cidrs contains an invalid CIDR")
        if not isinstance(network, ipaddress.IPv4Network):
            raise ContractError("allowed_ingress_cidrs supports IPv4 in this preview")
        parsed_ingress.append(network)

    region = config.get("region")
    if not isinstance(region, str) or not REGION_RE.fullmatch(region):
        raise ContractError("region must be an explicit OCI region identifier")
    release_id = config.get("release_id")
    if not isinstance(release_id, str) or not REVISION_RE.fullmatch(release_id):
        raise ContractError("release_id contains unsupported characters")
    port = config.get("container_port", 8080)
    if not isinstance(port, int) or isinstance(port, bool) or not 1024 <= port <= 65535:
        raise ContractError("container_port must be an unprivileged TCP port")
    for field, default in (("ocpus", 1), ("memory_in_gbs", 2), ("rate_limit_requests_per_second", 10)):
        value = config.get(field, default)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
            raise ContractError(f"{field} must be greater than zero")
    for field, default in (("cpu_alarm_threshold", 80), ("memory_alarm_threshold", 85)):
        value = config.get(field, default)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 < value <= 100:
            raise ContractError(f"{field} must be greater than 0 and at most 100")
    api_prefix = config.get("api_path_prefix", "/api")
    if not isinstance(api_prefix, str) or not re.fullmatch(r"/[A-Za-z0-9._~-]+", api_prefix):
        raise ContractError("api_path_prefix must be one non-root path segment")
    notification_email = config.get("notification_email")
    if not isinstance(notification_email, str) or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", notification_email):
        raise ContractError("notification_email must look like an email address")
    logging_service = config.get("api_gateway_logging_service_name", "apigateway")
    if not isinstance(logging_service, str) or not logging_service.strip():
        raise ContractError("api_gateway_logging_service_name must not be empty")

    warnings = [
        "single Container Instance: no high-availability or zero-downtime claim",
        "notification email must be confirmed before the alarm path is considered verified",
        "Container Instance logs are bounded retrieval, not centralized application-log retention",
    ]
    if any(network == ipaddress.ip_network("0.0.0.0/0") for network in parsed_ingress):
        warnings.append("anonymous API Gateway ingress is open to the internet on TCP 443")
    return warnings


def command_config_check(args: argparse.Namespace) -> int:
    config = require_object(load_json(Path(args.config)), "config")
    warnings = (
        validate_bootstrap_config(config)
        if args.kind == "bootstrap"
        else validate_runtime_config(config)
    )
    result = {
        "schema_version": SCHEMA_VERSION,
        "kind": args.kind,
        "valid": True,
        "warnings": sorted(warnings),
    }
    if args.out:
        write_private_json(Path(args.out), result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def command_image_ref_check(args: argparse.Namespace) -> int:
    image = args.image
    match = IMAGE_DIGEST_RE.search(image) if isinstance(image, str) else None
    prefix = image.rsplit("@sha256:", 1)[0] if match else ""
    if (
        not match
        or match.group(1) == "0" * 64
        or not prefix
        or "://" in prefix
        or any(character.isspace() for character in image)
    ):
        raise ContractError("image must be a non-placeholder immutable reference ending in @sha256:<64 lowercase hex>")
    result = {
        "schema_version": SCHEMA_VERSION,
        "artifact": "image-reference-check",
        "valid": True,
        "digest": f"sha256:{match.group(1)}",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def action_class(actions: Any) -> str:
    if not isinstance(actions, list) or not all(isinstance(item, str) for item in actions):
        raise ContractError("plan contains a malformed action list")
    mapping = {
        ("no-op",): "no_op",
        ("create",): "create",
        ("read",): "read",
        ("update",): "update",
        ("delete",): "delete",
        ("delete", "create"): "replace_delete_first",
        ("create", "delete"): "replace_create_first",
    }
    key = tuple(actions)
    if key not in mapping:
        raise ContractError("plan contains an unsupported action combination")
    return mapping[key]


def expected_address_type(stack: str, address: str, mode: str) -> Optional[str]:
    if mode == "data":
        return RUNTIME_DATA_ADDRESS_TYPES.get(address) if stack == "runtime" else None
    contracts = BOOTSTRAP_ADDRESS_TYPES if stack == "bootstrap" else RUNTIME_ADDRESS_TYPES
    expected = contracts.get(address)
    if expected:
        return expected
    if stack == "runtime" and GATEWAY_INGRESS_ADDRESS_RE.fullmatch(address):
        return "oci_core_network_security_group_security_rule"
    return None


def plan_variable_values(plan: Mapping[str, Any]) -> Dict[str, Any]:
    raw_variables = plan.get("variables")
    if not isinstance(raw_variables, dict):
        return {}
    values: Dict[str, Any] = {}
    for name, raw in raw_variables.items():
        if isinstance(name, str) and isinstance(raw, dict) and "value" in raw:
            values[name] = raw["value"]
    return values


def collect_references(value: Any) -> Set[str]:
    references: Set[str] = set()
    if isinstance(value, dict):
        raw_references = value.get("references")
        if isinstance(raw_references, list):
            references.update(item for item in raw_references if isinstance(item, str))
        for item in value.values():
            references.update(collect_references(item))
    elif isinstance(value, list):
        for item in value:
            references.update(collect_references(item))
    return references


def configuration_resources(plan: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    configuration = plan.get("configuration")
    if not isinstance(configuration, dict):
        return {}
    root_module = configuration.get("root_module")
    if not isinstance(root_module, dict) or root_module.get("module_calls"):
        return {}
    resources = root_module.get("resources")
    if not isinstance(resources, list):
        return {}
    result: Dict[str, Dict[str, Any]] = {}
    for raw in resources:
        if not isinstance(raw, dict) or not isinstance(raw.get("address"), str):
            return {}
        if raw["address"] in result:
            return {}
        result[raw["address"]] = raw
    return result


def configuration_output_references(plan: Mapping[str, Any], name: str) -> Set[str]:
    configuration = plan.get("configuration")
    root_module = configuration.get("root_module") if isinstance(configuration, dict) else None
    outputs = root_module.get("outputs") if isinstance(root_module, dict) else None
    output = outputs.get(name) if isinstance(outputs, dict) else None
    expression = output.get("expression") if isinstance(output, dict) else None
    references = collect_references(expression)
    return {
        reference
        for reference in references
        if not any(
            other != reference
            and (other.startswith(reference + ".") or other.startswith(reference + "["))
            for other in references
        )
    }


def base_configuration_address(address: str) -> str:
    if GATEWAY_INGRESS_ADDRESS_RE.fullmatch(address):
        return "oci_core_network_security_group_security_rule.gateway_https_ingress"
    if address == "oci_core_internet_gateway.public[0]":
        return "oci_core_internet_gateway.public"
    return address


def configuration_references(
    resources: Mapping[str, Mapping[str, Any]], address: str, *expression_path: Any
) -> Set[str]:
    resource = resources.get(base_configuration_address(address))
    if not isinstance(resource, dict):
        return set()
    node: Any = resource.get("expressions")
    for component in expression_path:
        if isinstance(component, str) and isinstance(node, dict):
            node = node.get(component)
        elif isinstance(component, int) and isinstance(node, list) and 0 <= component < len(node):
            node = node[component]
        else:
            return set()
    references = collect_references(node)
    return {
        reference
        for reference in references
        if not any(
            other != reference
            and (other.startswith(reference + ".") or other.startswith(reference + "["))
            for other in references
        )
    }


def configuration_meta_references(
    resources: Mapping[str, Mapping[str, Any]], address: str, field: str
) -> Set[str]:
    resource = resources.get(base_configuration_address(address))
    if not isinstance(resource, dict):
        return set()
    references = collect_references(resource.get(field))
    return {
        reference
        for reference in references
        if not any(
            other != reference
            and (other.startswith(reference + ".") or other.startswith(reference + "["))
            for other in references
        )
    }


def target_binding_blockers(
    plan: Mapping[str, Any],
    stack: str,
    tenancy: str,
    region: str,
    compartment: str,
    home_region: Optional[str],
    oci_profile: str,
) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]], Set[str]]:
    blockers: Set[str] = set()
    variables = plan_variable_values(plan)
    required = {
        "tenancy_ocid": tenancy,
        "compartment_id": compartment,
        "oci_profile": oci_profile,
    }
    if stack == "bootstrap":
        required.update({"target_region": region, "home_region": home_region})
    else:
        required.update({"region": region, "environment_class": "sandbox"})
    if any(variables.get(name) != expected for name, expected in required.items()):
        blockers.add("plan_target_variable_mismatch")

    configuration = plan.get("configuration")
    provider_config = configuration.get("provider_config") if isinstance(configuration, dict) else None
    if not isinstance(provider_config, dict):
        blockers.add("provider_configuration_missing")
    else:
        oci_providers = [
            raw
            for raw in provider_config.values()
            if isinstance(raw, dict) and raw.get("full_name") == "registry.terraform.io/oracle/oci"
        ]
        expected_provider_bindings = (
            {(None, "var.home_region"), ("target", "var.target_region")}
            if stack == "bootstrap"
            else {(None, "var.region")}
        )
        if len(provider_config) != len(expected_provider_bindings) or len(oci_providers) != len(
            expected_provider_bindings
        ):
            blockers.add("provider_target_binding_mismatch")
        actual_provider_bindings: Set[Tuple[Optional[str], str]] = set()
        for provider in oci_providers:
            expressions = provider.get("expressions")
            if (
                provider.get("name") != "oci"
                or not isinstance(expressions, dict)
                or set(expressions) != {"config_file_profile", "region"}
            ):
                continue
            region_references = collect_references(expressions.get("region"))
            profile_references = collect_references(expressions.get("config_file_profile"))
            if profile_references != {"var.oci_profile"} or len(region_references) != 1:
                continue
            alias = provider.get("alias")
            if alias not in (None, "target"):
                continue
            actual_provider_bindings.add((alias, next(iter(region_references))))
        if actual_provider_bindings != expected_provider_bindings:
            blockers.add("provider_target_binding_mismatch")

    resources = configuration_resources(plan)
    if not resources:
        blockers.add("configuration_resource_contract_missing")
    return variables, resources, blockers


def expected_managed_plan_addresses(stack: str, variables: Mapping[str, Any]) -> Optional[Set[str]]:
    if stack == "bootstrap":
        return set(BOOTSTRAP_ADDRESS_TYPES)
    endpoint_type = variables.get("gateway_endpoint_type")
    ingress = variables.get("allowed_ingress_cidrs")
    if endpoint_type not in ("PUBLIC", "PRIVATE") or not isinstance(ingress, list) or not ingress:
        return None
    if not all(isinstance(item, str) for item in ingress) or len(ingress) != len(set(ingress)):
        return None
    try:
        parsed_ingress = [ipaddress.ip_network(item, strict=True) for item in ingress]
    except ValueError:
        return None
    if not all(isinstance(item, ipaddress.IPv4Network) for item in parsed_ingress):
        return None
    expected = set(RUNTIME_ADDRESS_TYPES)
    if endpoint_type != "PUBLIC":
        expected.discard("oci_core_internet_gateway.public[0]")
    expected.update(
        f"oci_core_network_security_group_security_rule.gateway_https_ingress[{json.dumps(cidr)}]"
        for cidr in ingress
    )
    return expected


def resource_scope_blockers(
    address: str,
    resource_type: str,
    values: Mapping[str, Any],
    stack: str,
    tenancy: str,
    compartment: str,
) -> Set[str]:
    blockers: Set[str] = set()
    if stack == "bootstrap":
        expected_compartment = (
            compartment
            if address == "oci_artifacts_container_repository.api"
            else tenancy
        )
        if address != "oci_budget_alert_rule.actual" and values.get("compartment_id") != expected_compartment:
            blockers.add("resource_compartment_mismatch")
        if address == "oci_budget_budget.sandbox" and values.get("targets") != [compartment]:
            blockers.add("budget_target_mismatch")
    else:
        without_top_level_compartment = {
            "oci_core_network_security_group_security_rule",
            "oci_logging_log",
        }
        if resource_type not in without_top_level_compartment and values.get("compartment_id") != compartment:
            blockers.add("resource_compartment_mismatch")
        if resource_type == "oci_logging_log":
            configurations = values.get("configuration")
            if (
                not isinstance(configurations, list)
                or len(configurations) != 1
                or not isinstance(configurations[0], dict)
                or configurations[0].get("compartment_id") != compartment
            ):
                blockers.add("logging_compartment_mismatch")
        if resource_type == "oci_monitoring_alarm" and values.get("metric_compartment_id") != compartment:
            blockers.add("metric_compartment_mismatch")
    return blockers


def destination_port_range(values: Mapping[str, Any], protocol: str) -> Optional[Tuple[int, int]]:
    key = "tcp_options" if protocol == "6" else "udp_options"
    options = values.get(key)
    if not isinstance(options, list) or len(options) != 1 or not isinstance(options[0], dict):
        return None
    ranges = options[0].get("destination_port_range")
    if not isinstance(ranges, list) or len(ranges) != 1 or not isinstance(ranges[0], dict):
        return None
    minimum = ranges[0].get("min")
    maximum = ranges[0].get("max")
    if not isinstance(minimum, int) or isinstance(minimum, bool) or not isinstance(maximum, int) or isinstance(maximum, bool):
        return None
    return minimum, maximum


def plan_resource_risks(
    address: str,
    resource_type: str,
    after: Any,
    after_unknown: Any,
    stack: str,
    classification: str,
    compartment: str,
    variables: Mapping[str, Any],
    config_resources: Mapping[str, Mapping[str, Any]],
) -> Tuple[List[str], List[str]]:
    risks: List[str] = []
    blockers: List[str] = []
    values = after if isinstance(after, dict) else {}

    if resource_type not in KNOWN_RESOURCE_TYPES:
        blockers.append("unclassified_resource_type")
    expected_type = expected_address_type(stack, address, "managed")
    if expected_type is None:
        blockers.append("unexpected_resource_address")
    elif expected_type != resource_type:
        blockers.append("resource_address_type_mismatch")
    if stack == "runtime" and resource_type.startswith("oci_identity_"):
        blockers.append("runtime_contains_iam")
    if resource_type == "oci_artifacts_container_repository":
        if values.get("is_public") is not False or values.get("is_immutable") is not True:
            blockers.append("repository_not_private_and_immutable")
        if values.get("display_name") != variables.get("repository_name"):
            blockers.append("repository_name_mismatch")
        if configuration_references(config_resources, address, "display_name") != {
            "var.repository_name"
        }:
            blockers.append("repository_name_reference_mismatch")
    if resource_type == "oci_identity_dynamic_group":
        matching_rule = values.get("matching_rule")
        expected_rule = (
            "ALL {resource.type='computecontainerinstance', "
            f"resource.compartment.id='{compartment}'}}"
        )
        if matching_rule != expected_rule:
            blockers.append("unexpected_dynamic_group_rule")
        if configuration_references(config_resources, address, "matching_rule") != {
            "var.compartment_id"
        }:
            blockers.append("dynamic_group_scope_reference_mismatch")
    if resource_type == "oci_identity_policy":
        statements = values.get("statements", [])
        slug = variables.get("project_slug")
        repository_name = variables.get("repository_name")
        expected_group = (
            f"{slug}-ci-{hashlib.sha256(compartment.encode('utf-8')).hexdigest()[:8]}"
            if isinstance(slug, str)
            else None
        )
        expected_statement = (
            f"Allow dynamic-group {expected_group} to read repos in compartment id {compartment} "
            f"where target.repo.name = '{repository_name}'"
            if expected_group is not None and isinstance(repository_name, str)
            else None
        )
        if not isinstance(statements, list) or len(statements) != 1:
            blockers.append("unknown_iam_statements")
        else:
            if any("manage all-resources" in str(statement).lower() for statement in statements):
                blockers.append("forbidden_manage_all_resources")
            if statements[0] != expected_statement:
                blockers.append("unexpected_image_pull_policy")
        if nested_unknown(after_unknown, {"statements"}):
            blockers.append("unknown_iam_statements")
        if configuration_references(config_resources, address, "statements") != {
            "oci_identity_dynamic_group.container_instances.name",
            "var.compartment_id",
            "var.repository_name",
        }:
            blockers.append("image_pull_policy_reference_mismatch")
    if address == "oci_budget_budget.sandbox" and configuration_references(
        config_resources, address, "targets"
    ) != {"var.compartment_id"}:
        blockers.append("budget_target_reference_mismatch")
    if address == "oci_budget_alert_rule.actual" and configuration_references(
        config_resources, address, "budget_id"
    ) != {"oci_budget_budget.sandbox.id"}:
        blockers.append("budget_alert_reference_mismatch")
    if resource_type == "oci_apigateway_gateway":
        endpoint_type = values.get("endpoint_type")
        if endpoint_type != variables.get("gateway_endpoint_type"):
            blockers.append("gateway_endpoint_type_mismatch")
        if endpoint_type == "PUBLIC":
            risks.append("public_api_gateway")
        elif endpoint_type not in ("PRIVATE", None):
            blockers.append("unknown_gateway_exposure")
        if nested_unknown(after_unknown, {"endpoint_type"}):
            blockers.append("unknown_gateway_security_field")
        if values.get("ip_mode") != "IPV4":
            blockers.append("gateway_not_ipv4")
        nsgs = values.get("network_security_group_ids")
        if not isinstance(nsgs, list) or len(nsgs) != 1:
            blockers.append("gateway_nsg_binding_missing")
        if configuration_references(
            config_resources, address, "network_security_group_ids"
        ) != {"oci_core_network_security_group.gateway.id"}:
            blockers.append("gateway_nsg_reference_mismatch")
        if configuration_references(config_resources, address, "subnet_id") != {
            "oci_core_subnet.gateway.id"
        }:
            blockers.append("gateway_subnet_reference_mismatch")
    if resource_type == "oci_core_network_security_group_security_rule":
        direction = values.get("direction")
        protocol = values.get("protocol")
        source = values.get("source")
        if direction == "INGRESS" and source in ("0.0.0.0/0", "::/0"):
            risks.append("world_ingress")
        if nested_unknown(after_unknown, {"direction", "protocol", "source_type", "destination_type", "tcp_options", "udp_options"}):
            blockers.append("unknown_nsg_security_field")
        expected: Optional[Tuple[str, str, str, Tuple[int, int]]] = None
        ingress_match = GATEWAY_INGRESS_ADDRESS_RE.fullmatch(address)
        if ingress_match:
            expected = ("INGRESS", "6", "CIDR_BLOCK", (443, 443))
            if source != ingress_match.group(1):
                blockers.append("gateway_ingress_source_mismatch")
            if configuration_meta_references(
                config_resources, address, "for_each_expression"
            ) != {"var.allowed_ingress_cidrs"}:
                blockers.append("gateway_ingress_iteration_reference_mismatch")
            if configuration_references(config_resources, address, "source") != {
                "each.value"
            }:
                blockers.append("gateway_ingress_source_reference_mismatch")
        elif address == "oci_core_network_security_group_security_rule.gateway_to_app":
            expected = ("EGRESS", "6", "NETWORK_SECURITY_GROUP", destination_port_range(values, "6") or (-1, -1))
        elif address == "oci_core_network_security_group_security_rule.app_from_gateway":
            expected = ("INGRESS", "6", "NETWORK_SECURITY_GROUP", destination_port_range(values, "6") or (-1, -1))
        elif address == "oci_core_network_security_group_security_rule.app_to_oracle_services":
            expected = ("EGRESS", "6", "SERVICE_CIDR_BLOCK", (443, 443))
        elif address == "oci_core_network_security_group_security_rule.app_dns_udp":
            expected = ("EGRESS", "17", "CIDR_BLOCK", (53, 53))
            if values.get("destination") != "169.254.169.254/32":
                blockers.append("unexpected_dns_destination")
        elif address == "oci_core_network_security_group_security_rule.app_dns_tcp":
            expected = ("EGRESS", "6", "CIDR_BLOCK", (53, 53))
            if values.get("destination") != "169.254.169.254/32":
                blockers.append("unexpected_dns_destination")
        if expected:
            endpoint_type = values.get("source_type") if direction == "INGRESS" else values.get("destination_type")
            if (direction, protocol, endpoint_type) != expected[:3]:
                blockers.append("unexpected_nsg_rule_shape")
            actual_port = destination_port_range(values, protocol) if isinstance(protocol, str) else None
            if address.endswith(("gateway_to_app", "app_from_gateway")):
                if actual_port != (variables.get("container_port", 8080),) * 2:
                    blockers.append("unexpected_backend_port")
            elif actual_port != expected[3]:
                blockers.append("unexpected_nsg_destination_port")
        owner_reference = (
            "oci_core_network_security_group.gateway.id"
            if ingress_match or address.endswith("gateway_to_app")
            else "oci_core_network_security_group.app.id"
        )
        if configuration_references(
            config_resources, address, "network_security_group_id"
        ) != {owner_reference}:
            blockers.append("nsg_rule_owner_reference_mismatch")
        peer_expectations = {
            "oci_core_network_security_group_security_rule.gateway_to_app": (
                "destination",
                "oci_core_network_security_group.app.id",
            ),
            "oci_core_network_security_group_security_rule.app_from_gateway": (
                "source",
                "oci_core_network_security_group.gateway.id",
            ),
        }
        if address in peer_expectations:
            expression_name, expected_reference = peer_expectations[address]
            if configuration_references(
                config_resources, address, expression_name
            ) != {expected_reference}:
                blockers.append("nsg_peer_reference_mismatch")
        if address == "oci_core_network_security_group_security_rule.app_to_oracle_services":
            if configuration_references(config_resources, address, "destination") != {
                "data.oci_core_services.oracle_services.services[0].cidr_block"
            }:
                blockers.append("oracle_services_destination_reference_mismatch")
    if resource_type == "oci_core_internet_gateway":
        risks.append("internet_gateway")
    vcn_bound_addresses = {
        "oci_core_internet_gateway.public[0]",
        "oci_core_service_gateway.oracle_services",
        "oci_core_route_table.gateway",
        "oci_core_route_table.app",
        "oci_core_security_list.empty",
        "oci_core_subnet.gateway",
        "oci_core_subnet.app",
        "oci_core_network_security_group.gateway",
        "oci_core_network_security_group.app",
    }
    if address in vcn_bound_addresses and configuration_references(
        config_resources, address, "vcn_id"
    ) != {"oci_core_vcn.sandbox.id"}:
        blockers.append("vcn_reference_mismatch")
    if address == "oci_core_service_gateway.oracle_services":
        services = values.get("services")
        if not isinstance(services, list) or len(services) != 1:
            blockers.append("service_gateway_contract_mismatch")
        if configuration_references(
            config_resources, address, "services", 0, "service_id"
        ) != {"data.oci_core_services.oracle_services.services[0].id"}:
            blockers.append("service_gateway_reference_mismatch")
    if resource_type == "oci_core_subnet" and values.get("prohibit_public_ip_on_vnic") is False:
        risks.append("public_subnet")
    if address == "oci_core_vcn.sandbox" and values.get("cidr_blocks") != [variables.get("vcn_cidr", "10.42.0.0/16")]:
        blockers.append("vcn_cidr_mismatch")
    if address == "oci_core_subnet.gateway":
        if (
            values.get("cidr_block") != variables.get("gateway_subnet_cidr", "10.42.0.0/24")
            or values.get("prohibit_public_ip_on_vnic")
            is not (variables.get("gateway_endpoint_type") != "PUBLIC")
        ):
            blockers.append("gateway_subnet_contract_mismatch")
        if (
            configuration_references(config_resources, address, "route_table_id")
            != {"oci_core_route_table.gateway.id"}
            or configuration_references(config_resources, address, "security_list_ids")
            != {"oci_core_security_list.empty.id"}
        ):
            blockers.append("gateway_subnet_reference_mismatch")
    if address == "oci_core_subnet.app" and values.get("cidr_block") != variables.get(
        "app_subnet_cidr", "10.42.1.0/24"
    ):
        blockers.append("app_subnet_cidr_mismatch")
    if address == "oci_core_subnet.app" and (
        configuration_references(config_resources, address, "route_table_id")
        != {"oci_core_route_table.app.id"}
        or configuration_references(config_resources, address, "security_list_ids")
        != {"oci_core_security_list.empty.id"}
    ):
        blockers.append("app_subnet_reference_mismatch")
    if address == "oci_core_subnet.app" and values.get("prohibit_public_ip_on_vnic") is not True:
        blockers.append("app_subnet_not_private")
    if address == "oci_core_security_list.empty":
        if values.get("ingress_security_rules") not in (None, []) or values.get("egress_security_rules") not in (None, []):
            blockers.append("security_list_not_empty")
    if address == "oci_core_route_table.app":
        rules = values.get("route_rules")
        if (
            not isinstance(rules, list)
            or len(rules) != 1
            or not isinstance(rules[0], dict)
            or rules[0].get("destination_type") != "SERVICE_CIDR_BLOCK"
            or rules[0].get("destination") in ("0.0.0.0/0", "::/0")
        ):
            blockers.append("unexpected_app_route_table")
        if configuration_references(
            config_resources, address, "route_rules", 0, "network_entity_id"
        ) != {"oci_core_service_gateway.oracle_services.id"}:
            blockers.append("app_route_gateway_reference_mismatch")
        if configuration_references(
            config_resources, address, "route_rules", 0, "destination"
        ) != {"data.oci_core_services.oracle_services.services[0].cidr_block"}:
            blockers.append("app_route_destination_reference_mismatch")
    if address == "oci_core_route_table.gateway":
        rules = values.get("route_rules")
        expected_public = variables.get("gateway_endpoint_type") == "PUBLIC"
        if expected_public:
            if (
                not isinstance(rules, list)
                or len(rules) != 1
                or not isinstance(rules[0], dict)
                or rules[0].get("destination") != "0.0.0.0/0"
                or rules[0].get("destination_type") != "CIDR_BLOCK"
            ):
                blockers.append("unexpected_gateway_route_table")
        elif rules not in (None, []):
            blockers.append("unexpected_gateway_route_table")
    if resource_type == "oci_container_instances_container_instance":
        image_urls = []
        containers = values.get("containers", [])
        if isinstance(containers, list):
            image_urls = [item.get("image_url") for item in containers if isinstance(item, dict)]
        if not image_urls or any(not isinstance(item, str) or not IMAGE_DIGEST_RE.search(item) for item in image_urls):
            blockers.append("mutable_or_unknown_container_image")
        if image_urls != [variables.get("container_image_url")]:
            blockers.append("container_image_variable_mismatch")
        for container in containers if isinstance(containers, list) else []:
            if not isinstance(container, dict):
                blockers.append("malformed_container_contract")
                continue
            if container.get("is_resource_principal_disabled") is not True:
                blockers.append("application_resource_principal_exposed")
            contexts = container.get("security_context", [])
            if not isinstance(contexts, list) or len(contexts) != 1 or not isinstance(contexts[0], dict):
                blockers.append("missing_container_security_context")
                continue
            context = contexts[0]
            if (
                context.get("is_non_root_user_check_enabled") is not True
                or context.get("is_root_file_system_readonly") is not True
                or context.get("run_as_user") != 65532
                or context.get("run_as_group") != 65532
            ):
                blockers.append("weak_container_security_context")
            capabilities = context.get("capabilities", [])
            if (
                not isinstance(capabilities, list)
                or len(capabilities) != 1
                or not isinstance(capabilities[0], dict)
                or capabilities[0].get("drop_capabilities") != ["ALL"]
                # OCI applies additions after drops; Add=ALL also overrides
                # Drop=ALL. An omitted, null, or empty addition list is safe.
                or capabilities[0].get("add_capabilities") not in (None, [])
            ):
                blockers.append("container_capabilities_not_dropped")
        vnics = values.get("vnics", [])
        if not isinstance(vnics, list) or len(vnics) != 1 or any(
            not isinstance(item, dict)
            or item.get("is_public_ip_assigned") is not False
            or not isinstance(item.get("nsg_ids"), list)
            or len(item.get("nsg_ids")) != 1
            for item in vnics
        ):
            blockers.append("container_public_ip_not_proven_false")
        try:
            expected_private_ip = str(
                ipaddress.ip_network(
                    variables.get("app_subnet_cidr", "10.42.1.0/24"), strict=True
                ).network_address
                + 10
            )
        except (TypeError, ValueError):
            expected_private_ip = None
        if not vnics or not isinstance(vnics[0], dict) or vnics[0].get("private_ip") != expected_private_ip:
            blockers.append("container_private_ip_mismatch")
        if (
            configuration_references(config_resources, address, "vnics", 0, "subnet_id")
            != {"oci_core_subnet.app.id"}
            or configuration_references(config_resources, address, "vnics", 0, "nsg_ids")
            != {"oci_core_network_security_group.app.id"}
        ):
            blockers.append("container_vnic_reference_mismatch")
        if nested_unknown(after_unknown, {"image_url", "is_public_ip_assigned", "is_resource_principal_disabled", "security_context"}):
            blockers.append("unknown_container_security_field")
    if resource_type == "oci_apigateway_deployment":
        if configuration_references(config_resources, address, "gateway_id") != {
            "oci_apigateway_gateway.api.id"
        }:
            blockers.append("api_deployment_gateway_reference_mismatch")
        specifications = values.get("specification")
        expected_prefix = variables.get("api_path_prefix", "/api")
        expected_ip = None
        try:
            expected_ip = str(
                ipaddress.ip_network(
                    variables.get("app_subnet_cidr", "10.42.1.0/24"), strict=True
                ).network_address
                + 10
            )
        except (TypeError, ValueError):
            pass
        expected_port = variables.get("container_port", 8080)
        expected_routes = {
            "/": f"http://{expected_ip}:{expected_port}/",
            "/healthz": f"http://{expected_ip}:{expected_port}/healthz",
            "/readyz": f"http://{expected_ip}:{expected_port}/readyz",
        }
        observed_routes: Dict[str, str] = {}
        routes_valid = False
        rate_limit_valid = False
        if isinstance(specifications, list) and len(specifications) == 1 and isinstance(specifications[0], dict):
            routes = specifications[0].get("routes")
            request_policies = specifications[0].get("request_policies")
            if (
                isinstance(request_policies, list)
                and len(request_policies) == 1
                and isinstance(request_policies[0], dict)
            ):
                rate_limits = request_policies[0].get("rate_limiting")
                rate_limit_valid = (
                    isinstance(rate_limits, list)
                    and len(rate_limits) == 1
                    and isinstance(rate_limits[0], dict)
                    and rate_limits[0].get("rate_in_requests_per_second")
                    == variables.get("rate_limit_requests_per_second", 10)
                    and rate_limits[0].get("rate_key") == "CLIENT_IP"
                )
            if isinstance(routes, list) and len(routes) == len(expected_routes):
                routes_valid = True
                for route in routes:
                    if not isinstance(route, dict) or route.get("methods") != ["GET"]:
                        routes_valid = False
                        break
                    path = route.get("path")
                    if not isinstance(path, str) or path not in expected_routes or path in observed_routes:
                        routes_valid = False
                        break
                    backends = route.get("backend")
                    if not isinstance(backends, list) or len(backends) != 1 or not isinstance(backends[0], dict):
                        routes_valid = False
                        break
                    backend = backends[0]
                    if (
                        backend.get("type") != "HTTP_BACKEND"
                        or backend.get("url") != expected_routes[path]
                        or backend.get("connect_timeout_in_seconds") != 5
                        or backend.get("read_timeout_in_seconds") != 15
                        or backend.get("send_timeout_in_seconds") != 15
                    ):
                        routes_valid = False
                        break
                    observed_routes[path] = backend["url"]
        if (
            values.get("path_prefix") != expected_prefix
            or not routes_valid
            or observed_routes != expected_routes
            or not rate_limit_valid
        ):
            blockers.append("api_deployment_route_contract_mismatch")
        if nested_unknown(after_unknown, {"path_prefix", "specification"}):
            blockers.append("unknown_api_deployment_security_field")
    if resource_type == "oci_logging_log":
        configurations = values.get("configuration")
        source = None
        if (
            isinstance(configurations, list)
            and len(configurations) == 1
            and isinstance(configurations[0], dict)
        ):
            sources = configurations[0].get("source")
            if isinstance(sources, list) and len(sources) == 1 and isinstance(sources[0], dict):
                source = sources[0]
        expected_category = (
            "access" if address == "oci_logging_log.gateway_access" else "execution"
        )
        if (
            values.get("log_type") != "SERVICE"
            or values.get("is_enabled") is not True
            or values.get("retention_duration") != 30
            or source is None
            or source.get("category") != expected_category
            or source.get("service")
            != variables.get("api_gateway_logging_service_name", "apigateway")
            or source.get("source_type") != "OCISERVICE"
        ):
            blockers.append("logging_operational_contract_mismatch")
        if configuration_references(config_resources, address, "log_group_id") != {
            "oci_logging_log_group.api.id"
        }:
            blockers.append("logging_group_reference_mismatch")
        if configuration_references(
            config_resources, address, "configuration", 0, "compartment_id"
        ) != {"var.compartment_id"}:
            blockers.append("logging_compartment_reference_mismatch")
        if configuration_references(
            config_resources, address, "configuration", 0, "source", 0, "resource"
        ) != {"oci_apigateway_deployment.api.id"}:
            blockers.append("logging_source_resource_reference_mismatch")
        if configuration_references(
            config_resources, address, "configuration", 0, "source", 0, "service"
        ) != {"var.api_gateway_logging_service_name"}:
            blockers.append("logging_service_reference_mismatch")
    if address == "oci_ons_subscription.email":
        if (
            values.get("protocol") != "EMAIL"
            or values.get("endpoint") != variables.get("notification_email")
        ):
            blockers.append("notification_subscription_contract_mismatch")
        if configuration_references(config_resources, address, "topic_id") != {
            "oci_ons_notification_topic.alarms.id"
        }:
            blockers.append("notification_topic_reference_mismatch")
        if configuration_references(config_resources, address, "endpoint") != {
            "var.notification_email"
        }:
            blockers.append("notification_endpoint_reference_mismatch")
    if resource_type == "oci_monitoring_alarm":
        threshold_reference = (
            "var.cpu_alarm_threshold"
            if address == "oci_monitoring_alarm.high_cpu"
            else "var.memory_alarm_threshold"
        )
        destinations = values.get("destinations")
        if (
            values.get("namespace") != "oci_computecontainerinstance"
            or values.get("severity") != "WARNING"
            or values.get("is_enabled") is not True
            or values.get("pending_duration") != "PT5M"
            or not isinstance(destinations, list)
            or len(destinations) != 1
        ):
            blockers.append("monitoring_alarm_operational_contract_mismatch")
        if configuration_references(config_resources, address, "metric_compartment_id") != {
            "var.compartment_id"
        }:
            blockers.append("monitoring_compartment_reference_mismatch")
        if configuration_references(config_resources, address, "destinations") != {
            "oci_ons_notification_topic.alarms.id"
        }:
            blockers.append("monitoring_destination_reference_mismatch")
        if configuration_references(config_resources, address, "query") != {
            "oci_container_instances_container_instance.api.id",
            threshold_reference,
        }:
            blockers.append("monitoring_query_reference_mismatch")
    return sorted(set(risks)), sorted(set(blockers))


def nested_value(value: Any, *path: Any) -> Any:
    current = value
    for component in path:
        if isinstance(component, str) and isinstance(current, dict):
            current = current.get(component)
        elif isinstance(component, int) and isinstance(current, list) and 0 <= component < len(current):
            current = current[component]
        else:
            return None
    return current


def relationship_value_is_concrete(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return True
    if isinstance(value, list):
        return any(relationship_value_is_concrete(item) for item in value)
    if isinstance(value, dict):
        return any(relationship_value_is_concrete(item) for item in value.values())
    return True


def terraform_number_text(value: Any) -> str:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return str(value)
    try:
        rendered = format(Decimal(str(value)), "f")
    except InvalidOperation:
        return str(value)
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    return rendered or "0"


def plan_relationship_blockers(
    stack: str,
    managed_values: Mapping[str, Mapping[str, Any]],
    data_values: Mapping[str, Mapping[str, Any]],
    classifications: Mapping[str, str],
    variables: Mapping[str, Any],
) -> Set[str]:
    blockers: Set[str] = set()

    def planned(address: str, *path: Any) -> Any:
        collection = data_values if address.startswith("data.") else managed_values
        return nested_value(collection.get(address), *path)

    def check(
        source_address: str,
        source_path: Tuple[Any, ...],
        target_address: str,
        target_path: Tuple[Any, ...],
        code: str,
        *,
        as_list: bool = False,
    ) -> None:
        if source_address not in managed_values or classifications.get(source_address) == "delete":
            return
        actual = planned(source_address, *source_path)
        expected = planned(target_address, *target_path)
        if as_list:
            expected = [expected]
        if not relationship_value_is_concrete(actual):
            return
        if not relationship_value_is_concrete(expected) or actual != expected:
            blockers.add(code)

    if stack == "bootstrap":
        check(
            "oci_budget_alert_rule.actual",
            ("budget_id",),
            "oci_budget_budget.sandbox",
            ("id",),
            "planned_budget_alert_relationship_mismatch",
        )
        return blockers

    check(
        "oci_apigateway_gateway.api",
        ("network_security_group_ids",),
        "oci_core_network_security_group.gateway",
        ("id",),
        "planned_gateway_nsg_relationship_mismatch",
        as_list=True,
    )
    check(
        "oci_apigateway_gateway.api",
        ("subnet_id",),
        "oci_core_subnet.gateway",
        ("id",),
        "planned_gateway_subnet_relationship_mismatch",
    )
    for address in (
        "oci_core_internet_gateway.public[0]",
        "oci_core_service_gateway.oracle_services",
        "oci_core_route_table.gateway",
        "oci_core_route_table.app",
        "oci_core_security_list.empty",
        "oci_core_subnet.gateway",
        "oci_core_subnet.app",
        "oci_core_network_security_group.gateway",
        "oci_core_network_security_group.app",
    ):
        check(
            address,
            ("vcn_id",),
            "oci_core_vcn.sandbox",
            ("id",),
            "planned_vcn_relationship_mismatch",
        )
    for subnet, route_table in (
        ("oci_core_subnet.gateway", "oci_core_route_table.gateway"),
        ("oci_core_subnet.app", "oci_core_route_table.app"),
    ):
        check(
            subnet,
            ("route_table_id",),
            route_table,
            ("id",),
            "planned_subnet_route_relationship_mismatch",
        )
        check(
            subnet,
            ("security_list_ids",),
            "oci_core_security_list.empty",
            ("id",),
            "planned_subnet_security_list_relationship_mismatch",
            as_list=True,
        )
    check(
        "oci_core_service_gateway.oracle_services",
        ("services", 0, "service_id"),
        "data.oci_core_services.oracle_services",
        ("services", 0, "id"),
        "planned_service_gateway_relationship_mismatch",
    )
    check(
        "oci_core_route_table.app",
        ("route_rules", 0, "network_entity_id"),
        "oci_core_service_gateway.oracle_services",
        ("id",),
        "planned_app_route_gateway_relationship_mismatch",
    )
    check(
        "oci_core_route_table.app",
        ("route_rules", 0, "destination"),
        "data.oci_core_services.oracle_services",
        ("services", 0, "cidr_block"),
        "planned_app_route_destination_relationship_mismatch",
    )
    if variables.get("gateway_endpoint_type") == "PUBLIC":
        check(
            "oci_core_route_table.gateway",
            ("route_rules", 0, "network_entity_id"),
            "oci_core_internet_gateway.public[0]",
            ("id",),
            "planned_gateway_route_relationship_mismatch",
        )

    for address in managed_values:
        ingress = GATEWAY_INGRESS_ADDRESS_RE.fullmatch(address)
        if not ingress and not address.startswith(
            "oci_core_network_security_group_security_rule."
        ):
            continue
        owner = (
            "oci_core_network_security_group.gateway"
            if ingress or address.endswith("gateway_to_app")
            else "oci_core_network_security_group.app"
        )
        check(
            address,
            ("network_security_group_id",),
            owner,
            ("id",),
            "planned_nsg_owner_relationship_mismatch",
        )
    check(
        "oci_core_network_security_group_security_rule.gateway_to_app",
        ("destination",),
        "oci_core_network_security_group.app",
        ("id",),
        "planned_nsg_peer_relationship_mismatch",
    )
    check(
        "oci_core_network_security_group_security_rule.app_from_gateway",
        ("source",),
        "oci_core_network_security_group.gateway",
        ("id",),
        "planned_nsg_peer_relationship_mismatch",
    )
    check(
        "oci_core_network_security_group_security_rule.app_to_oracle_services",
        ("destination",),
        "data.oci_core_services.oracle_services",
        ("services", 0, "cidr_block"),
        "planned_oracle_services_relationship_mismatch",
    )
    check(
        "oci_container_instances_container_instance.api",
        ("vnics", 0, "subnet_id"),
        "oci_core_subnet.app",
        ("id",),
        "planned_container_subnet_relationship_mismatch",
    )
    check(
        "oci_container_instances_container_instance.api",
        ("vnics", 0, "nsg_ids"),
        "oci_core_network_security_group.app",
        ("id",),
        "planned_container_nsg_relationship_mismatch",
        as_list=True,
    )
    check(
        "oci_apigateway_deployment.api",
        ("gateway_id",),
        "oci_apigateway_gateway.api",
        ("id",),
        "planned_deployment_gateway_relationship_mismatch",
    )
    for address in (
        "oci_logging_log.gateway_access",
        "oci_logging_log.gateway_execution",
    ):
        check(
            address,
            ("log_group_id",),
            "oci_logging_log_group.api",
            ("id",),
            "planned_logging_group_relationship_mismatch",
        )
        check(
            address,
            ("configuration", 0, "source", 0, "resource"),
            "oci_apigateway_deployment.api",
            ("id",),
            "planned_logging_source_relationship_mismatch",
        )
    check(
        "oci_ons_subscription.email",
        ("topic_id",),
        "oci_ons_notification_topic.alarms",
        ("id",),
        "planned_notification_topic_relationship_mismatch",
    )
    for address in (
        "oci_monitoring_alarm.high_cpu",
        "oci_monitoring_alarm.high_memory",
    ):
        check(
            address,
            ("destinations",),
            "oci_ons_notification_topic.alarms",
            ("id",),
            "planned_monitoring_destination_relationship_mismatch",
            as_list=True,
        )
        query = planned(address, "query")
        container_id = planned("oci_container_instances_container_instance.api", "id")
        if relationship_value_is_concrete(query):
            threshold = (
                variables.get("cpu_alarm_threshold", 80)
                if address.endswith("high_cpu")
                else variables.get("memory_alarm_threshold", 85)
            )
            metric = "CpuUtilization" if address.endswith("high_cpu") else "MemoryUtilization"
            expected_query = (
                f'{metric}[1m]{{resourceId = "{container_id}"}}.mean() > '
                f'{terraform_number_text(threshold)}'
                if relationship_value_is_concrete(container_id)
                else None
            )
            if expected_query is None or query != expected_query:
                blockers.add("planned_monitoring_query_relationship_mismatch")
    return blockers


def build_plan_summary(
    plan: Mapping[str, Any],
    plan_json_source: Any,
    saved_plan_path: Path,
    stack: str,
    principal: str,
    tenancy: str,
    region: str,
    compartment: str,
    saved_plan_hash: Optional[str] = None,
    bootstrap_receipt_hash: Optional[str] = None,
    home_region: Optional[str] = None,
    oci_profile: str = "DEFAULT",
    source_evidence: Optional[Tuple[str, List[Dict[str, str]]]] = None,
) -> Dict[str, Any]:
    validate_target(principal, tenancy, region, compartment, home_region, oci_profile)
    if stack == "bootstrap" and home_region is None:
        raise ContractError("bootstrap plan summary requires the tenancy home region")
    if stack == "runtime" and home_region is not None:
        raise ContractError("runtime plan summary must not set home_region")
    format_version = plan.get("format_version")
    if not isinstance(format_version, str) or format_version.split(".", 1)[0] != "1":
        raise ContractError("unsupported Terraform plan JSON format major version")
    if plan.get("terraform_version") != TERRAFORM_VERSION:
        raise ContractError(f"saved plan must be generated by Terraform {TERRAFORM_VERSION}")
    resource_changes = plan.get("resource_changes", [])
    if not isinstance(resource_changes, list):
        raise ContractError("resource_changes must be an array")

    counts = {
        "create": 0,
        "delete": 0,
        "no_op": 0,
        "read": 0,
        "replace_create_first": 0,
        "replace_delete_first": 0,
        "update": 0,
    }
    resources: List[Dict[str, Any]] = []
    global_blockers: Set[str] = set()
    global_risks: Set[str] = set()
    cost_drivers: Set[str] = set()
    sensitive_addresses: Set[str] = set()
    variables, config_resources, binding_blockers = target_binding_blockers(
        plan, stack, tenancy, region, compartment, home_region, oci_profile
    )
    global_blockers.update(binding_blockers)
    if stack == "bootstrap" and configuration_output_references(
        plan, "repository_path"
    ) != {
        "var.ocir_registry_endpoint",
        "oci_artifacts_container_repository.api.namespace",
        "oci_artifacts_container_repository.api.display_name",
    }:
        global_blockers.add("repository_path_output_reference_mismatch")
    if plan.get("errored") is True:
        global_blockers.add("terraform_plan_errored")
    expected_addresses = expected_managed_plan_addresses(stack, variables)
    if expected_addresses is None:
        global_blockers.add("plan_address_contract_inputs_invalid")
    else:
        static_addresses = (
            set(BOOTSTRAP_ADDRESS_TYPES)
            if stack == "bootstrap"
            else set(RUNTIME_ADDRESS_TYPES)
            | {"oci_core_network_security_group_security_rule.gateway_https_ingress"}
        )
        expected_configuration_addresses = {
            base_configuration_address(address) for address in static_addresses
        }
        actual_configuration_addresses = {
            address
            for address, resource in config_resources.items()
            if resource.get("mode", "managed") == "managed"
        }
        if actual_configuration_addresses != expected_configuration_addresses:
            global_blockers.add("configuration_resource_set_mismatch")
        expected_data_configuration_addresses = (
            set(RUNTIME_DATA_ADDRESS_TYPES) if stack == "runtime" else set()
        )
        actual_data_configuration_addresses = {
            address
            for address, resource in config_resources.items()
            if resource.get("mode") == "data"
        }
        if actual_data_configuration_addresses != expected_data_configuration_addresses:
            global_blockers.add("configuration_data_source_set_mismatch")
    managed_addresses: List[str] = []
    planned_managed_values: Dict[str, Dict[str, Any]] = {}
    planned_data_values: Dict[str, Dict[str, Any]] = {}
    planned_classifications: Dict[str, str] = {}

    for raw in resource_changes:
        change = require_object(raw, "resource change")
        address = change.get("address")
        resource_type = change.get("type")
        mode = change.get("mode", "managed")
        if not isinstance(address, str) or not isinstance(resource_type, str):
            raise ContractError("resource change is missing a safe address or type")
        details = require_object(change.get("change"), "resource change.change")
        classification = action_class(details.get("actions"))
        counts[classification] += 1
        if mode == "data":
            data_after = details.get("after")
            if isinstance(data_after, dict):
                planned_data_values[address] = data_after
            expected_type = expected_address_type(stack, address, mode)
            if expected_type is None:
                global_blockers.add("unexpected_data_source_address")
            elif expected_type != resource_type:
                global_blockers.add("data_source_address_type_mismatch")
            config_resource = config_resources.get(address)
            configuration = plan.get("configuration", {})
            providers = (
                configuration.get("provider_config", {})
                if isinstance(configuration, dict)
                else {}
            )
            provider = (
                providers.get(config_resource.get("provider_config_key"))
                if isinstance(config_resource, dict) and isinstance(providers, dict)
                else None
            )
            if (
                not isinstance(config_resource, dict)
                or config_resource.get("mode") != "data"
                or config_resource.get("type") != resource_type
            ):
                global_blockers.add("data_source_configuration_mismatch")
            elif not isinstance(provider, dict) or provider.get("alias") is not None:
                global_blockers.add("data_source_provider_binding_mismatch")
            resources.append(
                {
                    "actions": details.get("actions"),
                    "address": address,
                    "classification": classification,
                    "mode": mode,
                    "risk_codes": [],
                    "type": resource_type,
                }
            )
            continue
        if mode != "managed":
            global_blockers.add("unsupported_resource_mode")
            continue
        managed_addresses.append(address)

        config_address = base_configuration_address(address)
        config_resource = config_resources.get(config_address)
        if (
            not isinstance(config_resource, dict)
            or config_resource.get("mode", "managed") != "managed"
            or config_resource.get("type") != resource_type
        ):
            global_blockers.add("resource_configuration_mismatch")
        else:
            configuration = plan.get("configuration", {})
            providers = configuration.get("provider_config", {}) if isinstance(configuration, dict) else {}
            provider = providers.get(config_resource.get("provider_config_key")) if isinstance(providers, dict) else None
            expected_alias = (
                "target"
                if stack == "bootstrap" and address == "oci_artifacts_container_repository.api"
                else None
            )
            if not isinstance(provider, dict) or provider.get("alias") != expected_alias:
                global_blockers.add("resource_provider_binding_mismatch")

        effective_values = details.get("before") if classification == "delete" else details.get("after")
        values = effective_values if isinstance(effective_values, dict) else {}
        planned_managed_values[address] = values
        planned_classifications[address] = classification
        global_blockers.update(
            resource_scope_blockers(address, resource_type, values, stack, tenancy, compartment)
        )
        risks, blockers = plan_resource_risks(
            address,
            resource_type,
            values,
            details.get("after_unknown", {}),
            stack,
            classification,
            compartment,
            variables,
            config_resources,
        )
        global_risks.update(risks)
        global_blockers.update(blockers)
        if resource_type in COST_DRIVERS and classification != "delete":
            cost_drivers.add(COST_DRIVERS[resource_type])
        if contains_sensitive_marker(details.get("after_sensitive", {})):
            sensitive_addresses.add(address)
        resources.append(
            {
                "actions": details.get("actions"),
                "address": address,
                "classification": classification,
                "mode": mode,
                "risk_codes": risks,
                "type": resource_type,
            }
        )

    if len(managed_addresses) != len(set(managed_addresses)):
        global_blockers.add("duplicate_managed_resource_address")
    if expected_addresses is not None and set(managed_addresses) != expected_addresses:
        global_blockers.add("incomplete_or_unexpected_resource_set")
    global_blockers.update(
        plan_relationship_blockers(
            stack,
            planned_managed_values,
            planned_data_values,
            planned_classifications,
            variables,
        )
    )

    output_changes = plan.get("output_changes", {})
    if not isinstance(output_changes, dict):
        raise ContractError("output_changes must be an object")
    outputs: List[Dict[str, Any]] = []
    for name, raw in sorted(output_changes.items()):
        details = require_object(raw, "output change")
        output_actions = details.get("actions", [])
        action_class(output_actions)
        sensitive = details.get("after_sensitive", False)
        if not isinstance(sensitive, bool):
            raise ContractError("output change contains a malformed sensitivity marker")
        if name not in RECEIPT_OUTPUT_KEYS[stack]:
            global_blockers.add("unexpected_output_name")
        if sensitive:
            global_blockers.add("sensitive_output")
        outputs.append(
            {
                "actions": output_actions,
                "name": name,
                "sensitive": sensitive,
            }
        )
    if set(output_changes) != RECEIPT_OUTPUT_KEYS[stack]:
        global_blockers.add("incomplete_or_unexpected_output_set")

    destructive = counts["delete"] + counts["replace_create_first"] + counts["replace_delete_first"]
    saved_hash = saved_plan_hash or sha256_file(saved_plan_path)
    if not HASH_RE.fullmatch(saved_hash):
        raise ContractError("saved plan hash is malformed")
    target_fingerprint = fingerprint(
        principal, tenancy, region, compartment, home_region, oci_profile
    )
    drift = plan.get("resource_drift", [])
    if not isinstance(drift, list):
        raise ContractError("resource_drift must be an array when present")

    plan_json_hash = (
        sha256_file(plan_json_source)
        if isinstance(plan_json_source, Path)
        else str(plan_json_source)
    )
    if not HASH_RE.fullmatch(plan_json_hash):
        raise ContractError("plan JSON hash is malformed")
    iac_source_hash, iac_source_manifest = source_evidence or saved_plan_source_evidence(
        saved_plan_path, stack, saved_hash
    )
    blocked = bool(global_blockers)
    approval_suffix = f" {bootstrap_receipt_hash[:16]}" if bootstrap_receipt_hash else ""
    approval = (
        f"APPLY {stack.upper()} {target_fingerprint} {saved_hash[:16]} {plan_json_hash[:16]} "
        f"{iac_source_hash[:16]}{approval_suffix}"
        if not blocked
        else None
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "artifact": "terraform-plan-summary",
        "generated_at": iso_now(),
        "stack": stack,
        "terraform_version": plan.get("terraform_version"),
        "format_version": format_version,
        "target": {
            "compartment": compartment,
            "fingerprint": target_fingerprint,
            "home_region": home_region,
            "oci_profile": oci_profile,
            "principal": principal,
            "region": region,
            "tenancy": tenancy,
        },
        "saved_plan_sha256": saved_hash,
        "plan_json_sha256": plan_json_hash,
        "iac_source_sha256": iac_source_hash,
        "iac_source_manifest": iac_source_manifest,
        "bootstrap_receipt_sha256": bootstrap_receipt_hash,
        "approval_phrase": approval,
        "change_counts": counts,
        "requires_destructive_review": destructive > 0,
        "drift_count": len(drift),
        "resources": sorted(resources, key=lambda item: item["address"]),
        "outputs": outputs,
        "sensitive_change_addresses": sorted(sensitive_addresses),
        "risk_codes": sorted(global_risks),
        "cost_drivers": sorted(cost_drivers),
        "blocked": blocked,
        "block_reasons": sorted(global_blockers),
    }


def command_plan_summary(args: argparse.Namespace) -> int:
    saved_path = Path(args.saved_plan)
    plan, plan_json_hash, saved_plan_hash = decode_saved_plan(saved_path, args.terraform_bin)
    bootstrap_receipt_hash: Optional[str] = None
    if args.stack == "runtime":
        if not args.bootstrap_receipt:
            raise ContractError("runtime plan summary requires the reviewed bootstrap receipt")
        container_image_url: Optional[str] = None
        for resource_change in plan.get("resource_changes", []):
            if (
                isinstance(resource_change, dict)
                and resource_change.get("type") == "oci_container_instances_container_instance"
            ):
                change = resource_change.get("change", {})
                after = change.get("after", {}) if isinstance(change, dict) else {}
                containers = after.get("containers", []) if isinstance(after, dict) else []
                if isinstance(containers, list) and containers and isinstance(containers[0], dict):
                    container_image_url = containers[0].get("image_url")
        if not isinstance(container_image_url, str):
            raise ContractError("runtime plan does not expose the immutable container image")
        bootstrap_receipt_hash = validate_bootstrap_lineage(
            Path(args.bootstrap_receipt),
            {
                "tenancy": args.tenancy,
                "region": args.region,
                "compartment": args.compartment,
                "oci_profile": args.oci_profile,
            },
            container_image_url,
        )
    summary = build_plan_summary(
        plan,
        plan_json_hash,
        saved_path,
        args.stack,
        args.principal,
        args.tenancy,
        args.region,
        args.compartment,
        saved_plan_hash,
        bootstrap_receipt_hash,
        args.home_region,
        args.oci_profile,
    )
    write_private_json(Path(args.out), summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 2 if summary["blocked"] else 0


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> None:
        raise urllib.error.HTTPError(req.full_url, code, "redirect refused", headers, fp)


def smoke_once(url: str, timeout: float, request_id: str) -> Tuple[int, bytes, bool]:
    opener = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=ssl.create_default_context()),
        NoRedirect(),
    )
    request = urllib.request.Request(
        url,
        method="GET",
        headers={"accept": "application/json", "x-request-id": request_id},
    )
    with opener.open(request, timeout=timeout) as response:
        body = response.read(MAX_HTTP_BODY_BYTES + 1)
        if len(body) > MAX_HTTP_BODY_BYTES:
            raise ContractError("health response exceeded the size limit")
        return int(response.status), body, response.headers.get_content_type() == "application/json"


def command_smoke(args: argparse.Namespace) -> int:
    parsed = urlsplit(args.url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ContractError("smoke URL must be HTTPS, contain a host, and contain no user information")
    if parsed.query or parsed.fragment:
        raise ContractError("smoke URL must not contain query data or a fragment")
    if not parsed.path.endswith("/healthz"):
        raise ContractError("smoke URL must target the /healthz contract")
    if args.attempts < 1 or args.attempts > 5:
        raise ContractError("attempts must be between 1 and 5")
    if args.timeout < 0.1 or args.timeout > 30:
        raise ContractError("timeout must be between 0.1 and 30 seconds")

    request_id = str(uuid.uuid4())
    passed = False
    final_status: Optional[int] = None
    body_length = 0
    body_hash: Optional[str] = None
    failure_code: Optional[str] = None
    content_type_ok = False
    attempts_used = 0
    for attempt in range(1, args.attempts + 1):
        attempts_used = attempt
        try:
            status, body, content_type_ok = smoke_once(args.url, args.timeout, request_id)
            final_status = status
            body_length = len(body)
            body_hash = hashlib.sha256(body).hexdigest()
            payload = json.loads(body.decode("utf-8"))
            passed = (
                status == 200
                and content_type_ok
                and payload == {"status": "ok"}
                and body == EXPECTED_HEALTH_BODY
            )
            failure_code = None if passed else "health_contract_mismatch"
        except urllib.error.HTTPError as exc:
            final_status = int(exc.code)
            failure_code = "http_error_or_redirect"
        except (urllib.error.URLError, TimeoutError):
            failure_code = "network_or_tls_error"
        except (UnicodeDecodeError, json.JSONDecodeError):
            failure_code = "invalid_json_response"
        if passed:
            break
        if attempt < args.attempts:
            time.sleep(min(attempt, 2))

    result = {
        "schema_version": SCHEMA_VERSION,
        "artifact": "smoke-result",
        "generated_at": iso_now(),
        "status": "verified" if passed else "failed",
        "request_id": request_id,
        "url_sha256": hashlib.sha256(args.url.encode("utf-8")).hexdigest(),
        "attempts": attempts_used,
        "http_status": final_status,
        "body_length": body_length,
        "body_sha256": body_hash,
        "assertions": {
            "https": True,
            "redirects_refused": True,
            "status_200": final_status == 200,
            "exact_health_shape": passed,
            "bounded_body": body_length <= MAX_HTTP_BODY_BYTES,
            "application_json": content_type_ok,
        },
        "failure_code": failure_code,
    }
    write_private_json(Path(args.out), result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if passed else 2


def read_state_inventory(path: Path, allow_empty: bool = False) -> Tuple[List[str], List[str]]:
    addresses = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not addresses and not allow_empty:
        raise ContractError("state address list is empty")
    if len(addresses) != len(set(addresses)):
        raise ContractError("state address list contains duplicates")
    if any(any(char.isspace() for char in address) for address in addresses):
        raise ContractError("state address list contains malformed whitespace")
    data_addresses = sorted(address for address in addresses if address.startswith("data."))
    managed_addresses = sorted(address for address in addresses if not address.startswith("data."))
    if not managed_addresses and not allow_empty:
        raise ContractError("managed state address list is empty")
    return managed_addresses, data_addresses


def state_snapshot_evidence(
    state: Mapping[str, Any],
    layer: str,
    tenancy: str,
    compartment: str,
    allow_empty: bool = False,
) -> Tuple[Dict[str, Any], List[str], List[str], Dict[str, str]]:
    format_version = state.get("format_version")
    if not isinstance(format_version, str) or format_version.split(".", 1)[0] != "1":
        raise ContractError("unsupported Terraform state JSON format major version")
    if state.get("terraform_version") != TERRAFORM_VERSION:
        raise ContractError(f"state snapshot must be rendered by Terraform {TERRAFORM_VERSION}")
    values = require_object(state.get("values"), "Terraform state values")
    root_module = require_object(values.get("root_module", {}), "Terraform state root module")
    if root_module.get("child_modules"):
        raise ContractError("state snapshot must not contain child modules")
    resources = root_module.get("resources", [])
    if not isinstance(resources, list):
        raise ContractError("Terraform state resources must be an array")
    managed: List[str] = []
    data: List[str] = []
    resource_ids: Dict[str, str] = {}
    resource_values: Dict[str, Dict[str, Any]] = {}
    for raw in resources:
        resource = require_object(raw, "Terraform state resource")
        address = resource.get("address")
        mode = resource.get("mode", "managed")
        resource_type = resource.get("type")
        resource_value = resource.get("values")
        if not isinstance(address, str) or not isinstance(resource_type, str) or not isinstance(resource_value, dict):
            raise ContractError("Terraform state contains a malformed resource")
        if mode == "data":
            expected_data_type = expected_address_type(layer, address, "data")
            if expected_data_type is None or expected_data_type != resource_type:
                raise ContractError("Terraform state contains an unexpected data source")
            data.append(address)
            continue
        if mode != "managed" or expected_address_type(layer, address, "managed") != resource_type:
            raise ContractError("Terraform state contains a managed resource outside the blueprint contract")
        identifier = resource_value.get("id")
        if not isinstance(identifier, str) or not OCID_RE.match(identifier):
            raise ContractError("Terraform state managed resource lacks an OCI identifier")
        scope_blockers = resource_scope_blockers(
            address, resource_type, resource_value, layer, tenancy, compartment
        )
        if scope_blockers:
            raise ContractError("Terraform state resource scope does not match the receipt target")
        managed.append(address)
        resource_ids[address] = identifier
        resource_values[address] = resource_value
    if len(managed) != len(set(managed)) or len(data) != len(set(data)):
        raise ContractError("Terraform state contains duplicate resource addresses")
    if not managed:
        if not allow_empty:
            raise ContractError("Terraform state contains no managed resources")
        if data:
            raise ContractError("empty post-destroy state must not retain data sources")
        return {}, [], [], {}

    raw_outputs = values.get("outputs")
    outputs = extract_outputs(raw_outputs, layer)
    validate_managed_state_addresses(managed, layer, outputs.get("gateway_endpoint_type"))

    output_address_map = {
        "bootstrap": {
            "repository_id": "oci_artifacts_container_repository.api",
            "dynamic_group_id": "oci_identity_dynamic_group.container_instances",
            "image_pull_policy_id": "oci_identity_policy.container_instances_pull",
            "budget_id": "oci_budget_budget.sandbox",
            "budget_alert_rule_id": "oci_budget_alert_rule.actual",
        },
        "runtime": {
            "container_instance_id": "oci_container_instances_container_instance.api",
            "gateway_id": "oci_apigateway_gateway.api",
            "deployment_id": "oci_apigateway_deployment.api",
            "log_group_id": "oci_logging_log_group.api",
            "gateway_access_log_id": "oci_logging_log.gateway_access",
            "gateway_execution_log_id": "oci_logging_log.gateway_execution",
            "notification_topic_id": "oci_ons_notification_topic.alarms",
            "notification_subscription_id": "oci_ons_subscription.email",
            "cpu_alarm_id": "oci_monitoring_alarm.high_cpu",
            "memory_alarm_id": "oci_monitoring_alarm.high_memory",
        },
    }
    for output_name, address in output_address_map[layer].items():
        if outputs.get(output_name) != resource_ids.get(address):
            raise ContractError("Terraform state output does not match its managed resource identifier")

    if layer == "bootstrap":
        repository_values = resource_values["oci_artifacts_container_repository.api"]
        namespace = repository_values.get("namespace")
        display_name = repository_values.get("display_name")
        repository_path = outputs["repository_path"]
        if (
            not isinstance(namespace, str)
            or not namespace
            or "/" in namespace
            or not isinstance(display_name, str)
            or not display_name
            or not repository_path.endswith(f"/{namespace}/{display_name}")
        ):
            raise ContractError("bootstrap repository_path does not derive from repository state")
    else:
        container_values = resource_values["oci_container_instances_container_instance.api"]
        containers = container_values.get("containers")
        vnics = container_values.get("vnics")
        if (
            not isinstance(containers, list)
            or len(containers) != 1
            or not isinstance(containers[0], dict)
            or containers[0].get("image_url") != outputs["container_image_url"]
            or containers[0].get("container_id") != outputs["container_id"]
            or not isinstance(vnics, list)
            or len(vnics) != 1
            or not isinstance(vnics[0], dict)
            or vnics[0].get("vnic_id") != outputs["container_vnic_id"]
        ):
            raise ContractError("runtime outputs do not match the Container Instance state")
        gateway_values = resource_values["oci_apigateway_gateway.api"]
        deployment_values = resource_values["oci_apigateway_deployment.api"]
        hostname = gateway_values.get("hostname")
        path_prefix = deployment_values.get("path_prefix")
        if (
            gateway_values.get("endpoint_type") != outputs["gateway_endpoint_type"]
            or not isinstance(hostname, str)
            or not isinstance(path_prefix, str)
            or outputs["endpoint"] != f"https://{hostname}{path_prefix}"
            or outputs["healthcheck_url"] != f"https://{hostname}{path_prefix}/healthz"
        ):
            raise ContractError("runtime endpoint outputs do not derive from the gateway state")
        subscription_values = resource_values["oci_ons_subscription.email"]
        if subscription_values.get("state") != outputs["notification_subscription_state"]:
            raise ContractError("notification subscription output does not match Terraform state")
    return outputs, sorted(managed), sorted(data), dict(sorted(resource_ids.items()))


def state_resource_values(state: Mapping[str, Any], address: str) -> Dict[str, Any]:
    values = require_object(state.get("values"), "Terraform state values")
    root_module = require_object(values.get("root_module", {}), "Terraform state root module")
    resources = root_module.get("resources", [])
    if not isinstance(resources, list):
        raise ContractError("Terraform state resources must be an array")
    matches = [
        resource.get("values")
        for resource in resources
        if isinstance(resource, dict)
        and resource.get("mode", "managed") == "managed"
        and resource.get("address") == address
    ]
    if len(matches) != 1 or not isinstance(matches[0], dict):
        raise ContractError("Terraform state is missing a required managed resource")
    return matches[0]


def validate_state_security_contract(
    state: Mapping[str, Any],
    plan: Mapping[str, Any],
    layer: str,
    tenancy: str,
    region: str,
    compartment: str,
    home_region: Optional[str],
    oci_profile: str = "DEFAULT",
) -> None:
    variables, config_resources, binding_blockers = target_binding_blockers(
        plan, layer, tenancy, region, compartment, home_region, oci_profile
    )
    if binding_blockers:
        raise ContractError("saved plan target/configuration contract is not valid for state verification")
    values = require_object(state.get("values"), "Terraform state values")
    root_module = require_object(values.get("root_module", {}), "Terraform state root module")
    resources = root_module.get("resources", [])
    if not isinstance(resources, list):
        raise ContractError("Terraform state resources must be an array")
    managed_values: Dict[str, Dict[str, Any]] = {}
    data_values: Dict[str, Dict[str, Any]] = {}
    for raw in resources:
        resource = require_object(raw, "Terraform state resource")
        mode = resource.get("mode", "managed")
        address = resource.get("address")
        resource_values = resource.get("values")
        if mode == "data":
            if isinstance(address, str) and isinstance(resource_values, dict):
                data_values[address] = resource_values
            continue
        if mode != "managed":
            continue
        resource_type = resource.get("type")
        if not isinstance(address, str) or not isinstance(resource_type, str) or not isinstance(resource_values, dict):
            raise ContractError("Terraform state contains a malformed managed resource")
        managed_values[address] = resource_values
        _risks, blockers = plan_resource_risks(
            address,
            resource_type,
            resource_values,
            {},
            layer,
            "no_op",
            compartment,
            variables,
            config_resources,
        )
        if blockers:
            raise ContractError("applied state violates the reviewed security contract")

    if layer == "bootstrap":
        alert = managed_values.get("oci_budget_alert_rule.actual", {})
        budget = managed_values.get("oci_budget_budget.sandbox", {})
        if alert.get("budget_id") != budget.get("id"):
            raise ContractError("applied state violates the reviewed resource relationship contract")
        return

    identifiers = {
        address: values.get("id") for address, values in managed_values.items()
    }
    vcn_id = identifiers.get("oci_core_vcn.sandbox")
    gateway_nsg_id = identifiers.get("oci_core_network_security_group.gateway")
    app_nsg_id = identifiers.get("oci_core_network_security_group.app")
    gateway_subnet_id = identifiers.get("oci_core_subnet.gateway")
    app_subnet_id = identifiers.get("oci_core_subnet.app")
    gateway_route_id = identifiers.get("oci_core_route_table.gateway")
    app_route_id = identifiers.get("oci_core_route_table.app")
    empty_security_list_id = identifiers.get("oci_core_security_list.empty")
    service_gateway_id = identifiers.get("oci_core_service_gateway.oracle_services")
    gateway_id = identifiers.get("oci_apigateway_gateway.api")

    relationship_valid = all(isinstance(identifier, str) for identifier in identifiers.values())
    gateway = managed_values.get("oci_apigateway_gateway.api", {})
    relationship_valid = relationship_valid and (
        gateway.get("network_security_group_ids") == [gateway_nsg_id]
        and gateway.get("subnet_id") == gateway_subnet_id
    )

    for address in (
        "oci_core_internet_gateway.public[0]",
        "oci_core_service_gateway.oracle_services",
        "oci_core_route_table.gateway",
        "oci_core_route_table.app",
        "oci_core_security_list.empty",
        "oci_core_subnet.gateway",
        "oci_core_subnet.app",
        "oci_core_network_security_group.gateway",
        "oci_core_network_security_group.app",
    ):
        if address in managed_values:
            relationship_valid = relationship_valid and managed_values[address].get("vcn_id") == vcn_id

    gateway_subnet = managed_values.get("oci_core_subnet.gateway", {})
    app_subnet = managed_values.get("oci_core_subnet.app", {})
    relationship_valid = relationship_valid and (
        gateway_subnet.get("route_table_id") == gateway_route_id
        and gateway_subnet.get("security_list_ids") == [empty_security_list_id]
        and app_subnet.get("route_table_id") == app_route_id
        and app_subnet.get("security_list_ids") == [empty_security_list_id]
    )

    oracle_services = data_values.get("data.oci_core_services.oracle_services", {}).get("services")
    if (
        not isinstance(oracle_services, list)
        or len(oracle_services) != 1
        or not isinstance(oracle_services[0], dict)
        or not isinstance(oracle_services[0].get("id"), str)
        or not isinstance(oracle_services[0].get("cidr_block"), str)
    ):
        relationship_valid = False
        oracle_service_id = None
        oracle_service_cidr = None
    else:
        oracle_service_id = oracle_services[0]["id"]
        oracle_service_cidr = oracle_services[0]["cidr_block"]

    service_gateway = managed_values.get("oci_core_service_gateway.oracle_services", {})
    service_bindings = service_gateway.get("services")
    relationship_valid = relationship_valid and (
        isinstance(service_bindings, list)
        and len(service_bindings) == 1
        and isinstance(service_bindings[0], dict)
        and service_bindings[0].get("service_id") == oracle_service_id
    )

    app_routes = managed_values.get("oci_core_route_table.app", {}).get("route_rules")
    relationship_valid = relationship_valid and (
        isinstance(app_routes, list)
        and len(app_routes) == 1
        and isinstance(app_routes[0], dict)
        and app_routes[0].get("network_entity_id") == service_gateway_id
        and app_routes[0].get("destination") == oracle_service_cidr
    )
    gateway_routes = managed_values.get("oci_core_route_table.gateway", {}).get("route_rules")
    if variables.get("gateway_endpoint_type") == "PUBLIC":
        relationship_valid = relationship_valid and (
            isinstance(gateway_routes, list)
            and len(gateway_routes) == 1
            and isinstance(gateway_routes[0], dict)
            and gateway_routes[0].get("network_entity_id")
            == identifiers.get("oci_core_internet_gateway.public[0]")
        )
    else:
        relationship_valid = relationship_valid and gateway_routes in (None, [])

    for address, values in managed_values.items():
        if not GATEWAY_INGRESS_ADDRESS_RE.fullmatch(address) and not address.startswith(
            "oci_core_network_security_group_security_rule."
        ):
            continue
        owner_id = (
            gateway_nsg_id
            if GATEWAY_INGRESS_ADDRESS_RE.fullmatch(address) or address.endswith("gateway_to_app")
            else app_nsg_id
        )
        relationship_valid = relationship_valid and values.get("network_security_group_id") == owner_id
        if address.endswith("gateway_to_app"):
            relationship_valid = relationship_valid and values.get("destination") == app_nsg_id
        elif address.endswith("app_from_gateway"):
            relationship_valid = relationship_valid and values.get("source") == gateway_nsg_id
        elif address.endswith("app_to_oracle_services"):
            relationship_valid = relationship_valid and values.get("destination") == oracle_service_cidr

    container = managed_values.get("oci_container_instances_container_instance.api", {})
    vnics = container.get("vnics")
    relationship_valid = relationship_valid and (
        isinstance(vnics, list)
        and len(vnics) == 1
        and isinstance(vnics[0], dict)
        and vnics[0].get("subnet_id") == app_subnet_id
        and vnics[0].get("nsg_ids") == [app_nsg_id]
    )
    deployment = managed_values.get("oci_apigateway_deployment.api", {})
    relationship_valid = relationship_valid and deployment.get("gateway_id") == gateway_id
    log_group_id = identifiers.get("oci_logging_log_group.api")
    deployment_id = identifiers.get("oci_apigateway_deployment.api")
    for address, category in (
        ("oci_logging_log.gateway_access", "access"),
        ("oci_logging_log.gateway_execution", "execution"),
    ):
        log_values = managed_values.get(address, {})
        configurations = log_values.get("configuration")
        source = None
        if (
            isinstance(configurations, list)
            and len(configurations) == 1
            and isinstance(configurations[0], dict)
        ):
            sources = configurations[0].get("source")
            if isinstance(sources, list) and len(sources) == 1 and isinstance(sources[0], dict):
                source = sources[0]
        relationship_valid = relationship_valid and (
            log_values.get("log_group_id") == log_group_id
            and log_values.get("log_type") == "SERVICE"
            and log_values.get("is_enabled") is True
            and log_values.get("retention_duration") == 30
            and source is not None
            and source.get("category") == category
            and source.get("resource") == deployment_id
            and source.get("service")
            == variables.get("api_gateway_logging_service_name", "apigateway")
            and source.get("source_type") == "OCISERVICE"
        )

    topic_id = identifiers.get("oci_ons_notification_topic.alarms")
    subscription = managed_values.get("oci_ons_subscription.email", {})
    relationship_valid = relationship_valid and (
        subscription.get("topic_id") == topic_id
        and subscription.get("protocol") == "EMAIL"
        and subscription.get("endpoint") == variables.get("notification_email")
    )

    container_instance_id = identifiers.get(
        "oci_container_instances_container_instance.api"
    )
    for address, metric, threshold in (
        (
            "oci_monitoring_alarm.high_cpu",
            "CpuUtilization",
            variables.get("cpu_alarm_threshold", 80),
        ),
        (
            "oci_monitoring_alarm.high_memory",
            "MemoryUtilization",
            variables.get("memory_alarm_threshold", 85),
        ),
    ):
        alarm = managed_values.get(address, {})
        expected_query = (
            f'{metric}[1m]{{resourceId = "{container_instance_id}"}}.mean() > '
            f'{terraform_number_text(threshold)}'
        )
        relationship_valid = relationship_valid and (
            alarm.get("destinations") == [topic_id]
            and alarm.get("query") == expected_query
            and alarm.get("namespace") == "oci_computecontainerinstance"
            and alarm.get("severity") == "WARNING"
            and alarm.get("is_enabled") is True
            and alarm.get("pending_duration") == "PT5M"
        )
    if not relationship_valid:
        raise ContractError("applied state violates the reviewed resource relationship contract")


def validate_managed_state_addresses(addresses: Sequence[str], layer: str, gateway_endpoint_type: Optional[str] = None) -> None:
    unknown = sorted(address for address in addresses if expected_address_type(layer, address, "managed") is None)
    if unknown:
        raise ContractError("managed state contains an address outside the blueprint contract")
    required = set(BOOTSTRAP_ADDRESS_TYPES if layer == "bootstrap" else RUNTIME_ADDRESS_TYPES)
    if layer == "runtime":
        required.discard("oci_core_internet_gateway.public[0]")
        ingress = [address for address in addresses if GATEWAY_INGRESS_ADDRESS_RE.fullmatch(address)]
        if not ingress:
            raise ContractError("runtime state is missing the explicit gateway ingress rule")
        has_internet_gateway = "oci_core_internet_gateway.public[0]" in addresses
        if (gateway_endpoint_type == "PUBLIC") != has_internet_gateway:
            raise ContractError("runtime state internet gateway does not match gateway_endpoint_type")
    missing = sorted(required - set(addresses))
    if missing:
        raise ContractError("managed state is incomplete for the blueprint contract")


def validate_https_output_url(raw: str, health: bool = False) -> None:
    parsed = urlsplit(raw)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ContractError("runtime endpoint outputs must be HTTPS URLs without user information")
    if parsed.query or parsed.fragment:
        raise ContractError("runtime endpoint outputs must not contain query data or fragments")
    if health and not parsed.path.endswith("/healthz"):
        raise ContractError("healthcheck_url must target /healthz")


def extract_outputs(raw: Any, layer: str) -> Dict[str, Any]:
    outputs = require_object(raw, "Terraform outputs")
    expected = RECEIPT_OUTPUT_KEYS[layer]
    missing = sorted(expected - set(outputs))
    unknown = sorted(set(outputs) - expected)
    if missing:
        raise ContractError(f"Terraform outputs are missing receipt fields: {', '.join(missing)}")
    if unknown:
        raise ContractError(f"Terraform outputs contain fields outside the receipt allowlist: {', '.join(unknown)}")
    values: Dict[str, Any] = {}
    for name in sorted(expected):
        entry = require_object(outputs[name], f"output {name}")
        if entry.get("sensitive") is True:
            raise ContractError(f"receipt refuses sensitive output {name}")
        value = entry.get("value")
        if not isinstance(value, str) or not value:
            raise ContractError(f"receipt output {name} must be a non-empty string")
        if name.endswith("_id") and not OCID_RE.match(value):
            raise ContractError(f"receipt output {name} must be an OCI resource identifier")
        values[name] = value
    if layer == "runtime":
        if not IMAGE_DIGEST_RE.search(values["container_image_url"]):
            raise ContractError("runtime receipt requires an immutable image digest")
        if values["notification_subscription_state"] != "ACTIVE":
            raise ContractError("notification subscription must be ACTIVE before a locally verified receipt")
        if values["gateway_endpoint_type"] not in ("PUBLIC", "PRIVATE"):
            raise ContractError("runtime receipt contains an unsupported gateway endpoint type")
        validate_https_output_url(values["endpoint"])
        validate_https_output_url(values["healthcheck_url"], health=True)
    else:
        repository_path = values["repository_path"]
        if "://" in repository_path or "@" in repository_path or not re.fullmatch(
            r"[A-Za-z0-9.-]+/[A-Za-z0-9._/-]+", repository_path
        ):
            raise ContractError("bootstrap receipt contains an invalid repository_path")
    return values


def validate_bootstrap_lineage(
    receipt_path: Path, target: Mapping[str, Any], container_image_url: str
) -> str:
    bootstrap = require_object(load_json(receipt_path), "bootstrap receipt")
    if (
        bootstrap.get("schema_version") != SCHEMA_VERSION
        or bootstrap.get("artifact") != "deployment-receipt"
        or bootstrap.get("status") != "locally_verified"
        or bootstrap.get("layer") != "bootstrap"
        or bootstrap.get("blueprint_version") != BLUEPRINT_VERSION
        or bootstrap.get("environment_class") != "sandbox"
    ):
        raise ContractError("runtime flow requires a locally verified bootstrap receipt")
    bootstrap_target = require_object(bootstrap.get("target"), "bootstrap receipt target")
    validate_target(
        bootstrap_target.get("principal"),
        bootstrap_target.get("tenancy"),
        bootstrap_target.get("region"),
        bootstrap_target.get("compartment"),
        bootstrap_target.get("home_region"),
        bootstrap_target.get("oci_profile"),
    )
    if bootstrap_target.get("fingerprint") != fingerprint(
        bootstrap_target["principal"],
        bootstrap_target["tenancy"],
        bootstrap_target["region"],
        bootstrap_target["compartment"],
        bootstrap_target.get("home_region"),
        bootstrap_target["oci_profile"],
    ):
        raise ContractError("bootstrap receipt target fingerprint is invalid")
    if any(
        bootstrap_target.get(field) != target.get(field)
        for field in ("tenancy", "region", "compartment", "oci_profile")
    ):
        raise ContractError("runtime and bootstrap receipts target different OCI scopes")
    bootstrap_outputs = require_object(bootstrap.get("outputs"), "bootstrap receipt outputs")
    bootstrap_state = require_object(bootstrap.get("state"), "bootstrap receipt state evidence")
    bootstrap_ids = require_object(
        bootstrap_state.get("resource_ids"), "bootstrap receipt resource identifiers"
    )
    bootstrap_addresses = bootstrap.get("state_addresses")
    if not isinstance(bootstrap_addresses, list) or set(bootstrap_addresses) != set(BOOTSTRAP_ADDRESS_TYPES):
        raise ContractError("bootstrap receipt state address contract is incomplete")
    if (
        not isinstance(bootstrap_state.get("lineage"), str)
        or not isinstance(bootstrap_state.get("serial"), int)
        or not HASH_RE.fullmatch(str(bootstrap_state.get("snapshot_sha256", "")))
        or set(bootstrap_ids) != set(BOOTSTRAP_ADDRESS_TYPES)
    ):
        raise ContractError("bootstrap receipt state evidence is incomplete")
    bootstrap_output_ids = {
        "repository_id": "oci_artifacts_container_repository.api",
        "dynamic_group_id": "oci_identity_dynamic_group.container_instances",
        "image_pull_policy_id": "oci_identity_policy.container_instances_pull",
        "budget_id": "oci_budget_budget.sandbox",
        "budget_alert_rule_id": "oci_budget_alert_rule.actual",
    }
    if any(bootstrap_outputs.get(name) != bootstrap_ids.get(address) for name, address in bootstrap_output_ids.items()):
        raise ContractError("bootstrap receipt outputs do not match its state evidence")
    repository_path = bootstrap_outputs.get("repository_path")
    repository_contract = require_object(
        bootstrap.get("repository_contract"), "bootstrap receipt repository contract"
    )
    if set(repository_contract) != {"registry_endpoint", "namespace", "display_name"}:
        raise ContractError("bootstrap receipt repository contract is malformed")
    if (
        not isinstance(repository_contract.get("registry_endpoint"), str)
        or not re.fullmatch(r"[A-Za-z0-9.-]+", repository_contract["registry_endpoint"])
        or not isinstance(repository_contract.get("namespace"), str)
        or not re.fullmatch(r"[A-Za-z0-9_-]+", repository_contract["namespace"])
        or not isinstance(repository_contract.get("display_name"), str)
        or not re.fullmatch(r"[a-z0-9][a-z0-9._/-]{1,254}", repository_contract["display_name"])
    ):
        raise ContractError("bootstrap receipt repository contract contains invalid components")
    expected_repository_path = (
        f"{repository_contract.get('registry_endpoint')}/"
        f"{repository_contract.get('namespace')}/"
        f"{repository_contract.get('display_name')}"
    )
    if not isinstance(repository_path, str) or not container_image_url.startswith(f"{repository_path}@sha256:"):
        raise ContractError("runtime image does not belong to the repository approved by bootstrap")
    if repository_path != expected_repository_path:
        raise ContractError("bootstrap receipt repository path is not derivable from its contract")
    return sha256_file(receipt_path)


def command_receipt(args: argparse.Namespace) -> int:
    summary = require_object(load_json(Path(args.summary)), "plan summary")
    if summary.get("artifact") != "terraform-plan-summary" or summary.get("schema_version") != SCHEMA_VERSION:
        raise ContractError("unsupported plan summary contract")
    if summary.get("stack") != args.layer:
        raise ContractError("receipt layer does not match the plan summary stack")
    if summary.get("blocked") is not False:
        raise ContractError("a blocked plan cannot produce a receipt")
    target = require_object(summary.get("target"), "plan summary target")
    validate_target(
        target.get("principal"),
        target.get("tenancy"),
        target.get("region"),
        target.get("compartment"),
        target.get("home_region"),
        target.get("oci_profile"),
    )
    expected_fingerprint = fingerprint(
        target["principal"],
        target["tenancy"],
        target["region"],
        target["compartment"],
        target.get("home_region"),
        target["oci_profile"],
    )
    if target.get("fingerprint") != expected_fingerprint:
        raise ContractError("plan summary target fingerprint is invalid")
    summary_time = parse_rfc3339_utc(summary.get("generated_at"), "plan summary generated_at")
    state, state_sha256, state_lineage, state_serial = decode_saved_state(
        Path(args.state), args.terraform_bin
    )
    outputs, addresses, data_addresses, resource_ids = state_snapshot_evidence(
        state,
        args.layer,
        target["tenancy"],
        target["compartment"],
    )
    bootstrap_receipt_hash: Optional[str] = None
    if args.layer == "runtime":
        if not args.bootstrap_receipt:
            raise ContractError("runtime receipt requires the reviewed bootstrap receipt")
        bootstrap_receipt_hash = validate_bootstrap_lineage(
            Path(args.bootstrap_receipt), target, outputs["container_image_url"]
        )
    if summary.get("bootstrap_receipt_sha256") != bootstrap_receipt_hash:
        raise ContractError("plan summary bootstrap lineage does not match the receipt input")
    plan, plan_json_hash, saved_plan_hash = decode_saved_plan(Path(args.saved_plan), args.terraform_bin)
    if summary.get("saved_plan_sha256") != saved_plan_hash or summary.get("plan_json_sha256") != plan_json_hash:
        raise ContractError("plan summary does not match the exact saved plan")
    recomputed = build_plan_summary(
        plan,
        plan_json_hash,
        Path(args.saved_plan),
        args.layer,
        target["principal"],
        target["tenancy"],
        target["region"],
        target["compartment"],
        saved_plan_hash,
        bootstrap_receipt_hash,
        target.get("home_region"),
        target["oci_profile"],
    )
    for field in (
        "approval_phrase",
        "block_reasons",
        "bootstrap_receipt_sha256",
        "blocked",
        "change_counts",
        "cost_drivers",
        "drift_count",
        "iac_source_manifest",
        "iac_source_sha256",
        "outputs",
        "requires_destructive_review",
        "resources",
        "risk_codes",
        "sensitive_change_addresses",
    ):
        if summary.get(field) != recomputed.get(field):
            raise ContractError("plan summary content does not match the decoded saved plan")
    plan_variables = plan_variable_values(plan)
    expected_state_addresses = expected_managed_plan_addresses(args.layer, plan_variables)
    if expected_state_addresses is None or set(addresses) != expected_state_addresses:
        raise ContractError("applied state resource set does not match the reviewed saved plan")
    validate_state_security_contract(
        state,
        plan,
        args.layer,
        target["tenancy"],
        target["region"],
        target["compartment"],
        target.get("home_region"),
        target["oci_profile"],
    )
    repository_contract: Optional[Dict[str, str]] = None
    if args.layer == "bootstrap":
        repository = state_resource_values(
            state, "oci_artifacts_container_repository.api"
        )
        registry_endpoint = plan_variables.get("ocir_registry_endpoint")
        namespace = repository.get("namespace")
        display_name = repository.get("display_name")
        if (
            not isinstance(registry_endpoint, str)
            or not re.fullmatch(r"[A-Za-z0-9.-]+", registry_endpoint)
            or not isinstance(namespace, str)
            or not re.fullmatch(r"[A-Za-z0-9_-]+", namespace)
            or not isinstance(display_name, str)
            or display_name != plan_variables.get("repository_name")
        ):
            raise ContractError("bootstrap repository state does not match the reviewed saved plan")
        expected_repository_path = f"{registry_endpoint}/{namespace}/{display_name}"
        if outputs["repository_path"] != expected_repository_path:
            raise ContractError("bootstrap repository_path does not match the reviewed state and plan")
        repository_contract = {
            "registry_endpoint": registry_endpoint,
            "namespace": namespace,
            "display_name": display_name,
        }
    if args.layer == "runtime":
        if (
            outputs["container_image_url"] != plan_variables.get("container_image_url")
            or outputs["gateway_endpoint_type"] != plan_variables.get("gateway_endpoint_type")
        ):
            raise ContractError("runtime state outputs do not match the reviewed saved plan")
    smoke: Optional[Dict[str, Any]] = None
    if args.layer == "runtime":
        if not args.smoke:
            raise ContractError("runtime receipt requires a smoke result")
        raw_smoke = require_object(load_json(Path(args.smoke)), "smoke result")
        if (
            raw_smoke.get("schema_version") != SCHEMA_VERSION
            or raw_smoke.get("artifact") != "smoke-result"
            or raw_smoke.get("status") != "verified"
        ):
            raise ContractError("runtime receipt requires a verified smoke result")
        smoke_time = parse_rfc3339_utc(raw_smoke.get("generated_at"), "smoke generated_at")
        now = utc_now()
        if smoke_time < summary_time - dt.timedelta(minutes=5) or smoke_time > now + dt.timedelta(minutes=5):
            raise ContractError("smoke timestamp is outside the plan and current-time window")
        if now - smoke_time > dt.timedelta(hours=24):
            raise ContractError("smoke result is older than 24 hours")
        try:
            uuid.UUID(str(raw_smoke.get("request_id")))
        except ValueError:
            raise ContractError("smoke request_id must be a UUID")
        expected_assertions = {
            "https": True,
            "redirects_refused": True,
            "status_200": True,
            "exact_health_shape": True,
            "bounded_body": True,
            "application_json": True,
        }
        if (
            raw_smoke.get("http_status") != 200
            or raw_smoke.get("body_sha256") != EXPECTED_HEALTH_BODY_SHA256
            or raw_smoke.get("body_length") != len(EXPECTED_HEALTH_BODY)
            or raw_smoke.get("assertions") != expected_assertions
            or raw_smoke.get("failure_code") is not None
            or raw_smoke.get("url_sha256")
            != hashlib.sha256(outputs["healthcheck_url"].encode("utf-8")).hexdigest()
        ):
            raise ContractError("smoke result does not match the exact deployed health contract")
        smoke = {
            "request_id": raw_smoke.get("request_id"),
            "attempts": raw_smoke.get("attempts"),
            "http_status": raw_smoke.get("http_status"),
            "body_length": raw_smoke.get("body_length"),
            "body_sha256": raw_smoke.get("body_sha256"),
            "url_sha256": raw_smoke.get("url_sha256"),
            "assertions": raw_smoke.get("assertions"),
            "artifact_sha256": sha256_file(Path(args.smoke)),
        }
    for label, revision in (("source_revision", args.source_revision), ("iac_revision", args.iac_revision)):
        if not REVISION_RE.fullmatch(revision):
            raise ContractError(f"{label} contains unsupported characters")
    previous_image_url = args.previous_image_url
    if previous_image_url is not None and not IMAGE_DIGEST_RE.search(previous_image_url):
        raise ContractError("previous_image_url must be an immutable image reference")
    lock_path = Path(args.provider_lock)
    if lock_path.is_symlink() or not lock_path.is_file():
        raise ContractError("provider lock must be an existing regular file, not a symlink")
    provider_lock_hash = sha256_file(lock_path)
    source_manifest = recomputed.get("iac_source_manifest")
    expected_lock_hashes = [
        entry.get("sha256")
        for entry in source_manifest
        if isinstance(entry, dict) and entry.get("path") == ".terraform.lock.hcl"
    ] if isinstance(source_manifest, list) else []
    if expected_lock_hashes != [provider_lock_hash]:
        raise ContractError("provider lock does not match the reviewed saved plan")
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "artifact": "deployment-receipt",
        "generated_at": iso_now(),
        "status": "locally_verified",
        "environment_class": "sandbox",
        "blueprint_version": BLUEPRINT_VERSION,
        "layer": args.layer,
        "source_revision": args.source_revision,
        "iac_revision": args.iac_revision,
        "provider_lock_sha256": provider_lock_hash,
        "plan": {
            "saved_plan_sha256": summary.get("saved_plan_sha256"),
            "iac_source_sha256": summary.get("iac_source_sha256"),
            "summary_sha256": sha256_file(Path(args.summary)),
        },
        "target": target,
        "outputs": outputs,
        "state_addresses": addresses,
        "observed_data_source_count": len(data_addresses),
        "state": {
            "lineage": state_lineage,
            "serial": state_serial,
            "snapshot_sha256": state_sha256,
            "resource_ids": resource_ids,
        },
        "bootstrap_receipt_sha256": bootstrap_receipt_hash,
        "repository_contract": repository_contract,
        "verification": smoke,
        "rollback": {
            "previous_image_url": previous_image_url,
            "zero_downtime_claim": False,
            "method": "create a fresh runtime plan using the prior locally verified digest",
        }
        if args.layer == "runtime"
        else None,
        "teardown_order": ["runtime", "bootstrap"],
    }
    write_private_json(Path(args.out), receipt)
    print(
        json.dumps(
            {
                "artifact": "deployment-receipt",
                "layer": args.layer,
                "out": str(Path(args.out)),
                "receipt_sha256": sha256_file(Path(args.out)),
                "status": "locally_verified",
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def validate_runtime_destroy_evidence(
    evidence_path: Path,
    runtime_receipt_path: Path,
    runtime_receipt: Mapping[str, Any],
    expected_target_fingerprint: str,
    post_destroy_lineage: str,
    post_destroy_serial: int,
) -> str:
    evidence = require_object(load_json(evidence_path), "runtime destroy readback evidence")
    if (
        evidence.get("schema_version") != SCHEMA_VERSION
        or evidence.get("artifact") != "oci-destroy-readback-evidence"
        or evidence.get("verification_method") != "authenticated-read-only-oci-get"
    ):
        raise ContractError("runtime destroy readback evidence has an unsupported contract")
    generated_at = parse_rfc3339_utc(
        evidence.get("generated_at"), "runtime destroy readback generated_at"
    )
    now = utc_now()
    if generated_at > now + dt.timedelta(minutes=5) or now - generated_at > dt.timedelta(hours=24):
        raise ContractError("runtime destroy readback evidence is outside the 24-hour window")
    if evidence.get("runtime_receipt_sha256") != sha256_file(runtime_receipt_path):
        raise ContractError("runtime destroy readback evidence does not bind the runtime receipt")
    if evidence.get("target_fingerprint") != expected_target_fingerprint:
        raise ContractError("runtime destroy readback evidence targets a different OCI scope")
    if (
        evidence.get("state_lineage") != post_destroy_lineage
        or evidence.get("state_serial") != post_destroy_serial
    ):
        raise ContractError("runtime destroy readback evidence does not bind the post-destroy state")

    runtime_state = require_object(runtime_receipt.get("state"), "runtime receipt state evidence")
    resource_ids = require_object(
        runtime_state.get("resource_ids"), "runtime receipt resource identifiers"
    )
    receipt_addresses = runtime_receipt.get("state_addresses")
    receipt_outputs = require_object(runtime_receipt.get("outputs"), "runtime receipt outputs")
    if (
        not isinstance(receipt_addresses, list)
        or not all(isinstance(address, str) for address in receipt_addresses)
        or len(receipt_addresses) != len(set(receipt_addresses))
        or set(resource_ids) != set(receipt_addresses)
        or not all(isinstance(value, str) and OCID_RE.match(value) for value in resource_ids.values())
        or len(set(resource_ids.values())) != len(resource_ids)
    ):
        raise ContractError("runtime receipt resource identifiers are incomplete")
    validate_managed_state_addresses(
        receipt_addresses, "runtime", receipt_outputs.get("gateway_endpoint_type")
    )
    readback_resource_ids = dict(resource_ids)
    for readback_address, output_name in RUNTIME_CHILD_READBACK_OUTPUTS.items():
        resource_id = receipt_outputs.get(output_name)
        if not isinstance(resource_id, str) or not OCID_RE.match(resource_id):
            raise ContractError("runtime receipt child resource identifiers are incomplete")
        readback_resource_ids[readback_address] = resource_id
    if len(set(readback_resource_ids.values())) != len(readback_resource_ids):
        raise ContractError("runtime receipt readback identifiers are not unique")
    checks = evidence.get("checks")
    if not isinstance(checks, list) or len(checks) != len(readback_resource_ids):
        raise ContractError("runtime destroy readback evidence has an incomplete check set")
    observed: Dict[str, str] = {}
    for raw_check in checks:
        check = require_object(raw_check, "runtime destroy readback check")
        if set(check) != {"address", "resource_id", "result"}:
            raise ContractError("runtime destroy readback check contains unsupported fields")
        address = check.get("address")
        resource_id = check.get("resource_id")
        if (
            not isinstance(address, str)
            or not isinstance(resource_id, str)
            or check.get("result") != "not_found"
            or address in observed
        ):
            raise ContractError("runtime destroy readback check is malformed")
        observed[address] = resource_id
    if observed != readback_resource_ids:
        raise ContractError("runtime destroy readback checks do not cover the exact receipt resources")
    return sha256_file(evidence_path)


def command_teardown_audit(args: argparse.Namespace) -> int:
    receipt = require_object(load_json(Path(args.receipt)), "deployment receipt")
    if (
        receipt.get("schema_version") != SCHEMA_VERSION
        or receipt.get("artifact") != "deployment-receipt"
        or receipt.get("status") != "locally_verified"
    ):
        raise ContractError("teardown requires a locally verified deployment receipt")
    layer = receipt.get("layer")
    if layer not in ("bootstrap", "runtime"):
        raise ContractError("receipt has an unsupported teardown layer")
    target = require_object(receipt.get("target"), "receipt target")
    target_home_region = target.get("home_region")
    if layer == "bootstrap" and (target_home_region is None or args.home_region is None):
        raise ContractError("bootstrap teardown requires the reviewed tenancy home region")
    if layer == "runtime" and args.home_region is not None:
        raise ContractError("runtime teardown must not set home_region")
    validate_target(
        target.get("principal"),
        target.get("tenancy"),
        target.get("region"),
        target.get("compartment"),
        target_home_region,
        target.get("oci_profile"),
    )
    validate_target(
        args.principal,
        args.tenancy,
        args.region,
        args.compartment,
        args.home_region,
        args.oci_profile,
    )
    current_fingerprint = fingerprint(
        args.principal,
        args.tenancy,
        args.region,
        args.compartment,
        args.home_region,
        args.oci_profile,
    )
    reasons: Set[str] = set()
    if current_fingerprint != target.get("fingerprint"):
        reasons.add("target_fingerprint_mismatch")

    raw_receipt_addresses = receipt.get("state_addresses")
    if not isinstance(raw_receipt_addresses, list) or not all(isinstance(item, str) for item in raw_receipt_addresses):
        raise ContractError("receipt state_addresses must be an array of strings")
    if len(raw_receipt_addresses) != len(set(raw_receipt_addresses)):
        raise ContractError("receipt state_addresses contains duplicates")
    receipt_addresses = set(raw_receipt_addresses)
    validate_managed_state_addresses(
        sorted(receipt_addresses), layer, require_object(receipt.get("outputs"), "receipt outputs").get("gateway_endpoint_type")
    )
    receipt_state = require_object(receipt.get("state"), "receipt state evidence")
    receipt_resource_ids = require_object(
        receipt_state.get("resource_ids"), "receipt state resource identifiers"
    )
    current_state, current_state_hash, current_lineage, current_serial = decode_saved_state(
        Path(args.state), args.terraform_bin
    )
    current_outputs, current_managed, current_data, current_resource_ids = state_snapshot_evidence(
        current_state,
        layer,
        target["tenancy"],
        target["compartment"],
    )
    current_addresses = set(current_managed)
    if receipt_addresses != current_addresses:
        reasons.add("receipt_state_address_mismatch")
    if receipt_resource_ids != current_resource_ids:
        reasons.add("receipt_state_resource_id_mismatch")
    if receipt_state.get("lineage") != current_lineage:
        reasons.add("state_lineage_mismatch")
    receipt_serial = receipt_state.get("serial")
    if not isinstance(receipt_serial, int) or isinstance(receipt_serial, bool) or current_serial < receipt_serial:
        reasons.add("state_serial_regressed")
    if require_object(receipt.get("outputs"), "receipt outputs") != current_outputs:
        reasons.add("receipt_state_output_mismatch")

    plan, plan_json_hash, saved_hash = decode_saved_plan(Path(args.saved_plan), args.terraform_bin)
    format_version = plan.get("format_version")
    if not isinstance(format_version, str) or format_version.split(".", 1)[0] != "1":
        raise ContractError("unsupported Terraform destroy plan JSON format major version")
    changes = plan.get("resource_changes", [])
    if not isinstance(changes, list):
        raise ContractError("destroy plan resource_changes must be an array")
    variables, _config_resources, binding_blockers = target_binding_blockers(
        plan,
        layer,
        args.tenancy,
        args.region,
        args.compartment,
        args.home_region,
        args.oci_profile,
    )
    reasons.update(binding_blockers)
    if not binding_blockers:
        try:
            validate_state_security_contract(
                current_state,
                plan,
                layer,
                args.tenancy,
                args.region,
                args.compartment,
                args.home_region,
                args.oci_profile,
            )
        except ContractError:
            reasons.add("current_state_security_contract_mismatch")
    expected_destroy_addresses = expected_managed_plan_addresses(layer, variables)
    if expected_destroy_addresses is None or expected_destroy_addresses != receipt_addresses:
        reasons.add("destroy_plan_target_contract_mismatch")
    delete_addresses: Set[str] = set()
    seen_addresses: Set[str] = set()
    invalid_actions: List[str] = []
    for raw in changes:
        change = require_object(raw, "destroy resource change")
        if change.get("mode", "managed") != "managed":
            continue
        address = change.get("address")
        details = require_object(change.get("change"), "destroy resource change.change")
        classification = action_class(details.get("actions"))
        if not isinstance(address, str):
            raise ContractError("destroy resource change is missing an address")
        if address in seen_addresses:
            reasons.add("destroy_plan_contains_duplicate_address")
        seen_addresses.add(address)
        expected_type = expected_address_type(layer, address, "managed")
        if expected_type is None or expected_type != change.get("type"):
            reasons.add("destroy_plan_address_outside_contract")
        before = details.get("before")
        if not isinstance(before, dict):
            reasons.add("destroy_plan_before_values_missing")
        else:
            if before.get("id") != current_resource_ids.get(address):
                reasons.add("destroy_plan_resource_id_mismatch")
            reasons.update(
                resource_scope_blockers(
                    address,
                    str(change.get("type")),
                    before,
                    layer,
                    args.tenancy,
                    args.compartment,
                )
            )
        if classification != "delete":
            invalid_actions.append(address)
        else:
            delete_addresses.add(address)
    if invalid_actions:
        reasons.add("destroy_plan_contains_non_delete_actions")
    if delete_addresses != receipt_addresses:
        reasons.add("destroy_plan_owned_set_mismatch")

    runtime_destroy_evidence_hash: Optional[str] = None
    if layer == "bootstrap":
        runtime_receipt_argument = getattr(args, "runtime_receipt", None)
        runtime_state_argument = getattr(args, "runtime_state", None)
        runtime_evidence_argument = getattr(args, "runtime_destroy_evidence", None)
        if not runtime_receipt_argument or not runtime_state_argument or not runtime_evidence_argument:
            reasons.add("runtime_destroy_evidence_missing")
        else:
            runtime_receipt_path = Path(runtime_receipt_argument)
            runtime_receipt = require_object(load_json(runtime_receipt_path), "runtime receipt")
            runtime_receipt_valid = True
            if (
                runtime_receipt.get("schema_version") != SCHEMA_VERSION
                or runtime_receipt.get("artifact") != "deployment-receipt"
                or runtime_receipt.get("status") != "locally_verified"
                or runtime_receipt.get("layer") != "runtime"
                or runtime_receipt.get("blueprint_version") != BLUEPRINT_VERSION
                or runtime_receipt.get("environment_class") != "sandbox"
            ):
                reasons.add("runtime_receipt_invalid")
                runtime_receipt_valid = False
            else:
                runtime_target = require_object(runtime_receipt.get("target"), "runtime receipt target")
                try:
                    validate_target(
                        runtime_target.get("principal"),
                        runtime_target.get("tenancy"),
                        runtime_target.get("region"),
                        runtime_target.get("compartment"),
                        runtime_target.get("home_region"),
                        runtime_target.get("oci_profile"),
                    )
                    expected_runtime_fingerprint = fingerprint(
                        runtime_target["principal"],
                        runtime_target["tenancy"],
                        runtime_target["region"],
                        runtime_target["compartment"],
                        runtime_target.get("home_region"),
                        runtime_target["oci_profile"],
                    )
                except ContractError:
                    expected_runtime_fingerprint = ""
                    runtime_receipt_valid = False
                    reasons.add("runtime_receipt_invalid")
                if runtime_target.get("fingerprint") != expected_runtime_fingerprint:
                    runtime_receipt_valid = False
                    reasons.add("runtime_receipt_invalid")
                if any(
                    runtime_target.get(field) != target.get(field)
                    for field in ("tenancy", "region", "compartment", "oci_profile")
                ):
                    reasons.add("runtime_receipt_target_mismatch")
                    runtime_receipt_valid = False
                if runtime_receipt.get("bootstrap_receipt_sha256") != sha256_file(Path(args.receipt)):
                    reasons.add("runtime_bootstrap_lineage_mismatch")
                    runtime_receipt_valid = False
            runtime_state, _runtime_state_hash, runtime_lineage, runtime_serial = decode_saved_state(
                Path(runtime_state_argument), args.terraform_bin
            )
            _runtime_outputs, runtime_managed, _runtime_data, _runtime_ids = state_snapshot_evidence(
                runtime_state,
                "runtime",
                target["tenancy"],
                target["compartment"],
                allow_empty=True,
            )
            if runtime_managed:
                reasons.add("runtime_state_not_empty")
            runtime_receipt_state = require_object(
                runtime_receipt.get("state"), "runtime receipt state evidence"
            )
            if runtime_receipt_state.get("lineage") != runtime_lineage:
                reasons.add("runtime_state_lineage_mismatch")
            runtime_receipt_serial = runtime_receipt_state.get("serial")
            if (
                not isinstance(runtime_receipt_serial, int)
                or isinstance(runtime_receipt_serial, bool)
                or runtime_serial <= runtime_receipt_serial
            ):
                reasons.add("runtime_destroy_state_serial_not_advanced")
                runtime_receipt_valid = False
            if runtime_receipt_valid and not runtime_managed:
                try:
                    runtime_destroy_evidence_hash = validate_runtime_destroy_evidence(
                        Path(runtime_evidence_argument),
                        runtime_receipt_path,
                        runtime_receipt,
                        runtime_target["fingerprint"],
                        runtime_lineage,
                        runtime_serial,
                    )
                except ContractError:
                    reasons.add("runtime_destroy_readback_evidence_invalid")
    receipt_hash = sha256_file(Path(args.receipt))
    iac_source_hash, iac_source_manifest = saved_plan_source_evidence(
        Path(args.saved_plan), str(layer), saved_hash
    )
    ready = not reasons
    report = {
        "schema_version": SCHEMA_VERSION,
        "artifact": "teardown-audit",
        "generated_at": iso_now(),
        "layer": layer,
        "ready_for_destroy": ready,
        "block_reasons": sorted(reasons),
        "target_fingerprint": current_fingerprint,
        "saved_plan_sha256": saved_hash,
        "plan_json_sha256": plan_json_hash,
        "iac_source_sha256": iac_source_hash,
        "iac_source_manifest": iac_source_manifest,
        "state_snapshot_sha256": current_state_hash,
        "state_lineage": current_lineage,
        "state_serial": current_serial,
        "receipt_sha256": receipt_hash,
        "runtime_destroy_evidence_sha256": runtime_destroy_evidence_hash,
        "owned_address_count": len(receipt_addresses),
        "observed_data_source_count": len(current_data),
        "planned_delete_count": len(delete_addresses),
        "approval_phrase": (
            f"DESTROY {str(layer).upper()} {current_fingerprint} {saved_hash[:16]} "
            f"{plan_json_hash[:16]} {iac_source_hash[:16]} {receipt_hash[:16]} "
            f"{current_state_hash[:16]}"
            f"{' ' + runtime_destroy_evidence_hash[:16] if runtime_destroy_evidence_hash else ''}"
            if ready
            else None
        ),
        "next_layer": "collect-runtime-destroy-readback" if ready and layer == "runtime" else None,
    }
    write_private_json(Path(args.out), report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if ready else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Offline contract checks for the Founder Toolkit for OCI Container API preview"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    config = subparsers.add_parser("config-check", help="validate a generated JSON tfvars contract")
    config.add_argument("--kind", choices=("bootstrap", "runtime"), required=True)
    config.add_argument("--config", required=True)
    config.add_argument("--out")
    config.set_defaults(handler=command_config_check)

    image_ref = subparsers.add_parser("image-ref-check", help="validate an immutable container image reference")
    image_ref.add_argument("--image", required=True)
    image_ref.set_defaults(handler=command_image_ref_check)

    plan = subparsers.add_parser("plan-summary", help="create a value-redacted Terraform plan summary")
    plan.add_argument("--stack", choices=("bootstrap", "runtime"), required=True)
    plan.add_argument("--saved-plan", required=True)
    plan.add_argument("--terraform-bin", default="terraform")
    plan.add_argument("--bootstrap-receipt")
    plan.add_argument("--principal", required=True)
    plan.add_argument("--tenancy", required=True)
    plan.add_argument("--region", required=True)
    plan.add_argument("--home-region")
    plan.add_argument("--oci-profile", required=True)
    plan.add_argument("--compartment", required=True)
    plan.add_argument("--out", required=True)
    plan.set_defaults(handler=command_plan_summary)

    smoke = subparsers.add_parser("smoke", help="verify the bounded HTTPS health contract")
    smoke.add_argument("--url", required=True)
    smoke.add_argument("--out", required=True)
    smoke.add_argument("--timeout", type=float, default=10.0)
    smoke.add_argument("--attempts", type=int, default=3)
    smoke.set_defaults(handler=command_smoke)

    receipt = subparsers.add_parser("receipt", help="generate a strict, secret-free deployment receipt")
    receipt.add_argument("--layer", choices=("bootstrap", "runtime"), required=True)
    receipt.add_argument("--summary", required=True)
    receipt.add_argument("--saved-plan", required=True)
    receipt.add_argument("--terraform-bin", default="terraform")
    receipt.add_argument("--state", required=True, help="raw Terraform state snapshot captured after apply")
    receipt.add_argument("--provider-lock", required=True)
    receipt.add_argument("--source-revision", required=True)
    receipt.add_argument("--iac-revision", required=True)
    receipt.add_argument("--smoke")
    receipt.add_argument("--bootstrap-receipt")
    receipt.add_argument("--previous-image-url")
    receipt.add_argument("--out", required=True)
    receipt.set_defaults(handler=command_receipt)

    teardown = subparsers.add_parser("teardown-audit", help="reconcile receipt, state, and exact destroy plan")
    teardown.add_argument("--receipt", required=True)
    teardown.add_argument("--saved-plan", required=True)
    teardown.add_argument("--terraform-bin", default="terraform")
    teardown.add_argument("--state", required=True, help="raw current Terraform state snapshot")
    teardown.add_argument("--principal", required=True)
    teardown.add_argument("--tenancy", required=True)
    teardown.add_argument("--region", required=True)
    teardown.add_argument("--home-region")
    teardown.add_argument("--oci-profile", required=True)
    teardown.add_argument("--compartment", required=True)
    teardown.add_argument("--runtime-receipt")
    teardown.add_argument("--runtime-state", help="raw post-destroy runtime state snapshot")
    teardown.add_argument(
        "--runtime-destroy-evidence",
        help="local read-only OCI not-found evidence for every runtime receipt OCID",
    )
    teardown.add_argument("--out", required=True)
    teardown.set_defaults(handler=command_teardown_audit)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (ContractError, OSError) as exc:
        print(f"founderctl: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
