from __future__ import annotations

import argparse
import copy
import contextlib
import datetime as dt
import hashlib
import importlib.util
import io
import json
import pathlib
import tempfile
import unittest
import zipfile
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures"
SPEC = importlib.util.spec_from_file_location("founderctl", ROOT / "tools" / "founderctl.py")
assert SPEC and SPEC.loader
FOUNDERCTL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FOUNDERCTL)


TENANCY = "ocid1.tenancy.oc1..fake"
COMPARTMENT = "ocid1.compartment.oc1..fake"
REGION = "sa-saopaulo-1"
PRINCIPAL = "ocid1.user.oc1..fake"
OCI_PROFILE = "DEFAULT"
IMAGE = "gru.ocir.io/test/founder-api/api@sha256:" + "a" * 64


def _port_options(port: int, protocol: str = "6") -> dict:
    key = "tcp_options" if protocol == "6" else "udp_options"
    return {key: [{"destination_port_range": [{"min": port, "max": port}]}]}


def _configuration_expressions(address: str) -> dict:
    def reference(*items: str) -> dict:
        return {"references": list(items)}

    expressions: dict = {}
    if address == "oci_apigateway_gateway.api":
        expressions = {
            "network_security_group_ids": reference(
                "oci_core_network_security_group.gateway.id"
            ),
            "subnet_id": reference("oci_core_subnet.gateway.id"),
        }
    elif address == "oci_container_instances_container_instance.api":
        expressions = {
            "vnics": [
                {
                    "subnet_id": reference("oci_core_subnet.app.id"),
                    "nsg_ids": reference(
                        "oci_core_network_security_group.app.id"
                    ),
                }
            ]
        }
    elif address == "oci_core_route_table.app":
        expressions = {
            "route_rules": [
                {
                    "network_entity_id": reference(
                        "oci_core_service_gateway.oracle_services.id"
                    ),
                    "destination": reference(
                        "data.oci_core_services.oracle_services.services[0].cidr_block"
                    ),
                }
            ]
        }
    elif address == "oci_core_network_security_group_security_rule.gateway_https_ingress":
        expressions = {
            "network_security_group_id": reference(
                "oci_core_network_security_group.gateway.id"
            ),
            "source": reference("each.value"),
        }
    elif address == "oci_core_network_security_group_security_rule.gateway_to_app":
        expressions = {
            "network_security_group_id": reference(
                "oci_core_network_security_group.gateway.id"
            ),
            "destination": reference("oci_core_network_security_group.app.id"),
        }
    elif address == "oci_core_network_security_group_security_rule.app_from_gateway":
        expressions = {
            "network_security_group_id": reference(
                "oci_core_network_security_group.app.id"
            ),
            "source": reference("oci_core_network_security_group.gateway.id"),
        }
    elif address == "oci_core_network_security_group_security_rule.app_to_oracle_services":
        expressions = {
            "network_security_group_id": reference(
                "oci_core_network_security_group.app.id"
            ),
            "destination": reference(
                "data.oci_core_services.oracle_services.services[0].cidr_block"
            ),
        }
    elif address in {
        "oci_core_network_security_group_security_rule.app_dns_tcp",
        "oci_core_network_security_group_security_rule.app_dns_udp",
    }:
        expressions = {
            "network_security_group_id": reference(
                "oci_core_network_security_group.app.id"
            )
        }
    vcn_bound = {
        "oci_core_internet_gateway.public",
        "oci_core_service_gateway.oracle_services",
        "oci_core_route_table.gateway",
        "oci_core_route_table.app",
        "oci_core_security_list.empty",
        "oci_core_subnet.gateway",
        "oci_core_subnet.app",
        "oci_core_network_security_group.gateway",
        "oci_core_network_security_group.app",
    }
    if address in vcn_bound:
        expressions["vcn_id"] = reference("oci_core_vcn.sandbox.id")
    if address == "oci_core_service_gateway.oracle_services":
        expressions["services"] = [
            {
                "service_id": reference(
                    "data.oci_core_services.oracle_services.services[0].id"
                )
            }
        ]
    if address == "oci_core_subnet.gateway":
        expressions.update(
            {
                "route_table_id": reference("oci_core_route_table.gateway.id"),
                "security_list_ids": reference("oci_core_security_list.empty.id"),
            }
        )
    if address == "oci_core_subnet.app":
        expressions.update(
            {
                "route_table_id": reference("oci_core_route_table.app.id"),
                "security_list_ids": reference("oci_core_security_list.empty.id"),
            }
        )
    if address == "oci_apigateway_deployment.api":
        expressions["gateway_id"] = reference("oci_apigateway_gateway.api.id")
    if address in {
        "oci_logging_log.gateway_access",
        "oci_logging_log.gateway_execution",
    }:
        expressions.update(
            {
                "log_group_id": reference("oci_logging_log_group.api.id"),
                "configuration": [
                    {
                        "compartment_id": reference("var.compartment_id"),
                        "source": [
                            {
                                "resource": reference(
                                    "oci_apigateway_deployment.api.id"
                                ),
                                "service": reference(
                                    "var.api_gateway_logging_service_name"
                                ),
                            }
                        ],
                    }
                ],
            }
        )
    if address == "oci_ons_subscription.email":
        expressions.update(
            {
                "topic_id": reference("oci_ons_notification_topic.alarms.id"),
                "endpoint": reference("var.notification_email"),
            }
        )
    if address in {
        "oci_monitoring_alarm.high_cpu",
        "oci_monitoring_alarm.high_memory",
    }:
        threshold = (
            "var.cpu_alarm_threshold"
            if address.endswith("high_cpu")
            else "var.memory_alarm_threshold"
        )
        expressions.update(
            {
                "metric_compartment_id": reference("var.compartment_id"),
                "destinations": reference("oci_ons_notification_topic.alarms.id"),
                "query": reference(
                    "oci_container_instances_container_instance.api.id", threshold
                ),
            }
        )
    return expressions


def _runtime_after(address: str, variables: dict) -> dict:
    resource_type = FOUNDERCTL.expected_address_type("runtime", address, "managed")
    values: dict = {"compartment_id": variables["compartment_id"]}
    ingress_match = FOUNDERCTL.GATEWAY_INGRESS_ADDRESS_RE.fullmatch(address)

    if address == "oci_apigateway_gateway.api":
        values.update(
            {
                "endpoint_type": variables["gateway_endpoint_type"],
                "ip_mode": "IPV4",
                "network_security_group_ids": [None],
                "subnet_id": None,
            }
        )
    elif address == "oci_apigateway_deployment.api":
        private_ip = "10.42.1.10"
        port = variables["container_port"]
        routes = []
        for path in ("/", "/healthz", "/readyz"):
            suffix = path
            routes.append(
                {
                    "path": path,
                    "methods": ["GET"],
                    "backend": [
                        {
                            "type": "HTTP_BACKEND",
                            "url": f"http://{private_ip}:{port}{suffix}",
                            "connect_timeout_in_seconds": 5,
                            "read_timeout_in_seconds": 15,
                            "send_timeout_in_seconds": 15,
                        }
                    ],
                }
            )
        values.update(
            {
                "path_prefix": variables["api_path_prefix"],
                "specification": [
                    {
                        "request_policies": [
                            {
                                "rate_limiting": [
                                    {
                                        "rate_in_requests_per_second": variables[
                                            "rate_limit_requests_per_second"
                                        ],
                                        "rate_key": "CLIENT_IP",
                                    }
                                ]
                            }
                        ],
                        "routes": routes,
                    }
                ],
            }
        )
    elif address == "oci_container_instances_container_instance.api":
        values.update(
            {
                "availability_domain": variables["availability_domain"],
                "shape": variables["container_shape"],
                "shape_config": [
                    {
                        "ocpus": variables["ocpus"],
                        "memory_in_gbs": variables["memory_in_gbs"],
                    }
                ],
                "container_restart_policy": "ALWAYS",
                "graceful_shutdown_timeout_in_seconds": 30,
                "containers": [
                    {
                        "image_url": variables["container_image_url"],
                        "is_resource_principal_disabled": True,
                        "environment_variables": {
                            "INTERNAL_VALUE": "value-that-must-not-escape",
                            "OCI_FOUNDER_RELEASE": variables["release_id"],
                            "PORT": str(variables["container_port"]),
                        },
                        "health_checks": [
                            {
                                "health_check_type": "HTTP",
                                "path": "/healthz",
                                "port": variables["container_port"],
                                "failure_action": "KILL",
                            }
                        ],
                        "security_context": [
                            {
                                "is_non_root_user_check_enabled": True,
                                "is_root_file_system_readonly": True,
                                "run_as_user": 65532,
                                "run_as_group": 65532,
                                "capabilities": [{"drop_capabilities": ["ALL"]}],
                            }
                        ],
                    }
                ],
                "vnics": [
                    {
                        "is_public_ip_assigned": False,
                        "private_ip": "10.42.1.10",
                        "nsg_ids": [None],
                        "subnet_id": None,
                    }
                ],
            }
        )
    elif ingress_match:
        values = {
            "direction": "INGRESS",
            "protocol": "6",
            "source": ingress_match.group(1),
            "source_type": "CIDR_BLOCK",
            "stateless": False,
            **_port_options(443),
        }
    elif address == "oci_core_network_security_group_security_rule.gateway_to_app":
        values = {
            "direction": "EGRESS",
            "protocol": "6",
            "destination": None,
            "destination_type": "NETWORK_SECURITY_GROUP",
            "stateless": False,
            **_port_options(variables["container_port"]),
        }
    elif address == "oci_core_network_security_group_security_rule.app_from_gateway":
        values = {
            "direction": "INGRESS",
            "protocol": "6",
            "source": None,
            "source_type": "NETWORK_SECURITY_GROUP",
            "stateless": False,
            **_port_options(variables["container_port"]),
        }
    elif address == "oci_core_network_security_group_security_rule.app_to_oracle_services":
        values = {
            "direction": "EGRESS",
            "protocol": "6",
            "destination": None,
            "destination_type": "SERVICE_CIDR_BLOCK",
            "stateless": False,
            **_port_options(443),
        }
    elif address in {
        "oci_core_network_security_group_security_rule.app_dns_tcp",
        "oci_core_network_security_group_security_rule.app_dns_udp",
    }:
        protocol = "17" if address.endswith("udp") else "6"
        values = {
            "direction": "EGRESS",
            "protocol": protocol,
            "destination": "169.254.169.254/32",
            "destination_type": "CIDR_BLOCK",
            "stateless": False,
            **_port_options(53, protocol),
        }
    elif address == "oci_core_vcn.sandbox":
        values["cidr_blocks"] = [variables["vcn_cidr"]]
    elif address == "oci_core_subnet.gateway":
        values.update(
            {
                "cidr_block": variables["gateway_subnet_cidr"],
                "prohibit_public_ip_on_vnic": variables["gateway_endpoint_type"] != "PUBLIC",
            }
        )
    elif address == "oci_core_subnet.app":
        values.update(
            {
                "cidr_block": variables["app_subnet_cidr"],
                "prohibit_public_ip_on_vnic": True,
            }
        )
    elif address == "oci_core_security_list.empty":
        values.update({"ingress_security_rules": [], "egress_security_rules": []})
    elif address == "oci_core_route_table.app":
        values["route_rules"] = [
            {"destination": None, "destination_type": "SERVICE_CIDR_BLOCK"}
        ]
    elif address == "oci_core_route_table.gateway":
        values["route_rules"] = (
            [{"destination": "0.0.0.0/0", "destination_type": "CIDR_BLOCK"}]
            if variables["gateway_endpoint_type"] == "PUBLIC"
            else []
        )
    elif address == "oci_core_service_gateway.oracle_services":
        values["services"] = [{"service_id": None}]
    elif resource_type == "oci_logging_log":
        category = "access" if address.endswith("gateway_access") else "execution"
        values = {
            "log_group_id": None,
            "log_type": "SERVICE",
            "is_enabled": True,
            "retention_duration": 30,
            "configuration": [
                {
                    "compartment_id": variables["compartment_id"],
                    "source": [
                        {
                            "category": category,
                            "resource": None,
                            "service": variables["api_gateway_logging_service_name"],
                            "source_type": "OCISERVICE",
                        }
                    ],
                }
            ],
        }
    elif address == "oci_ons_subscription.email":
        values.update(
            {
                "topic_id": None,
                "protocol": "EMAIL",
                "endpoint": variables["notification_email"],
            }
        )
    elif resource_type == "oci_monitoring_alarm":
        metric = "CpuUtilization" if address.endswith("high_cpu") else "MemoryUtilization"
        threshold = (
            variables["cpu_alarm_threshold"]
            if address.endswith("high_cpu")
            else variables["memory_alarm_threshold"]
        )
        values.update(
            {
                "metric_compartment_id": variables["compartment_id"],
                "namespace": "oci_computecontainerinstance",
                "query": None,
                "severity": "WARNING",
                "is_enabled": True,
                "pending_duration": "PT5M",
                "destinations": [None],
            }
        )
    return values


def build_runtime_plan(public: bool = False) -> dict:
    variables = {
        "tenancy_ocid": TENANCY,
        "compartment_id": COMPARTMENT,
        "region": REGION,
        "oci_profile": "DEFAULT",
        "environment_class": "sandbox",
        "project_slug": "founder-api",
        "release_id": "abc1234",
        "container_image_url": IMAGE,
        "approved_repository_path": "gru.ocir.io/test/founder-api/api",
        "availability_domain": "example-prefix:SA-SAOPAULO-1-AD-1",
        "container_shape": "CI.Standard.E4.Flex",
        "ocpus": 1,
        "memory_in_gbs": 2,
        "container_port": 8080,
        "vcn_cidr": "10.42.0.0/16",
        "gateway_subnet_cidr": "10.42.0.0/24",
        "app_subnet_cidr": "10.42.1.0/24",
        "gateway_endpoint_type": "PUBLIC" if public else "PRIVATE",
        "allowed_ingress_cidrs": ["0.0.0.0/0"] if public else ["10.42.0.0/16"],
        "api_path_prefix": "/api",
        "rate_limit_requests_per_second": 10,
        "notification_email": "founder@invalid.test",
        "api_gateway_logging_service_name": "apigateway",
        "cpu_alarm_threshold": 80,
        "memory_alarm_threshold": 85,
    }
    expected_addresses = FOUNDERCTL.expected_managed_plan_addresses("runtime", variables)
    assert expected_addresses is not None

    resource_changes = []
    for address in sorted(expected_addresses):
        resource_type = FOUNDERCTL.expected_address_type("runtime", address, "managed")
        after = _runtime_after(address, variables)
        resource_changes.append(
            {
                "address": address,
                "mode": "managed",
                "type": resource_type,
                "change": {
                    "actions": ["create"],
                    "before": None,
                    "after": after,
                    "after_unknown": {},
                    "before_sensitive": False,
                    "after_sensitive": (
                        {"containers": [{"environment_variables": {"INTERNAL_VALUE": True}}]}
                        if address == "oci_container_instances_container_instance.api"
                        else False
                    ),
                },
            }
        )
    for address, resource_type in sorted(FOUNDERCTL.RUNTIME_DATA_ADDRESS_TYPES.items()):
        resource_changes.append(
            {
                "address": address,
                "mode": "data",
                "type": resource_type,
                "change": {
                    "actions": ["read"],
                    "before": None,
                    "after": {},
                    "after_unknown": {},
                    "before_sensitive": False,
                    "after_sensitive": False,
                },
            }
        )

    configuration_addresses = sorted(
        {
            FOUNDERCTL.base_configuration_address(address)
            for address in set(FOUNDERCTL.RUNTIME_ADDRESS_TYPES)
            | {"oci_core_network_security_group_security_rule.gateway_https_ingress"}
        }
    )
    configuration_resources = []
    for address in configuration_addresses:
        resource_type = (
            "oci_core_network_security_group_security_rule"
            if address == "oci_core_network_security_group_security_rule.gateway_https_ingress"
            else "oci_core_internet_gateway"
            if address == "oci_core_internet_gateway.public"
            else FOUNDERCTL.expected_address_type("runtime", address, "managed")
        )
        configuration_resource = {
            "address": address,
            "mode": "managed",
            "type": resource_type,
            "provider_config_key": "oci",
            "expressions": _configuration_expressions(address),
        }
        if address == "oci_core_network_security_group_security_rule.gateway_https_ingress":
            configuration_resource["for_each_expression"] = {
                "references": ["var.allowed_ingress_cidrs"]
            }
        configuration_resources.append(configuration_resource)
    for address, resource_type in sorted(FOUNDERCTL.RUNTIME_DATA_ADDRESS_TYPES.items()):
        configuration_resources.append(
            {
                "address": address,
                "mode": "data",
                "type": resource_type,
                "provider_config_key": "oci",
                "expressions": {},
            }
        )

    output_changes = {
        name: {
            "actions": ["create"],
            "before": None,
            "after": "value-that-must-not-escape",
            "after_unknown": True,
            "before_sensitive": False,
            "after_sensitive": False,
        }
        for name in FOUNDERCTL.RECEIPT_OUTPUT_KEYS["runtime"]
    }
    return {
        "format_version": "1.2",
        "terraform_version": FOUNDERCTL.TERRAFORM_VERSION,
        "variables": {name: {"value": value} for name, value in variables.items()},
        "configuration": {
            "provider_config": {
                "oci": {
                    "name": "oci",
                    "full_name": "registry.terraform.io/oracle/oci",
                    "expressions": {
                        "config_file_profile": {"references": ["var.oci_profile"]},
                        "region": {"references": ["var.region"]},
                    },
                }
            },
            "root_module": {"resources": configuration_resources},
        },
        "resource_changes": resource_changes,
        "output_changes": output_changes,
        "resource_drift": [],
    }


def planned_resource(plan: dict, address: str) -> dict:
    return next(change for change in plan["resource_changes"] if change["address"] == address)


def configured_resource(plan: dict, address: str) -> dict:
    resources = plan["configuration"]["root_module"]["resources"]
    return next(resource for resource in resources if resource["address"] == address)


def nested_value(value: object, *path: object) -> object:
    current = value
    for component in path:
        current = current[component]  # type: ignore[index]
    return current


def fake_ocid(label: str) -> str:
    suffix = hashlib.sha256(label.encode("utf-8")).hexdigest()[:24]
    return f"ocid1.test.oc1..{suffix}"


def write_saved_plan_source_fixture(
    path: pathlib.Path,
    stack: str,
    *,
    tampered_source: object = None,
    extra_source: bool = False,
) -> None:
    source_root = ROOT / "terraform" / stack
    with zipfile.ZipFile(path, "w") as archive:
        for source in sorted(source_root.glob("*.tf"), key=lambda item: item.name):
            payload = source.read_bytes()
            if source.name == tampered_source:
                payload += b"\n# unreviewed mutation\n"
            archive.writestr(f"tfconfig/m-/{source.name}", payload)
        archive.write(source_root / ".terraform.lock.hcl", ".terraform.lock.hcl")
        if extra_source:
            archive.writestr("tfconfig/m-/unreviewed.tf", b"resource \"null_resource\" \"x\" {}\n")


def build_runtime_state_show(public: bool = False) -> dict:
    plan = build_runtime_plan(public=public)
    variables = {name: entry["value"] for name, entry in plan["variables"].items()}
    resources = []
    resource_ids = {}
    for change in plan["resource_changes"]:
        address = change["address"]
        values = copy.deepcopy(change["change"]["after"])
        if change["mode"] == "managed":
            identifier = fake_ocid(address)
            values["id"] = identifier
            resource_ids[address] = identifier
            if address == "oci_container_instances_container_instance.api":
                values["containers"][0]["container_id"] = fake_ocid("runtime-container")
                values["vnics"][0]["vnic_id"] = fake_ocid("runtime-vnic")
            elif address == "oci_apigateway_gateway.api":
                values["hostname"] = "api.example.invalid"
            elif address == "oci_ons_subscription.email":
                values["state"] = "ACTIVE"
        resources.append(
            {
                "address": address,
                "mode": change["mode"],
                "type": change["type"],
                "values": values,
            }
        )

    by_address = {resource["address"]: resource["values"] for resource in resources}
    vcn_id = resource_ids["oci_core_vcn.sandbox"]
    gateway_nsg_id = resource_ids["oci_core_network_security_group.gateway"]
    app_nsg_id = resource_ids["oci_core_network_security_group.app"]
    gateway_subnet_id = resource_ids["oci_core_subnet.gateway"]
    app_subnet_id = resource_ids["oci_core_subnet.app"]
    gateway_route_id = resource_ids["oci_core_route_table.gateway"]
    app_route_id = resource_ids["oci_core_route_table.app"]
    security_list_id = resource_ids["oci_core_security_list.empty"]
    service_gateway_id = resource_ids["oci_core_service_gateway.oracle_services"]
    oracle_service_id = fake_ocid("oracle-services-network")
    oracle_service_cidr = "all-gru-services-in-oracle-services-network"

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
        if address in by_address:
            by_address[address]["vcn_id"] = vcn_id
    by_address["oci_apigateway_gateway.api"].update(
        {
            "network_security_group_ids": [gateway_nsg_id],
            "subnet_id": gateway_subnet_id,
        }
    )
    by_address["oci_core_subnet.gateway"].update(
        {
            "route_table_id": gateway_route_id,
            "security_list_ids": [security_list_id],
        }
    )
    by_address["oci_core_subnet.app"].update(
        {
            "route_table_id": app_route_id,
            "security_list_ids": [security_list_id],
        }
    )
    by_address["data.oci_core_services.oracle_services"]["services"] = [
        {"id": oracle_service_id, "cidr_block": oracle_service_cidr}
    ]
    by_address["oci_core_service_gateway.oracle_services"]["services"] = [
        {"service_id": oracle_service_id}
    ]
    by_address["oci_core_route_table.app"]["route_rules"][0].update(
        {
            "network_entity_id": service_gateway_id,
            "destination": oracle_service_cidr,
        }
    )
    if public:
        by_address["oci_core_route_table.gateway"]["route_rules"][0][
            "network_entity_id"
        ] = resource_ids["oci_core_internet_gateway.public[0]"]
    for address, values in by_address.items():
        ingress_match = FOUNDERCTL.GATEWAY_INGRESS_ADDRESS_RE.fullmatch(address)
        if ingress_match or address.endswith("gateway_to_app"):
            values["network_security_group_id"] = gateway_nsg_id
        elif address.startswith("oci_core_network_security_group_security_rule."):
            values["network_security_group_id"] = app_nsg_id
        if address.endswith("gateway_to_app"):
            values["destination"] = app_nsg_id
        elif address.endswith("app_from_gateway"):
            values["source"] = gateway_nsg_id
        elif address.endswith("app_to_oracle_services"):
            values["destination"] = oracle_service_cidr
    by_address["oci_container_instances_container_instance.api"]["vnics"][0].update(
        {"subnet_id": app_subnet_id, "nsg_ids": [app_nsg_id]}
    )
    by_address["oci_apigateway_deployment.api"]["gateway_id"] = resource_ids[
        "oci_apigateway_gateway.api"
    ]
    for address in (
        "oci_logging_log.gateway_access",
        "oci_logging_log.gateway_execution",
    ):
        by_address[address]["log_group_id"] = resource_ids[
            "oci_logging_log_group.api"
        ]
        by_address[address]["configuration"][0]["source"][0]["resource"] = resource_ids[
            "oci_apigateway_deployment.api"
        ]
    by_address["oci_ons_subscription.email"]["topic_id"] = resource_ids[
        "oci_ons_notification_topic.alarms"
    ]
    for address, metric, threshold in (
        (
            "oci_monitoring_alarm.high_cpu",
            "CpuUtilization",
            variables["cpu_alarm_threshold"],
        ),
        (
            "oci_monitoring_alarm.high_memory",
            "MemoryUtilization",
            variables["memory_alarm_threshold"],
        ),
    ):
        by_address[address]["destinations"] = [
            resource_ids["oci_ons_notification_topic.alarms"]
        ]
        by_address[address]["query"] = (
            f'{metric}[1m]{{resourceId = "'
            f'{resource_ids["oci_container_instances_container_instance.api"]}'
            f'"}}.mean() > {threshold}'
        )

    output_values = {
        "endpoint": f"https://api.example.invalid{variables['api_path_prefix']}",
        "healthcheck_url": (
            f"https://api.example.invalid{variables['api_path_prefix']}/healthz"
        ),
        "gateway_endpoint_type": variables["gateway_endpoint_type"],
        "container_image_url": variables["container_image_url"],
        "container_instance_id": resource_ids[
            "oci_container_instances_container_instance.api"
        ],
        "container_id": fake_ocid("runtime-container"),
        "container_vnic_id": fake_ocid("runtime-vnic"),
        "gateway_id": resource_ids["oci_apigateway_gateway.api"],
        "deployment_id": resource_ids["oci_apigateway_deployment.api"],
        "log_group_id": resource_ids["oci_logging_log_group.api"],
        "gateway_access_log_id": resource_ids["oci_logging_log.gateway_access"],
        "gateway_execution_log_id": resource_ids[
            "oci_logging_log.gateway_execution"
        ],
        "notification_topic_id": resource_ids[
            "oci_ons_notification_topic.alarms"
        ],
        "notification_subscription_id": resource_ids["oci_ons_subscription.email"],
        "notification_subscription_state": "ACTIVE",
        "cpu_alarm_id": resource_ids["oci_monitoring_alarm.high_cpu"],
        "memory_alarm_id": resource_ids["oci_monitoring_alarm.high_memory"],
    }
    return {
        "format_version": "1.0",
        "terraform_version": FOUNDERCTL.TERRAFORM_VERSION,
        "values": {
            "outputs": {
                name: {"sensitive": False, "value": value}
                for name, value in output_values.items()
            },
            "root_module": {"resources": resources},
        },
    }


def build_runtime_destroy_plan(state: dict, public: bool = False) -> dict:
    plan = build_runtime_plan(public=public)
    state_resources = {
        resource["address"]: resource
        for resource in state["values"]["root_module"]["resources"]
        if resource["mode"] == "managed"
    }
    plan["resource_changes"] = [
        {
            "address": address,
            "mode": "managed",
            "type": resource["type"],
            "change": {
                "actions": ["delete"],
                "before": copy.deepcopy(resource["values"]),
                "after": None,
                "after_unknown": False,
                "before_sensitive": False,
                "after_sensitive": False,
            },
        }
        for address, resource in sorted(state_resources.items())
    ]
    plan["output_changes"] = {}
    return plan


def build_empty_state_show() -> dict:
    return {
        "format_version": "1.0",
        "terraform_version": FOUNDERCTL.TERRAFORM_VERSION,
        "values": {"root_module": {"resources": []}},
    }


def build_runtime_destroy_evidence(
    runtime_receipt_path: pathlib.Path,
    runtime_receipt: dict,
    state_lineage: str,
    state_serial: int,
) -> dict:
    resource_ids = dict(runtime_receipt["state"]["resource_ids"])
    for address, output_name in FOUNDERCTL.RUNTIME_CHILD_READBACK_OUTPUTS.items():
        resource_ids[address] = runtime_receipt["outputs"][output_name]
    return {
        "schema_version": FOUNDERCTL.SCHEMA_VERSION,
        "artifact": "oci-destroy-readback-evidence",
        "generated_at": FOUNDERCTL.iso_now(),
        "verification_method": "authenticated-read-only-oci-get",
        "runtime_receipt_sha256": FOUNDERCTL.sha256_file(runtime_receipt_path),
        "target_fingerprint": runtime_receipt["target"]["fingerprint"],
        "state_lineage": state_lineage,
        "state_serial": state_serial,
        "checks": [
            {
                "address": address,
                "resource_id": resource_id,
                "result": "not_found",
            }
            for address, resource_id in sorted(resource_ids.items())
        ],
    }


def build_bootstrap_plan() -> dict:
    home_region = "us-ashburn-1"
    registry_endpoint = "gru.ocir.io"
    repository_name = "founder-api/api"
    project_slug = "founder-api"
    group_name = (
        f"{project_slug}-ci-"
        f"{hashlib.sha256(COMPARTMENT.encode('utf-8')).hexdigest()[:8]}"
    )
    variables = {
        "tenancy_ocid": TENANCY,
        "compartment_id": COMPARTMENT,
        "home_region": home_region,
        "target_region": REGION,
        "oci_profile": "DEFAULT",
        "project_slug": project_slug,
        "repository_name": repository_name,
        "ocir_registry_endpoint": registry_endpoint,
        "budget_target_verified_without_existing_budget": True,
    }
    after_values = {
        "oci_artifacts_container_repository.api": {
            "compartment_id": COMPARTMENT,
            "display_name": repository_name,
            "is_public": False,
            "is_immutable": True,
        },
        "oci_identity_dynamic_group.container_instances": {
            "compartment_id": TENANCY,
            "name": group_name,
            "matching_rule": (
                "ALL {resource.type='computecontainerinstance', "
                f"resource.compartment.id='{COMPARTMENT}'}}"
            ),
        },
        "oci_identity_policy.container_instances_pull": {
            "compartment_id": TENANCY,
            "statements": [
                f"Allow dynamic-group {group_name} to read repos in compartment id "
                f"{COMPARTMENT} where target.repo.name = '{repository_name}'"
            ],
        },
        "oci_budget_budget.sandbox": {
            "compartment_id": TENANCY,
            "targets": [COMPARTMENT],
        },
        "oci_budget_alert_rule.actual": {},
    }
    configuration_expressions = {
        "oci_artifacts_container_repository.api": {
            "display_name": {"references": ["var.repository_name"]}
        },
        "oci_identity_dynamic_group.container_instances": {
            "matching_rule": {"references": ["var.compartment_id"]}
        },
        "oci_identity_policy.container_instances_pull": {
            "statements": {
                "references": [
                    "oci_identity_dynamic_group.container_instances.name",
                    "var.compartment_id",
                    "var.repository_name",
                ]
            }
        },
        "oci_budget_budget.sandbox": {
            "targets": {"references": ["var.compartment_id"]}
        },
        "oci_budget_alert_rule.actual": {
            "budget_id": {"references": ["oci_budget_budget.sandbox.id"]}
        },
    }
    configuration_resources = [
        {
            "address": address,
            "mode": "managed",
            "type": resource_type,
            "provider_config_key": (
                "oci.target"
                if address == "oci_artifacts_container_repository.api"
                else "oci"
            ),
            "expressions": configuration_expressions[address],
        }
        for address, resource_type in sorted(FOUNDERCTL.BOOTSTRAP_ADDRESS_TYPES.items())
    ]
    return {
        "format_version": "1.2",
        "terraform_version": FOUNDERCTL.TERRAFORM_VERSION,
        "variables": {name: {"value": value} for name, value in variables.items()},
        "configuration": {
            "provider_config": {
                "oci": {
                    "name": "oci",
                    "full_name": "registry.terraform.io/oracle/oci",
                    "expressions": {
                        "config_file_profile": {"references": ["var.oci_profile"]},
                        "region": {"references": ["var.home_region"]},
                    },
                },
                "oci.target": {
                    "name": "oci",
                    "full_name": "registry.terraform.io/oracle/oci",
                    "alias": "target",
                    "expressions": {
                        "config_file_profile": {"references": ["var.oci_profile"]},
                        "region": {"references": ["var.target_region"]},
                    },
                },
            },
            "root_module": {
                "resources": configuration_resources,
                "outputs": {
                    "repository_path": {
                        "expression": {
                            "references": [
                                "var.ocir_registry_endpoint",
                                "oci_artifacts_container_repository.api.namespace",
                                "oci_artifacts_container_repository.api.display_name",
                            ]
                        }
                    }
                },
            },
        },
        "resource_changes": [
            {
                "address": address,
                "mode": "managed",
                "type": resource_type,
                "change": {
                    "actions": ["create"],
                    "before": None,
                    "after": after_values[address],
                    "after_unknown": {},
                    "before_sensitive": False,
                    "after_sensitive": False,
                },
            }
            for address, resource_type in sorted(FOUNDERCTL.BOOTSTRAP_ADDRESS_TYPES.items())
        ],
        "output_changes": {
            name: {
                "actions": ["create"],
                "before": None,
                "after": "redacted-by-summary",
                "after_unknown": True,
                "before_sensitive": False,
                "after_sensitive": False,
            }
            for name in FOUNDERCTL.RECEIPT_OUTPUT_KEYS["bootstrap"]
        },
        "resource_drift": [],
    }


def build_bootstrap_state_show() -> dict:
    repository_name = "founder-api/api"
    group_name = (
        "founder-api-ci-"
        f"{hashlib.sha256(COMPARTMENT.encode('utf-8')).hexdigest()[:8]}"
    )
    resource_ids = {
        address: fake_ocid(address) for address in FOUNDERCTL.BOOTSTRAP_ADDRESS_TYPES
    }
    resources = []
    for address, resource_type in sorted(FOUNDERCTL.BOOTSTRAP_ADDRESS_TYPES.items()):
        values = {"id": resource_ids[address]}
        if address != "oci_budget_alert_rule.actual":
            values["compartment_id"] = (
                COMPARTMENT
                if address == "oci_artifacts_container_repository.api"
                else TENANCY
            )
        if address == "oci_budget_budget.sandbox":
            values["targets"] = [COMPARTMENT]
        if address == "oci_budget_alert_rule.actual":
            values["budget_id"] = resource_ids["oci_budget_budget.sandbox"]
        if address == "oci_artifacts_container_repository.api":
            values.update(
                {
                    "namespace": "test",
                    "display_name": repository_name,
                    "is_public": False,
                    "is_immutable": True,
                }
            )
        elif address == "oci_identity_dynamic_group.container_instances":
            values["matching_rule"] = (
                "ALL {resource.type='computecontainerinstance', "
                f"resource.compartment.id='{COMPARTMENT}'}}"
            )
        elif address == "oci_identity_policy.container_instances_pull":
            values["statements"] = [
                f"Allow dynamic-group {group_name} to read repos in compartment id "
                f"{COMPARTMENT} where target.repo.name = '{repository_name}'"
            ]
        resources.append(
            {
                "address": address,
                "mode": "managed",
                "type": resource_type,
                "values": values,
            }
        )
    output_values = {
        "repository_id": resource_ids["oci_artifacts_container_repository.api"],
        "repository_path": IMAGE.rsplit("@sha256:", 1)[0],
        "dynamic_group_id": resource_ids[
            "oci_identity_dynamic_group.container_instances"
        ],
        "image_pull_policy_id": resource_ids[
            "oci_identity_policy.container_instances_pull"
        ],
        "budget_id": resource_ids["oci_budget_budget.sandbox"],
        "budget_alert_rule_id": resource_ids["oci_budget_alert_rule.actual"],
    }
    return {
        "format_version": "1.0",
        "terraform_version": FOUNDERCTL.TERRAFORM_VERSION,
        "values": {
            "outputs": {
                name: {"sensitive": False, "value": value}
                for name, value in output_values.items()
            },
            "root_module": {"resources": resources},
        },
    }


def build_bootstrap_destroy_plan(state: dict, home_region: str) -> dict:
    resources = state["values"]["root_module"]["resources"]
    plan = build_bootstrap_plan()
    plan["variables"]["home_region"]["value"] = home_region
    plan["resource_changes"] = [
        {
            "address": resource["address"],
            "mode": "managed",
            "type": resource["type"],
            "change": {
                "actions": ["delete"],
                "before": copy.deepcopy(resource["values"]),
                "after": None,
                "after_unknown": False,
                "before_sensitive": False,
                "after_sensitive": False,
            },
        }
        for resource in resources
    ]
    plan["output_changes"] = {}
    return plan


def future_expiry() -> str:
    value = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=30)
    return value.replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


class ConfigContractTests(unittest.TestCase):
    def runtime_config(self) -> dict:
        return {
            "tenancy_ocid": "ocid1.tenancy.oc1..fake",
            "compartment_id": "ocid1.compartment.oc1..fake",
            "region": "sa-saopaulo-1",
            "environment_class": "sandbox",
            "project_slug": "founder-api",
            "release_id": "abc1234",
            "owner": "test-team",
            "expires_at": future_expiry(),
            "approved_repository_path": "gru.ocir.io/test/api",
            "container_image_url": "gru.ocir.io/test/api@sha256:" + "a" * 64,
            "availability_domain": "example-prefix:SA-SAOPAULO-1-AD-1",
            "gateway_endpoint_type": "PRIVATE",
            "allowed_ingress_cidrs": ["10.42.0.0/16"],
            "notification_email": "founder@invalid.test",
        }

    def test_valid_runtime_config(self) -> None:
        warnings = FOUNDERCTL.validate_runtime_config(self.runtime_config())
        self.assertTrue(any("single Container Instance" in warning for warning in warnings))

    def test_production_is_rejected(self) -> None:
        config = self.runtime_config()
        config["environment_class"] = "production"
        with self.assertRaises(FOUNDERCTL.ContractError):
            FOUNDERCTL.validate_runtime_config(config)

    def test_mutable_image_is_rejected(self) -> None:
        config = self.runtime_config()
        config["container_image_url"] = "gru.ocir.io/test/api:latest"
        with self.assertRaises(FOUNDERCTL.ContractError):
            FOUNDERCTL.validate_runtime_config(config)

    def test_secret_named_environment_value_is_rejected(self) -> None:
        config = self.runtime_config()
        config["environment_variables"] = {"DATABASE_PASSWORD": "not-recorded"}
        with self.assertRaises(FOUNDERCTL.ContractError):
            FOUNDERCTL.validate_runtime_config(config)

    def test_empty_logging_service_name_is_rejected(self) -> None:
        config = self.runtime_config()
        config["api_gateway_logging_service_name"] = "  "
        with self.assertRaises(FOUNDERCTL.ContractError):
            FOUNDERCTL.validate_runtime_config(config)

    def test_base_image_requires_a_non_placeholder_digest(self) -> None:
        valid = argparse.Namespace(image="python:3.12-slim@sha256:" + "b" * 64)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(FOUNDERCTL.command_image_ref_check(valid), 0)
        with self.assertRaises(FOUNDERCTL.ContractError):
            FOUNDERCTL.command_image_ref_check(argparse.Namespace(image="python:3.12-slim"))


class PlanSummaryTests(unittest.TestCase):
    def summary(self, plan: dict) -> dict:
        return FOUNDERCTL.build_plan_summary(
            plan,
            "b" * 64,
            pathlib.Path("unused.tfplan"),
            "runtime",
            PRINCIPAL,
            TENANCY,
            REGION,
            COMPARTMENT,
            "a" * 64,
            source_evidence=FOUNDERCTL.iac_source_evidence("runtime"),
        )

    def test_summary_redacts_values_and_flags_exposure(self) -> None:
        summary = self.summary(build_runtime_plan(public=True))
        serialized = json.dumps(summary, sort_keys=True)
        self.assertNotIn("value-that-must-not-escape", serialized)
        self.assertFalse(summary["blocked"])
        self.assertIn("public_api_gateway", summary["risk_codes"])
        self.assertIn("world_ingress", summary["risk_codes"])
        self.assertEqual(summary["change_counts"]["create"], 26)
        self.assertEqual(summary["change_counts"]["read"], 2)
        self.assertEqual(
            summary["sensitive_change_addresses"],
            ["oci_container_instances_container_instance.api"],
        )

    def test_wrong_target_variable_is_blocked(self) -> None:
        plan = build_runtime_plan()
        plan["variables"]["compartment_id"]["value"] = "ocid1.compartment.oc1..foreign"

        summary = self.summary(plan)

        self.assertTrue(summary["blocked"])
        self.assertIn("plan_target_variable_mismatch", summary["block_reasons"])
        self.assertIsNone(summary["approval_phrase"])

    def test_oci_profile_is_bound_and_provider_auth_override_is_blocked(self) -> None:
        profile_plan = build_runtime_plan()
        profile_plan["variables"]["oci_profile"]["value"] = "ADMIN"
        profile_summary = self.summary(profile_plan)
        self.assertIn("plan_target_variable_mismatch", profile_summary["block_reasons"])

        auth_plan = build_runtime_plan()
        auth_plan["configuration"]["provider_config"]["oci"]["expressions"]["auth"] = {
            "constant_value": "InstancePrincipal"
        }
        auth_summary = self.summary(auth_plan)
        self.assertIn("provider_target_binding_mismatch", auth_summary["block_reasons"])

    def test_data_source_must_use_the_reviewed_default_provider(self) -> None:
        plan = build_runtime_plan()
        configured_resource(
            plan, "data.oci_core_services.oracle_services"
        )["provider_config_key"] = "unreviewed"

        summary = self.summary(plan)

        self.assertTrue(summary["blocked"])
        self.assertIn("data_source_provider_binding_mismatch", summary["block_reasons"])

    def test_wrong_resource_compartment_is_blocked(self) -> None:
        plan = build_runtime_plan()
        planned_resource(plan, "oci_apigateway_gateway.api")["change"]["after"][
            "compartment_id"
        ] = "ocid1.compartment.oc1..foreign"

        summary = self.summary(plan)

        self.assertTrue(summary["blocked"])
        self.assertIn("resource_compartment_mismatch", summary["block_reasons"])

    def test_partial_managed_resource_plan_is_blocked(self) -> None:
        plan = build_runtime_plan()
        plan["resource_changes"] = [
            change
            for change in plan["resource_changes"]
            if change["address"] != "oci_monitoring_alarm.high_memory"
        ]

        summary = self.summary(plan)

        self.assertTrue(summary["blocked"])
        self.assertIn("incomplete_or_unexpected_resource_set", summary["block_reasons"])

    def test_unsafe_app_route_is_blocked(self) -> None:
        plan = build_runtime_plan()
        route_table = planned_resource(plan, "oci_core_route_table.app")
        route_table["change"]["after"]["route_rules"][0]["destination"] = "0.0.0.0/0"

        summary = self.summary(plan)

        self.assertTrue(summary["blocked"])
        self.assertIn("unexpected_app_route_table", summary["block_reasons"])

    def test_unsafe_api_deployment_route_is_blocked(self) -> None:
        plan = build_runtime_plan()
        deployment = planned_resource(plan, "oci_apigateway_deployment.api")
        deployment["change"]["after"]["specification"][0]["routes"][1]["backend"][0][
            "url"
        ] = "http://203.0.113.10:8080/admin"

        summary = self.summary(plan)

        self.assertTrue(summary["blocked"])
        self.assertIn("api_deployment_route_contract_mismatch", summary["block_reasons"])

    def test_unsafe_backend_nsg_port_is_blocked(self) -> None:
        plan = build_runtime_plan()
        rule = planned_resource(
            plan, "oci_core_network_security_group_security_rule.gateway_to_app"
        )
        port_range = rule["change"]["after"]["tcp_options"][0][
            "destination_port_range"
        ][0]
        port_range.update({"min": 9999, "max": 9999})

        summary = self.summary(plan)

        self.assertTrue(summary["blocked"])
        self.assertIn("unexpected_backend_port", summary["block_reasons"])

    def test_nested_reference_must_be_on_the_exact_vnic_field(self) -> None:
        plan = build_runtime_plan()
        expressions = configured_resource(
            plan, "oci_container_instances_container_instance.api"
        )["expressions"]
        vnic = expressions["vnics"][0]
        vnic["subnet_id"], vnic["nsg_ids"] = vnic["nsg_ids"], vnic["subnet_id"]

        summary = self.summary(plan)

        self.assertTrue(summary["blocked"])
        self.assertIn("container_vnic_reference_mismatch", summary["block_reasons"])

    def test_extra_nested_topology_references_are_blocked(self) -> None:
        cases = (
            (
                "oci_container_instances_container_instance.api",
                ("vnics", 0, "subnet_id", "references"),
                "oci_core_subnet.gateway.id",
                "container_vnic_reference_mismatch",
            ),
            (
                "oci_core_route_table.app",
                ("route_rules", 0, "network_entity_id", "references"),
                "oci_core_internet_gateway.public.id",
                "app_route_gateway_reference_mismatch",
            ),
            (
                "oci_core_service_gateway.oracle_services",
                ("services", 0, "service_id", "references"),
                "oci_core_service_gateway.oracle_services.id",
                "service_gateway_reference_mismatch",
            ),
        )
        for address, path, extra_reference, expected_reason in cases:
            with self.subTest(address=address):
                plan = build_runtime_plan()
                expressions = configured_resource(plan, address)["expressions"]
                references = nested_value(expressions, *path)
                self.assertIsInstance(references, list)
                references.append(extra_reference)

                summary = self.summary(plan)

                self.assertTrue(summary["blocked"])
                self.assertIn(expected_reason, summary["block_reasons"])

    def test_known_foreign_relationship_values_are_blocked_before_apply(self) -> None:
        cases = (
            (
                True,
                "oci_apigateway_gateway.api",
                ("network_security_group_ids",),
                [fake_ocid("foreign-gateway-nsg")],
                "planned_gateway_nsg_relationship_mismatch",
            ),
            (
                True,
                "oci_core_route_table.gateway",
                ("route_rules", 0, "network_entity_id"),
                fake_ocid("foreign-drg"),
                "planned_gateway_route_relationship_mismatch",
            ),
            (
                False,
                "oci_logging_log.gateway_access",
                ("configuration", 0, "source", 0, "resource"),
                fake_ocid("foreign-deployment"),
                "planned_logging_source_relationship_mismatch",
            ),
        )
        for public, address, path, foreign_value, expected_reason in cases:
            with self.subTest(address=address, path=path):
                plan = build_runtime_plan(public=public)
                resource = planned_resource(plan, address)["change"]["after"]
                parent = nested_value(resource, *path[:-1])
                self.assertIsInstance(parent, (dict, list))
                parent[path[-1]] = foreign_value

                summary = self.summary(plan)

                self.assertTrue(summary["blocked"])
                self.assertIn(expected_reason, summary["block_reasons"])

    def test_observability_leaf_reference_and_operational_values_are_blocked(self) -> None:
        plan = build_runtime_plan()
        log = planned_resource(plan, "oci_logging_log.gateway_execution")
        log["change"]["after"]["retention_duration"] = 1
        expression = configured_resource(
            plan, "oci_monitoring_alarm.high_cpu"
        )["expressions"]["destinations"]
        expression["references"] = ["oci_ons_notification_topic.foreign.id"]

        summary = self.summary(plan)

        self.assertTrue(summary["blocked"])
        self.assertIn("logging_operational_contract_mismatch", summary["block_reasons"])
        self.assertIn("monitoring_destination_reference_mismatch", summary["block_reasons"])

    def test_approval_binds_the_reviewed_iac_source_manifest(self) -> None:
        summary = self.summary(build_runtime_plan())
        expected_hash, expected_manifest = FOUNDERCTL.iac_source_evidence("runtime")

        self.assertFalse(summary["blocked"])
        self.assertEqual(summary["iac_source_sha256"], expected_hash)
        self.assertEqual(summary["iac_source_manifest"], expected_manifest)
        self.assertIn(expected_hash[:16], summary["approval_phrase"])

    def test_runtime_iam_is_blocked(self) -> None:
        plan = {
            "format_version": "1.2",
            "terraform_version": "1.16.3",
            "resource_changes": [
                {
                    "address": "oci_identity_policy.bad",
                    "mode": "managed",
                    "type": "oci_identity_policy",
                    "change": {
                        "actions": ["create"],
                        "after": {"statements": ["Allow group x to read repos in tenancy"]},
                        "after_unknown": {},
                        "after_sensitive": False,
                    },
                }
            ],
            "output_changes": {},
            "resource_drift": [],
        }
        with tempfile.TemporaryDirectory() as directory:
            plan_path = pathlib.Path(directory) / "plan.json"
            saved = pathlib.Path(directory) / "plan.tfplan"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            saved.write_bytes(b"plan")
            summary = FOUNDERCTL.build_plan_summary(
                plan,
                plan_path,
                saved,
                "runtime",
                "ocid1.user.oc1..fake",
                "ocid1.tenancy.oc1..fake",
                "sa-saopaulo-1",
                "ocid1.compartment.oc1..fake",
                source_evidence=FOUNDERCTL.iac_source_evidence("runtime"),
            )
        self.assertTrue(summary["blocked"])
        self.assertIn("runtime_contains_iam", summary["block_reasons"])
        self.assertIsNone(summary["approval_phrase"])


class BootstrapPlanTests(unittest.TestCase):
    def summary(self, plan: dict) -> dict:
        return FOUNDERCTL.build_plan_summary(
            plan,
            "b" * 64,
            pathlib.Path("unused.tfplan"),
            "bootstrap",
            PRINCIPAL,
            TENANCY,
            REGION,
            COMPARTMENT,
            "a" * 64,
            None,
            "us-ashburn-1",
            source_evidence=FOUNDERCTL.iac_source_evidence("bootstrap"),
        )

    def test_complete_bootstrap_plan_is_approvable(self) -> None:
        summary = self.summary(build_bootstrap_plan())

        self.assertFalse(summary["blocked"])
        self.assertEqual(summary["change_counts"]["create"], 5)
        self.assertEqual(summary["block_reasons"], [])
        self.assertIsNotNone(summary["approval_phrase"])

    def test_repository_path_output_rejects_an_extra_reference(self) -> None:
        plan = build_bootstrap_plan()
        references = plan["configuration"]["root_module"]["outputs"][
            "repository_path"
        ]["expression"]["references"]
        references.append("var.repository_name")

        summary = self.summary(plan)

        self.assertTrue(summary["blocked"])
        self.assertIn(
            "repository_path_output_reference_mismatch", summary["block_reasons"]
        )
        self.assertIsNone(summary["approval_phrase"])


class SavedPlanSourceEvidenceTests(unittest.TestCase):
    def test_saved_plan_embedded_sources_match_reviewed_stack(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            saved_plan = pathlib.Path(directory) / "runtime.tfplan"
            write_saved_plan_source_fixture(saved_plan, "runtime")

            evidence = FOUNDERCTL.saved_plan_source_evidence(
                saved_plan,
                "runtime",
                FOUNDERCTL.sha256_file(saved_plan),
            )

        self.assertEqual(evidence, FOUNDERCTL.iac_source_evidence("runtime"))

    def test_saved_plan_rejects_modified_or_extra_embedded_sources(self) -> None:
        cases = (
            {"tampered_source": "network.tf"},
            {"extra_source": True},
        )
        for options in cases:
            with self.subTest(options=options), tempfile.TemporaryDirectory() as directory:
                saved_plan = pathlib.Path(directory) / "runtime.tfplan"
                write_saved_plan_source_fixture(saved_plan, "runtime", **options)

                with self.assertRaisesRegex(
                    FOUNDERCTL.ContractError, "source snapshot"
                ):
                    FOUNDERCTL.saved_plan_source_evidence(
                        saved_plan,
                        "runtime",
                        FOUNDERCTL.sha256_file(saved_plan),
                    )

    def test_unknown_relationship_cannot_hide_modified_plan_sources(self) -> None:
        plan = build_runtime_plan(public=True)
        route = planned_resource(plan, "oci_core_route_table.gateway")
        route["change"]["after"]["route_rules"][0]["network_entity_id"] = None
        with tempfile.TemporaryDirectory() as directory:
            saved_plan = pathlib.Path(directory) / "runtime.tfplan"
            write_saved_plan_source_fixture(
                saved_plan, "runtime", tampered_source="network.tf"
            )

            with self.assertRaisesRegex(
                FOUNDERCTL.ContractError, "source snapshot"
            ):
                FOUNDERCTL.build_plan_summary(
                    plan,
                    "b" * 64,
                    saved_plan,
                    "runtime",
                    PRINCIPAL,
                    TENANCY,
                    REGION,
                    COMPARTMENT,
                    FOUNDERCTL.sha256_file(saved_plan),
                )


class ReceiptAndTeardownTests(unittest.TestCase):
    def setUp(self) -> None:
        self.saved_plan_source_patcher = mock.patch.object(
            FOUNDERCTL,
            "saved_plan_source_evidence",
            side_effect=lambda _path, stack, _expected_hash: FOUNDERCTL.iac_source_evidence(
                stack
            ),
        )
        self.saved_plan_source_patcher.start()
        self.addCleanup(self.saved_plan_source_patcher.stop)

    def target(self) -> dict:
        target = {
            "principal": PRINCIPAL,
            "tenancy": TENANCY,
            "region": REGION,
            "compartment": COMPARTMENT,
            "oci_profile": OCI_PROFILE,
        }
        target["fingerprint"] = FOUNDERCTL.fingerprint(
            target["principal"],
            target["tenancy"],
            target["region"],
            target["compartment"],
            None,
            target["oci_profile"],
        )
        return target

    def bootstrap_receipt(self, target: dict) -> dict:
        state = build_bootstrap_state_show()
        outputs, addresses, _data, resource_ids = FOUNDERCTL.state_snapshot_evidence(
            state, "bootstrap", TENANCY, COMPARTMENT
        )
        bootstrap_target = {**target, "home_region": "us-ashburn-1"}
        bootstrap_target["fingerprint"] = FOUNDERCTL.fingerprint(
            bootstrap_target["principal"],
            bootstrap_target["tenancy"],
            bootstrap_target["region"],
            bootstrap_target["compartment"],
            bootstrap_target["home_region"],
            bootstrap_target["oci_profile"],
        )
        return {
            "schema_version": FOUNDERCTL.SCHEMA_VERSION,
            "artifact": "deployment-receipt",
            "status": "locally_verified",
            "layer": "bootstrap",
            "blueprint_version": FOUNDERCTL.BLUEPRINT_VERSION,
            "environment_class": "sandbox",
            "target": bootstrap_target,
            "outputs": outputs,
            "repository_contract": {
                "registry_endpoint": "gru.ocir.io",
                "namespace": "test",
                "display_name": "founder-api/api",
            },
            "state_addresses": addresses,
            "state": {
                "lineage": "bootstrap-lineage-0001",
                "serial": 4,
                "snapshot_sha256": "9" * 64,
                "resource_ids": resource_ids,
            },
        }

    def runtime_receipt(self, target: dict, state: dict) -> dict:
        outputs, addresses, data, resource_ids = FOUNDERCTL.state_snapshot_evidence(
            state, "runtime", TENANCY, COMPARTMENT
        )
        return {
            "schema_version": FOUNDERCTL.SCHEMA_VERSION,
            "artifact": "deployment-receipt",
            "status": "locally_verified",
            "layer": "runtime",
            "blueprint_version": FOUNDERCTL.BLUEPRINT_VERSION,
            "environment_class": "sandbox",
            "target": target,
            "outputs": outputs,
            "state_addresses": addresses,
            "observed_data_source_count": len(data),
            "state": {
                "lineage": "runtime-lineage-0001",
                "serial": 10,
                "snapshot_sha256": "8" * 64,
                "resource_ids": resource_ids,
            },
        }

    def test_runtime_destroy_readback_evidence_binds_exact_receipt_and_state(self) -> None:
        runtime_receipt = self.runtime_receipt(self.target(), build_runtime_state_show())
        with tempfile.TemporaryDirectory() as directory:
            work = pathlib.Path(directory)
            receipt_path = work / "runtime-receipt.json"
            evidence_path = work / "runtime-destroy-evidence.json"
            receipt_path.write_text(json.dumps(runtime_receipt), encoding="utf-8")
            evidence = build_runtime_destroy_evidence(
                receipt_path,
                runtime_receipt,
                "runtime-lineage-0001",
                11,
            )
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")

            evidence_hash = FOUNDERCTL.validate_runtime_destroy_evidence(
                evidence_path,
                receipt_path,
                runtime_receipt,
                runtime_receipt["target"]["fingerprint"],
                "runtime-lineage-0001",
                11,
            )

            self.assertEqual(evidence_hash, FOUNDERCTL.sha256_file(evidence_path))
            expected_readbacks = dict(runtime_receipt["state"]["resource_ids"])
            for address, output_name in FOUNDERCTL.RUNTIME_CHILD_READBACK_OUTPUTS.items():
                expected_readbacks[address] = runtime_receipt["outputs"][output_name]
            self.assertEqual(
                {check["address"]: check["resource_id"] for check in evidence["checks"]},
                expected_readbacks,
            )
            self.assertTrue(
                all(check["result"] == "not_found" for check in evidence["checks"])
            )

    def test_runtime_destroy_readback_evidence_rejects_wrong_resource_id(self) -> None:
        runtime_receipt = self.runtime_receipt(self.target(), build_runtime_state_show())
        with tempfile.TemporaryDirectory() as directory:
            work = pathlib.Path(directory)
            receipt_path = work / "runtime-receipt.json"
            evidence_path = work / "runtime-destroy-evidence.json"
            receipt_path.write_text(json.dumps(runtime_receipt), encoding="utf-8")
            evidence = build_runtime_destroy_evidence(
                receipt_path,
                runtime_receipt,
                "runtime-lineage-0001",
                11,
            )
            evidence["checks"][0]["resource_id"] = fake_ocid("wrong-destroy-target")
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")

            with self.assertRaises(FOUNDERCTL.ContractError):
                FOUNDERCTL.validate_runtime_destroy_evidence(
                    evidence_path,
                    receipt_path,
                    runtime_receipt,
                    runtime_receipt["target"]["fingerprint"],
                    "runtime-lineage-0001",
                    11,
                )

    def test_runtime_destroy_readback_evidence_requires_child_resources(self) -> None:
        runtime_receipt = self.runtime_receipt(self.target(), build_runtime_state_show())
        with tempfile.TemporaryDirectory() as directory:
            work = pathlib.Path(directory)
            receipt_path = work / "runtime-receipt.json"
            evidence_path = work / "runtime-destroy-evidence.json"
            receipt_path.write_text(json.dumps(runtime_receipt), encoding="utf-8")
            evidence = build_runtime_destroy_evidence(
                receipt_path,
                runtime_receipt,
                "runtime-lineage-0001",
                11,
            )
            evidence["checks"] = [
                check
                for check in evidence["checks"]
                if check["address"]
                != "oci_container_instances_container_instance.api#container"
            ]
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")

            with self.assertRaisesRegex(
                FOUNDERCTL.ContractError, "incomplete check set"
            ):
                FOUNDERCTL.validate_runtime_destroy_evidence(
                    evidence_path,
                    receipt_path,
                    runtime_receipt,
                    runtime_receipt["target"]["fingerprint"],
                    "runtime-lineage-0001",
                    11,
                )

    def test_runtime_destroy_readback_evidence_rejects_binding_tamper(self) -> None:
        runtime_receipt = self.runtime_receipt(self.target(), build_runtime_state_show())
        with tempfile.TemporaryDirectory() as directory:
            work = pathlib.Path(directory)
            receipt_path = work / "runtime-receipt.json"
            evidence_path = work / "runtime-destroy-evidence.json"
            receipt_path.write_text(json.dumps(runtime_receipt), encoding="utf-8")
            valid_evidence = build_runtime_destroy_evidence(
                receipt_path,
                runtime_receipt,
                "runtime-lineage-0001",
                11,
            )
            cases = (
                ("runtime_receipt_sha256", "0" * 64),
                ("state_lineage", "different-runtime-lineage"),
                ("state_serial", 12),
            )
            for field, tampered_value in cases:
                with self.subTest(field=field):
                    evidence = copy.deepcopy(valid_evidence)
                    evidence[field] = tampered_value
                    evidence_path.write_text(json.dumps(evidence), encoding="utf-8")

                    with self.assertRaises(FOUNDERCTL.ContractError):
                        FOUNDERCTL.validate_runtime_destroy_evidence(
                            evidence_path,
                            receipt_path,
                            runtime_receipt,
                            runtime_receipt["target"]["fingerprint"],
                            "runtime-lineage-0001",
                            11,
                        )

    def test_bootstrap_teardown_accepts_exact_runtime_destroy_readback(self) -> None:
        target = self.target()
        bootstrap_receipt = self.bootstrap_receipt(target)
        bootstrap_state = build_bootstrap_state_show()
        destroy_plan = build_bootstrap_destroy_plan(
            bootstrap_state, bootstrap_receipt["target"]["home_region"]
        )
        runtime_state = build_runtime_state_show()
        runtime_receipt = self.runtime_receipt(target, runtime_state)
        post_destroy_state = build_empty_state_show()
        with tempfile.TemporaryDirectory() as directory:
            work = pathlib.Path(directory)
            bootstrap_receipt_path = work / "bootstrap-receipt.json"
            bootstrap_state_path = work / "bootstrap.tfstate"
            saved_path = work / "destroy.tfplan"
            runtime_receipt_path = work / "runtime-receipt.json"
            runtime_state_path = work / "runtime-post-destroy.tfstate"
            evidence_path = work / "runtime-destroy-evidence.json"
            report_path = work / "audit.json"
            bootstrap_receipt_path.write_text(
                json.dumps(bootstrap_receipt), encoding="utf-8"
            )
            bootstrap_state_path.write_text("{}", encoding="utf-8")
            saved_path.write_bytes(b"destroy")
            runtime_state_path.write_text("{}", encoding="utf-8")
            runtime_receipt["bootstrap_receipt_sha256"] = FOUNDERCTL.sha256_file(
                bootstrap_receipt_path
            )
            runtime_receipt_path.write_text(
                json.dumps(runtime_receipt), encoding="utf-8"
            )
            evidence = build_runtime_destroy_evidence(
                runtime_receipt_path,
                runtime_receipt,
                "runtime-lineage-0001",
                11,
            )
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            evidence_hash = FOUNDERCTL.sha256_file(evidence_path)
            bootstrap_target = bootstrap_receipt["target"]
            args = argparse.Namespace(
                receipt=str(bootstrap_receipt_path),
                saved_plan=str(saved_path),
                terraform_bin="terraform-for-test",
                state=str(bootstrap_state_path),
                principal=bootstrap_target["principal"],
                tenancy=bootstrap_target["tenancy"],
                region=bootstrap_target["region"],
                home_region=bootstrap_target["home_region"],
                oci_profile=bootstrap_target["oci_profile"],
                compartment=bootstrap_target["compartment"],
                runtime_receipt=str(runtime_receipt_path),
                runtime_state=str(runtime_state_path),
                runtime_destroy_evidence=str(evidence_path),
                out=str(report_path),
            )
            with mock.patch.object(
                FOUNDERCTL,
                "decode_saved_plan",
                return_value=(destroy_plan, "e" * 64, "f" * 64),
            ), mock.patch.object(
                FOUNDERCTL,
                "decode_saved_state",
                side_effect=(
                    (
                        bootstrap_state,
                        "9" * 64,
                        "bootstrap-lineage-0001",
                        4,
                    ),
                    (
                        post_destroy_state,
                        "7" * 64,
                        "runtime-lineage-0001",
                        11,
                    ),
                ),
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(FOUNDERCTL.command_teardown_audit(args), 0)

            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertTrue(report["ready_for_destroy"])
            self.assertEqual(
                report["runtime_destroy_evidence_sha256"], evidence_hash
            )
            self.assertEqual(
                report["approval_phrase"],
                f"DESTROY BOOTSTRAP {bootstrap_target['fingerprint']} "
                f"{'f' * 16} {'e' * 16} "
                f"{FOUNDERCTL.iac_source_evidence('bootstrap')[0][:16]} "
                f"{FOUNDERCTL.sha256_file(bootstrap_receipt_path)[:16]} "
                f"{'9' * 16} {evidence_hash[:16]}",
            )

    def test_complete_bootstrap_plan_produces_repository_bound_receipt(self) -> None:
        plan = build_bootstrap_plan()
        state = build_bootstrap_state_show()
        with tempfile.TemporaryDirectory() as directory:
            work = pathlib.Path(directory)
            summary_path = work / "summary.json"
            lock_path = work / ".terraform.lock.hcl"
            saved_path = work / "bootstrap.tfplan"
            state_path = work / "bootstrap.tfstate"
            receipt_path = work / "receipt.json"
            lock_path.write_bytes(
                (ROOT / "terraform/bootstrap/.terraform.lock.hcl").read_bytes()
            )
            saved_path.write_bytes(b"opaque bootstrap plan")
            state_path.write_text("{}", encoding="utf-8")
            summary = FOUNDERCTL.build_plan_summary(
                plan,
                "b" * 64,
                saved_path,
                "bootstrap",
                PRINCIPAL,
                TENANCY,
                REGION,
                COMPARTMENT,
                "a" * 64,
                None,
                "us-ashburn-1",
                source_evidence=FOUNDERCTL.iac_source_evidence("bootstrap"),
            )
            summary_path.write_text(json.dumps(summary), encoding="utf-8")
            args = argparse.Namespace(
                layer="bootstrap",
                summary=str(summary_path),
                saved_plan=str(saved_path),
                terraform_bin="terraform-for-test",
                state=str(state_path),
                provider_lock=str(lock_path),
                source_revision="abc1234",
                iac_revision="def5678",
                smoke=None,
                bootstrap_receipt=None,
                previous_image_url=None,
                out=str(receipt_path),
            )
            with mock.patch.object(
                FOUNDERCTL,
                "decode_saved_plan",
                return_value=(plan, "b" * 64, "a" * 64),
            ), mock.patch.object(
                FOUNDERCTL,
                "decode_saved_state",
                return_value=(state, "9" * 64, "bootstrap-lineage-0001", 4),
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(FOUNDERCTL.command_receipt(args), 0)

            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(
                receipt["repository_contract"],
                {
                    "registry_endpoint": "gru.ocir.io",
                    "namespace": "test",
                    "display_name": "founder-api/api",
                },
            )
            self.assertEqual(
                receipt["outputs"]["repository_path"],
                "gru.ocir.io/test/founder-api/api",
            )

    def test_bootstrap_receipt_rejects_malicious_repository_path(self) -> None:
        plan = build_bootstrap_plan()
        state = build_bootstrap_state_show()
        state["values"]["outputs"]["repository_path"]["value"] = (
            "attacker.invalid/test/founder-api/api"
        )
        with tempfile.TemporaryDirectory() as directory:
            work = pathlib.Path(directory)
            summary_path = work / "summary.json"
            lock_path = work / ".terraform.lock.hcl"
            saved_path = work / "bootstrap.tfplan"
            state_path = work / "bootstrap.tfstate"
            receipt_path = work / "receipt.json"
            lock_path.write_bytes(
                (ROOT / "terraform/bootstrap/.terraform.lock.hcl").read_bytes()
            )
            saved_path.write_bytes(b"opaque bootstrap plan")
            state_path.write_text("{}", encoding="utf-8")
            summary = FOUNDERCTL.build_plan_summary(
                plan,
                "b" * 64,
                saved_path,
                "bootstrap",
                PRINCIPAL,
                TENANCY,
                REGION,
                COMPARTMENT,
                "a" * 64,
                None,
                "us-ashburn-1",
                source_evidence=FOUNDERCTL.iac_source_evidence("bootstrap"),
            )
            summary_path.write_text(json.dumps(summary), encoding="utf-8")
            args = argparse.Namespace(
                layer="bootstrap",
                summary=str(summary_path),
                saved_plan=str(saved_path),
                terraform_bin="terraform-for-test",
                state=str(state_path),
                provider_lock=str(lock_path),
                source_revision="abc1234",
                iac_revision="def5678",
                smoke=None,
                bootstrap_receipt=None,
                previous_image_url=None,
                out=str(receipt_path),
            )
            with mock.patch.object(
                FOUNDERCTL,
                "decode_saved_plan",
                return_value=(plan, "b" * 64, "a" * 64),
            ), mock.patch.object(
                FOUNDERCTL,
                "decode_saved_state",
                return_value=(state, "9" * 64, "bootstrap-lineage-0001", 4),
            ), self.assertRaises(FOUNDERCTL.ContractError):
                FOUNDERCTL.command_receipt(args)

            self.assertFalse(receipt_path.exists())

    def test_receipt_then_exact_teardown(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            work = pathlib.Path(directory)
            summary_path = work / "summary.json"
            lock_path = work / ".terraform.lock.hcl"
            receipt_path = work / "receipt.json"
            bootstrap_path = work / "bootstrap-receipt.json"
            smoke_path = work / "smoke.json"
            saved = work / "runtime.tfplan"
            state_path = work / "runtime.tfstate"
            destroy_saved = work / "destroy.tfplan"
            report_path = work / "teardown.json"
            lock_path.write_bytes(
                (ROOT / "terraform/runtime/.terraform.lock.hcl").read_bytes()
            )
            saved.write_bytes(b"opaque runtime plan")
            state_path.write_text("{}", encoding="utf-8")
            destroy_saved.write_bytes(b"opaque destroy plan")
            target = self.target()
            bootstrap = self.bootstrap_receipt(target)
            bootstrap_path.write_text(json.dumps(bootstrap), encoding="utf-8")
            bootstrap_hash = FOUNDERCTL.sha256_file(bootstrap_path)
            plan = build_runtime_plan()
            summary = FOUNDERCTL.build_plan_summary(
                plan,
                "b" * 64,
                saved,
                "runtime",
                target["principal"],
                target["tenancy"],
                target["region"],
                target["compartment"],
                "a" * 64,
                bootstrap_hash,
                source_evidence=FOUNDERCTL.iac_source_evidence("runtime"),
            )
            summary_path.write_text(json.dumps(summary), encoding="utf-8")
            state = build_runtime_state_show()
            state_outputs, _addresses, _data, _ids = FOUNDERCTL.state_snapshot_evidence(
                state, "runtime", TENANCY, COMPARTMENT
            )
            smoke = json.loads((FIXTURES / "smoke-result.json").read_text(encoding="utf-8"))
            smoke["generated_at"] = FOUNDERCTL.iso_now()
            smoke["url_sha256"] = hashlib.sha256(
                state_outputs["healthcheck_url"].encode("utf-8")
            ).hexdigest()
            smoke_path.write_text(json.dumps(smoke), encoding="utf-8")
            receipt_args = argparse.Namespace(
                layer="runtime",
                summary=str(summary_path),
                saved_plan=str(saved),
                terraform_bin="terraform-for-test",
                state=str(state_path),
                provider_lock=str(lock_path),
                source_revision="abc1234",
                iac_revision="def5678",
                smoke=str(smoke_path),
                bootstrap_receipt=str(bootstrap_path),
                previous_image_url=None,
                out=str(receipt_path),
            )
            with mock.patch.object(
                FOUNDERCTL,
                "decode_saved_plan",
                return_value=(plan, "b" * 64, "a" * 64),
            ), mock.patch.object(
                FOUNDERCTL,
                "decode_saved_state",
                return_value=(state, "8" * 64, "runtime-lineage-0001", 10),
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(FOUNDERCTL.command_receipt(receipt_args), 0)
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["status"], "locally_verified")
            self.assertNotIn("notification_email", json.dumps(receipt))
            self.assertEqual(receipt["observed_data_source_count"], 2)
            self.assertTrue(all(not item.startswith("data.") for item in receipt["state_addresses"]))
            self.assertEqual(receipt["state"]["lineage"], "runtime-lineage-0001")
            self.assertEqual(
                receipt["state"]["resource_ids"]["oci_apigateway_gateway.api"],
                state_outputs["gateway_id"],
            )

            bad_smoke = dict(smoke)
            bad_smoke["url_sha256"] = "0" * 64
            smoke_path.write_text(json.dumps(bad_smoke), encoding="utf-8")
            with mock.patch.object(
                FOUNDERCTL,
                "decode_saved_plan",
                return_value=(plan, "b" * 64, "a" * 64),
            ), mock.patch.object(
                FOUNDERCTL,
                "decode_saved_state",
                return_value=(state, "8" * 64, "runtime-lineage-0001", 10),
            ), self.assertRaises(FOUNDERCTL.ContractError):
                FOUNDERCTL.command_receipt(receipt_args)

            destroy_plan = build_runtime_destroy_plan(state)
            teardown_args = argparse.Namespace(
                receipt=str(receipt_path),
                saved_plan=str(destroy_saved),
                terraform_bin="terraform-for-test",
                state=str(state_path),
                principal=target["principal"],
                tenancy=target["tenancy"],
                region=target["region"],
                home_region=None,
                oci_profile=target["oci_profile"],
                compartment=target["compartment"],
                runtime_receipt=None,
                runtime_state=None,
                out=str(report_path),
            )
            with mock.patch.object(
                FOUNDERCTL,
                "decode_saved_plan",
                return_value=(destroy_plan, "c" * 64, "d" * 64),
            ), mock.patch.object(
                FOUNDERCTL,
                "decode_saved_state",
                return_value=(state, "8" * 64, "runtime-lineage-0001", 10),
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(FOUNDERCTL.command_teardown_audit(teardown_args), 0)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertTrue(report["ready_for_destroy"])
            self.assertEqual(report["observed_data_source_count"], 2)
            self.assertIn(FOUNDERCTL.sha256_file(receipt_path)[:16], report["approval_phrase"])
            self.assertIn(("8" * 64)[:16], report["approval_phrase"])

    def test_state_security_change_is_rejected_even_when_address_is_unchanged(self) -> None:
        plan = build_runtime_plan()
        state = build_runtime_state_show()
        ingress = next(
            resource
            for resource in state["values"]["root_module"]["resources"]
            if FOUNDERCTL.GATEWAY_INGRESS_ADDRESS_RE.fullmatch(resource["address"])
        )
        ingress["values"]["source"] = "0.0.0.0/0"

        with self.assertRaisesRegex(
            FOUNDERCTL.ContractError,
            "applied state violates the reviewed security contract",
        ):
            FOUNDERCTL.validate_state_security_contract(
                state,
                plan,
                "runtime",
                TENANCY,
                REGION,
                COMPARTMENT,
                None,
            )

    def test_state_observability_relationship_change_is_rejected(self) -> None:
        plan = build_runtime_plan()
        state = build_runtime_state_show()
        log = next(
            resource
            for resource in state["values"]["root_module"]["resources"]
            if resource["address"] == "oci_logging_log.gateway_access"
        )
        log["values"]["configuration"][0]["source"][0]["resource"] = fake_ocid(
            "foreign-deployment"
        )

        with self.assertRaisesRegex(
            FOUNDERCTL.ContractError,
            "applied state violates the reviewed resource relationship contract",
        ):
            FOUNDERCTL.validate_state_security_contract(
                state,
                plan,
                "runtime",
                TENANCY,
                REGION,
                COMPARTMENT,
                None,
            )

    def test_receipt_rejects_state_ingress_not_reviewed_in_plan(self) -> None:
        target = self.target()
        bootstrap = self.bootstrap_receipt(target)
        plan = build_runtime_plan()
        state = build_runtime_state_show()
        ingress = next(
            resource
            for resource in state["values"]["root_module"]["resources"]
            if FOUNDERCTL.GATEWAY_INGRESS_ADDRESS_RE.fullmatch(resource["address"])
        )
        ingress["address"] = (
            'oci_core_network_security_group_security_rule.gateway_https_ingress'
            '["192.0.2.0/24"]'
        )
        ingress["values"]["source"] = "192.0.2.0/24"

        with tempfile.TemporaryDirectory() as directory:
            work = pathlib.Path(directory)
            bootstrap_path = work / "bootstrap-receipt.json"
            summary_path = work / "summary.json"
            saved_path = work / "runtime.tfplan"
            state_path = work / "runtime.tfstate"
            receipt_path = work / "receipt.json"
            bootstrap_path.write_text(json.dumps(bootstrap), encoding="utf-8")
            saved_path.write_bytes(b"opaque runtime plan")
            state_path.write_text("{}", encoding="utf-8")
            bootstrap_hash = FOUNDERCTL.sha256_file(bootstrap_path)
            summary = FOUNDERCTL.build_plan_summary(
                plan,
                "b" * 64,
                saved_path,
                "runtime",
                target["principal"],
                target["tenancy"],
                target["region"],
                target["compartment"],
                "a" * 64,
                bootstrap_hash,
                source_evidence=FOUNDERCTL.iac_source_evidence("runtime"),
            )
            summary_path.write_text(json.dumps(summary), encoding="utf-8")
            args = argparse.Namespace(
                layer="runtime",
                summary=str(summary_path),
                saved_plan=str(saved_path),
                terraform_bin="terraform-for-test",
                state=str(state_path),
                provider_lock=str(work / ".terraform.lock.hcl"),
                source_revision="abc1234",
                iac_revision="def5678",
                smoke=None,
                bootstrap_receipt=str(bootstrap_path),
                previous_image_url=None,
                out=str(receipt_path),
            )
            with mock.patch.object(
                FOUNDERCTL,
                "decode_saved_plan",
                return_value=(plan, "b" * 64, "a" * 64),
            ), mock.patch.object(
                FOUNDERCTL,
                "decode_saved_state",
                return_value=(state, "8" * 64, "runtime-lineage-0001", 10),
            ), self.assertRaisesRegex(
                FOUNDERCTL.ContractError,
                "applied state resource set does not match the reviewed saved plan",
            ):
                FOUNDERCTL.command_receipt(args)

            self.assertFalse(receipt_path.exists())

    def test_teardown_stops_on_target_mismatch(self) -> None:
        target = self.target()
        state = build_runtime_state_show()
        receipt = self.runtime_receipt(
            {**target, "fingerprint": "not-the-current-target"}, state
        )
        destroy_plan = build_runtime_destroy_plan(state)
        with tempfile.TemporaryDirectory() as directory:
            work = pathlib.Path(directory)
            receipt_path = work / "receipt.json"
            state_path = work / "runtime.tfstate"
            saved = work / "destroy.tfplan"
            out = work / "audit.json"
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            state_path.write_text("{}", encoding="utf-8")
            saved.write_bytes(b"destroy")
            args = argparse.Namespace(
                receipt=str(receipt_path),
                saved_plan=str(saved),
                terraform_bin="terraform-for-test",
                state=str(state_path),
                principal=PRINCIPAL,
                tenancy=TENANCY,
                region=REGION,
                home_region=None,
                oci_profile=OCI_PROFILE,
                compartment=COMPARTMENT,
                runtime_receipt=None,
                runtime_state=None,
                out=str(out),
            )
            with mock.patch.object(
                FOUNDERCTL,
                "decode_saved_plan",
                return_value=(destroy_plan, "c" * 64, "d" * 64),
            ), mock.patch.object(
                FOUNDERCTL,
                "decode_saved_state",
                return_value=(state, "8" * 64, "runtime-lineage-0001", 10),
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(FOUNDERCTL.command_teardown_audit(args), 2)
            report = json.loads(out.read_text(encoding="utf-8"))
            self.assertIn("target_fingerprint_mismatch", report["block_reasons"])
            self.assertIsNone(report["approval_phrase"])

    def test_bootstrap_teardown_requires_runtime_destroy_evidence(self) -> None:
        receipt = self.bootstrap_receipt(self.target())
        target = receipt["target"]
        state = build_bootstrap_state_show()
        destroy_plan = build_bootstrap_destroy_plan(state, target["home_region"])
        with tempfile.TemporaryDirectory() as directory:
            work = pathlib.Path(directory)
            receipt_path = work / "receipt.json"
            state_path = work / "bootstrap.tfstate"
            saved_path = work / "destroy.tfplan"
            out_path = work / "audit.json"
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            state_path.write_text("{}", encoding="utf-8")
            saved_path.write_bytes(b"destroy")
            args = argparse.Namespace(
                receipt=str(receipt_path),
                saved_plan=str(saved_path),
                terraform_bin="terraform-for-test",
                state=str(state_path),
                principal=target["principal"],
                tenancy=target["tenancy"],
                region=target["region"],
                home_region=target["home_region"],
                oci_profile=target["oci_profile"],
                compartment=target["compartment"],
                runtime_receipt=None,
                runtime_state=None,
                out=str(out_path),
            )
            with mock.patch.object(
                FOUNDERCTL,
                "decode_saved_plan",
                return_value=(destroy_plan, "e" * 64, "f" * 64),
            ), mock.patch.object(
                FOUNDERCTL,
                "decode_saved_state",
                return_value=(state, "9" * 64, "bootstrap-lineage-0001", 4),
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(FOUNDERCTL.command_teardown_audit(args), 2)
            audit = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertIn("runtime_destroy_evidence_missing", audit["block_reasons"])
            self.assertIsNone(audit["approval_phrase"])

    def test_teardown_rejects_destroy_plan_for_a_different_resource_id(self) -> None:
        target = self.target()
        state = build_runtime_state_show()
        receipt = self.runtime_receipt(target, state)
        destroy_plan = build_runtime_destroy_plan(state)
        planned_resource(destroy_plan, "oci_apigateway_gateway.api")["change"]["before"][
            "id"
        ] = fake_ocid("foreign-gateway")
        with tempfile.TemporaryDirectory() as directory:
            work = pathlib.Path(directory)
            receipt_path = work / "receipt.json"
            state_path = work / "runtime.tfstate"
            saved_path = work / "destroy.tfplan"
            out_path = work / "audit.json"
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            state_path.write_text("{}", encoding="utf-8")
            saved_path.write_bytes(b"destroy")
            args = argparse.Namespace(
                receipt=str(receipt_path),
                saved_plan=str(saved_path),
                terraform_bin="terraform-for-test",
                state=str(state_path),
                principal=target["principal"],
                tenancy=target["tenancy"],
                region=target["region"],
                home_region=None,
                oci_profile=target["oci_profile"],
                compartment=target["compartment"],
                runtime_receipt=None,
                runtime_state=None,
                out=str(out_path),
            )
            with mock.patch.object(
                FOUNDERCTL,
                "decode_saved_plan",
                return_value=(destroy_plan, "c" * 64, "d" * 64),
            ), mock.patch.object(
                FOUNDERCTL,
                "decode_saved_state",
                return_value=(state, "8" * 64, "runtime-lineage-0001", 10),
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(FOUNDERCTL.command_teardown_audit(args), 2)
            audit = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertIn("destroy_plan_resource_id_mismatch", audit["block_reasons"])
            self.assertIsNone(audit["approval_phrase"])


class PrivateArtifactTests(unittest.TestCase):
    def test_atomic_writer_refuses_symlink_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            work = pathlib.Path(directory)
            protected = work / "protected.txt"
            target = work / "result.json"
            protected.write_text("unchanged", encoding="utf-8")
            target.symlink_to(protected)
            with self.assertRaises(FOUNDERCTL.ContractError):
                FOUNDERCTL.write_private_json(target, {"safe": True})
            self.assertEqual(protected.read_text(encoding="utf-8"), "unchanged")

    def test_atomic_writer_refuses_symlinked_parent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            work = pathlib.Path(directory)
            protected_directory = work / "protected"
            linked_directory = work / "linked"
            protected_directory.mkdir()
            linked_directory.symlink_to(protected_directory, target_is_directory=True)

            with self.assertRaises(FOUNDERCTL.ContractError):
                FOUNDERCTL.write_private_json(linked_directory / "result.json", {"safe": True})

            self.assertFalse((protected_directory / "result.json").exists())

            with self.assertRaises(FOUNDERCTL.ContractError):
                FOUNDERCTL.write_private_json(
                    linked_directory / "must-not-exist" / "result.json", {"safe": True}
                )

            self.assertFalse((protected_directory / "must-not-exist").exists())


if __name__ == "__main__":
    unittest.main()
