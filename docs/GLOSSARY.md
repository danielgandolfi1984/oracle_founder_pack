# OCI glossary for founders and backend developers

Use this glossary to orient yourself when an OCI term appears in a plan,
Terraform file, console screen, or agent response. The cross-cloud mappings are
**approximate mental models, not service equivalence**. Identity scope, network
behavior, availability, limits, and pricing still require OCI-specific review.

New to the Console? Follow [Account setup](ACCOUNT-SETUP.md), then the
[First VM lab](FIRST-VM.md). Installing a skill, configuring a CLI identity,
and granting IAM permission are separate steps.

## Account, identity, and location

| OCI term | Plain definition | Approximate cross-cloud mental model | Common trap |
|---|---|---|---|
| **Tenancy** | The account-level OCI security and governance boundary. It contains the compartment hierarchy, IAM configuration, and cloud resources. | Roughly an AWS account, Azure subscription, or the organization/project boundary in GCP, depending on how the other cloud was organized. | Treating the tenancy root as the normal project container or using a tenancy administrator for daily deployment. Start with a dedicated project compartment. |
| **Compartment** | A tenancy-wide logical container used to organize resources and scope access, quotas, and governance. It is not a physical container or a separate billing account. | Some jobs resemble an AWS account or OU, an Azure resource group, or a GCP folder/project. | Assuming a compartment creates network isolation. A VCN, IAM policies, and network rules are separate controls. |
| **Home region** | The region associated with tenancy-wide identity administration and other home-region operations. It need not be the region where an application runs. | No exact equivalent; think of it as the home for part of the account control plane. | Choosing the workload region only because it is the home region, or sending a home-region resource to an arbitrary regional provider. |
| **Region** | A geographic OCI location that contains one or more Availability Domains and offers a region-specific service catalog and capacity pool. | An AWS, Azure, or GCP region. | Assuming every region has the same services, shapes, capacity, limits, or number of Availability Domains. |
| **Availability Domain (AD)** | An isolated data-center grouping inside an OCI region. A region can have one or more ADs. | An AWS Availability Zone, Azure availability zone, or GCP zone. | Hard-coding an AD count or name, or calling a single-AD deployment highly available without reviewing the failure model. |
| **Fault Domain (FD)** | A placement boundary inside an AD that reduces the chance that colocated compute resources fail together during hardware failure or maintenance. | Closest to an Azure fault domain or an AWS placement-group partition; there is no universal match. | Treating FDs as separate data centers or as protection from an AD- or region-wide failure. |
| **Realm** | A collection of OCI regions that shares an isolated cloud domain and endpoint model. Commercial and government environments can be in different realms. | Closest to an AWS partition or an Azure cloud environment. | Hard-coding commercial-realm endpoints, registry hosts, or certificate assumptions into software intended for another realm. |
| **OCID** | The Oracle Cloud Identifier assigned to an OCI resource, such as a tenancy, compartment, VCN, or image. Automation should use the exact OCID when an API expects an identifier. | An AWS ARN, Azure resource ID, or GCP fully qualified resource name. | Using a display name as if it were unique, or pasting real OCIDs into public logs and examples. An OCID is not a password, but it is still environment metadata. |
| **IAM policy** | Rules that authorize a principal to perform particular operations on resources in a defined scope. Authentication establishes identity; a policy determines access. | IAM permissions or role assignments in other clouds. | Assuming a successful login or a known OCID grants permission to create a VM. Use the project scope and permissions required for the reviewed operation. |

See [IAM policy basics](https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/policygetstarted.htm)
and [locating OCIDs](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/apisigningkey.htm).

## Local tools, profiles, and credentials

| Term | What it is for | Common trap |
|---|---|---|
| **OCI CLI** | The local `oci` command-line client that sends OCI API requests. An agent needs an available, authorized execution tool to use it. | Assuming the installed skill includes a CLI, account credentials, or permission to run commands. |
| **CLI profile** | A named configuration section, such as `FOUNDER`, that selects identity settings and a region. | Treating the profile name as a credential, or assuming a local profile also exists in a remote agent's environment. |
| **CLI session token** | A temporary authentication session, commonly created through browser sign-in with `oci session authenticate`. Session-authenticated commands use `--auth security_token`. | Assuming an existing Console login authenticates every terminal, or using an expired session. The generated token and its private key stay local. |
| **API signing key** | A public/private key pair for signing OCI API requests. IAM holds the public key; the configured client uses the private key. | Confusing it with an SSH key. Keep the private key outside Git and chat; a fingerprint identifies the public key, not the permissions granted. |
| **SSH key** | A separate key pair used to log in to a VM's operating system. The VM is configured with the public key; your SSH client uses the private key. | Using the OCI API signing key or Console password as the VM login credential. |
| **OCIR auth token** | A generated credential used for registry login, including Docker authentication to OCIR. | Using the Console password, API signing key, or CLI session token as the registry password. Do not paste the auth token into prompts or commit it. |

Sources: [CLI setup](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm),
[CLI sessions](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/clitoken.htm),
[API signing keys and configuration](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/apisigningkey.htm),
[Linux SSH access](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/connect-to-linux-instance.htm),
and [OCIR auth tokens](https://docs.oracle.com/en-us/iaas/Content/Registry/Tasks/registrygettingauthtoken.htm).

## Networking

| OCI term | Plain definition | Approximate cross-cloud mental model | Common trap |
|---|---|---|---|
| **VCN (Virtual Cloud Network)** | A software-defined network in one OCI region, with CIDR ranges, subnets, route tables, gateways, DNS choices, and security controls. | An AWS or GCP VPC, or an Azure VNet. | Copying a CIDR or route design mechanically from another cloud without checking overlap, regional behavior, service access, and DNS. |
| **CIDR** | Address-range notation such as `10.20.0.0/16`. The suffix describes the network prefix; for IPv4, `/32` identifies one address. | The same IP addressing notation in other clouds. | Copying an example range without checking overlap with existing VCNs, office networks, or a VPN. `0.0.0.0/0` covers all IPv4 addresses, not just your laptop. |
| **Subnet** | An IP address range inside a VCN where VNICs are placed. Its route table and security lists help determine reachability and filtering. | A subnet in AWS, Azure, or GCP. | Assuming the word `public` alone makes a resource internet-reachable. Routes, a gateway, public addressing, and security rules must all agree. |
| **VNIC** | A virtual network interface connecting an instance to a subnet, with IP configuration and applicable network security rules. | An AWS network interface or Azure NIC. | Creating an NSG but never associating the VM's VNIC with it. |
| **Internet Gateway (IGW)** | A VCN gateway used for internet connectivity with the required routes and public addressing. | An AWS Internet Gateway; Azure and GCP expose different public-internet routing models. | Expecting a gateway alone to open SSH or make a private-only VM publicly reachable. |
| **Route table** | Rules that send traffic for a destination range to a target, such as `0.0.0.0/0` to an Internet Gateway for the public lab. | A cloud route table. | Confusing a route to the internet with a firewall rule allowing inbound traffic from the internet. |
| **NSG (Network Security Group)** | A set of ingress and egress rules applied to selected VNICs, which makes it useful for workload-level network policy. | An AWS security group or Azure NSG; GCP firewall targeting is only an approximation. | Treating an NSG as a route or assuming it overrides subnet security lists. Reachability and all applicable controls must be reviewed together. |
| **Security list** | A set of network rules applied at subnet scope to the VNICs in that subnet. | Closest to a subnet network ACL, but the evaluation and statefulness semantics are not equivalent. | Using a broad security list when an NSG would express the workload boundary more narrowly, or assuming one control cancels a rule in the other. |
| **Service Gateway** | A VCN gateway that provides private reachability to supported Oracle services without sending that traffic over the public internet. | Roughly an AWS VPC gateway endpoint, Google Private Access pattern, or Azure service endpoint; the service coverage differs. | Expecting arbitrary private-service or internet access. The target service, route rule, and security rules must support the path. |
| **NAT Gateway** | A gateway that lets resources without public IPs initiate outbound connections to the internet without accepting unsolicited inbound internet connections. | A NAT Gateway in AWS, Azure, or GCP. | Adding NAT for traffic that should use a Service Gateway, or forgetting that routes, egress policy, and gateway traffic can affect cost. |

For the basic lab, NSG and security-list allow rules combine: a narrow SSH rule
in an NSG does not cancel a broad SSH allowance in a subnet security list.
Review both, plus routing and the operating-system firewall. See
[Networking overview](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/overview.htm)
and [Security rules](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/securityrules.htm).

## Workload identity and artifacts

| OCI term | Plain definition | Approximate cross-cloud mental model | Common trap |
|---|---|---|---|
| **Dynamic group** | An IAM group whose membership is selected by matching rules over OCI resources. It is commonly used so resource principals can be named in IAM policies. | Roughly a role trust condition or managed-identity assignment rule. | Believing membership grants access by itself. A narrowly scoped IAM policy is still required; a broad matching rule widens the principal set. |
| **Resource principal** | A service identity that lets a supported OCI resource call OCI APIs without distributing a human user's API key to the application. | An AWS workload role, GCP service account attached to a workload, or Azure managed identity. | Assuming a platform capability such as private image pull automatically means the application should receive OCI API access. Give the app an identity only for a reviewed need. |
| **Workload identity** | A way for a supported application workload, notably an OKE workload, to authenticate to OCI APIs as that workload instead of as a human user. | AWS IRSA/EKS Pod Identity, GKE Workload Identity, or Azure Workload Identity. | Treating the Kubernetes service account association as permission. The exact cluster, namespace, service account, principal type, and IAM policy still matter. |
| **OCIR (OCI Container Registry)** | OCI's managed registry for storing and pulling container images. | Amazon ECR, Google Artifact Registry, or Azure Container Registry. | Assuming repository creation enables scanning or private pulls automatically. Registry endpoint, namespace, authentication, network path, repository policy, and immutable digest all need deliberate handling. |

## Compute, delivery, and governance

| OCI term | Plain definition | Approximate cross-cloud mental model | Common trap |
|---|---|---|---|
| **Compute instance / VM** | A virtual machine that runs an operating system and your software. You select its image, shape, storage, and network configuration. | An EC2 instance, Azure VM, or Compute Engine VM. | Treating a successful SSH login as evidence that an application is deployed, secured, or production-ready. |
| **Image** | The operating-system and software starting point used to launch an instance. | An AMI or VM image. | Selecting an image whose processor architecture or supported shape does not match the intended VM. |
| **Shape** | The hardware allocation model for an instance, including processor, memory, and related resource characteristics. | An EC2 instance type or VM machine type/size. | Assuming a familiar shape name guarantees available capacity, Free Tier eligibility, or compatibility in the selected region. |
| **Boot volume** | Persistent block storage containing the VM's boot image and operating-system disk. It has a lifecycle separate from the running VM. | An EBS root volume, Azure OS disk, or Compute Engine boot disk. | Assuming Stop or Terminate automatically removes all storage and charges. Review retention explicitly, including backups. |
| **OCPU** | OCI's unit for expressing processor capacity. Its relationship to vCPUs depends on the processor and shape, so it is not a safe one-for-one synonym for `vCPU`. | A vCPU sizing input, after normalizing for the selected processor and shape. | Comparing performance or price across clouds by the number alone without checking the OCPU-to-vCPU model and memory allocation. |
| **Flex shape** | A compute shape whose processor and memory allocation can be selected within the shape's supported range. | Closest to a GCP custom machine type or a configurable VM family in another cloud. | Assuming every service, processor, region, or OCPU-to-memory combination supports the same Flex choices or resize behavior. |
| **Resource Manager** | OCI's managed Terraform service for organizing stacks and running Terraform jobs with managed state. Local use of the OCI Terraform provider is a separate execution choice. | Terraform Cloud/Enterprise is the closest operational model; CloudFormation, Deployment Manager, and ARM/Bicep are only intent-level comparisons. | Assuming Terraform that validates locally will run unchanged. Resource Manager supports specific Terraform versions and needs its own compatibility test. |
| **Work request** | A status record for an asynchronous OCI operation. It can expose progress and operation-specific errors after the initial API call returns. | An Azure long-running operation, GCP operation resource, or an AWS asynchronous operation status. | Treating an accepted API response as completion. Poll the work request to a terminal state and inspect its errors before declaring success. |
| **Budget** | A cost-monitoring target with actual or forecast alert rules and notification destinations. It does not stop resource consumption. | AWS Budgets, GCP budgets, or Azure budgets. | Calling a budget a spending cap. Use architecture bounds and supported quotas when enforcement is required, and verify that notifications are delivered. |
| **Quota** | A tenancy-admin policy that constrains how supported resources can be allocated in compartments. | A mixture of organization policy and a service quota allocated to a project or account. | Assuming every service supports quotas, or that a quota reserves capacity. A quota can restrict use but cannot raise a service limit or guarantee capacity. |
| **Service limit** | The maximum amount of a service resource OCI currently allows for a tenancy or scope. Some limits can be increased through the documented request process. | An AWS Service Quota, Azure subscription quota, or GCP project quota. | Confusing an approved limit with live capacity or regional availability. Check all three before deployment and never copy a limit value from an old example. |

See [Creating an instance](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/launchinginstance.htm),
[Compute shapes](https://docs.oracle.com/en-us/iaas/Content/Compute/References/computeshapes.htm),
[Boot volumes](https://docs.oracle.com/en-us/iaas/Content/Block/Concepts/bootvolumes.htm),
and [Billing for stopped instances](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/resource-billing-stopped-instances.htm).

## Sources and scope

This glossary condenses the founder-oriented models already maintained in
[`service-map.md`](../skills/oci-founder/references/service-map.md) and the
safety rules in [`guardrails.md`](../skills/oci-founder/references/guardrails.md).
The official Oracle sources already used by this repository are authoritative:

- [OCI account concepts](https://docs.oracle.com/en-us/iaas/Content/GSG/Concepts/concepts-account.htm) for the tenancy, region, and account model.
- [Working with compartments](https://docs.oracle.com/en-us/iaas/Content/Identity/compartments/Working_with_Compartments.htm) and [IAM tenancy and compartments](https://docs.oracle.com/en-us/iaas/Content/Security/Reference/iam_security_topic-IAM_Tenancy_and_Compartments.htm) for governance scope.
- [Networking overview](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/overview.htm) for VCNs, subnets, routing, and gateways.
- [OCI Functions resource access](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsaccessingociresources.htm), [OKE](https://docs.oracle.com/en-us/iaas/Content/ContEng/home.htm), and [Container Instances IAM policies](https://docs.oracle.com/en-us/iaas/Content/container-instances/permissions/policy-reference.htm) for workload identity patterns.
- [Repository-level OCIR policies](https://docs.oracle.com/en-us/iaas/Content/Registry/Concepts/registrypolicyrepoaccess.htm) and [OCIR image scanning](https://docs.oracle.com/en-us/iaas/Content/Registry/Tasks/registryscanningimagesforvulnerabilities.htm) for registry access and scanning.
- [Terraform on OCI](https://docs.oracle.com/en-us/iaas/Content/dev/terraform/home.htm) and [Resource Manager supported Terraform versions](https://docs.oracle.com/en-us/iaas/Content/ResourceManager/Reference/terraformversions.htm) for Terraform execution choices.
- [Budgets overview](https://docs.oracle.com/en-us/iaas/Content/Billing/Concepts/budgetsoverview.htm) and [OCI cost management](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/era-cost-management.htm) for budget and cost-control semantics.

Product behavior, regional availability, limits, and pricing can change. Treat
this glossary as orientation and verify consequential decisions against current
official documentation and the target tenancy.
