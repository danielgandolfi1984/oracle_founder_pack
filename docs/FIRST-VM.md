# Your first VCN and Linux VM

Build a small learning environment, understand its network, connect over SSH,
then remove only what you created. This is a **human-executed Console guide**,
not a new automated VM skill, a production architecture, or release qualification.
The standalone `oci-founder` **v0.1.1** remains at planning level without verified
operational dependencies. Reading this guide or installing the skill grants no
cloud authority. See the [skill contract](../skills/oci-founder/SKILL.md).

Public Oracle sources checked on **2026-09-19**. Console labels can vary; this
guide includes the documented tab-based and older **Resources** navigation.
The procedure has been reviewed against documentation, not run against a live
tenancy as part of this documentation update.

## 1. Prepare the account and agree on the lab

Complete [account setup](ACCOUNT-SETUP.md) first: know your tenancy, region,
project compartment and local authentication method. CLI setup is useful for
later agent work, but the resource creation below is performed in the Console.

Before creating anything:

- Use a dedicated, authorized compartment, such as `founder-lab`, and confirm
  the selected region. Do not reuse production networking for this exercise.
- Confirm permissions for each planned networking, instance, image and volume
  operation, including cleanup. Permission to list a VCN does not prove access
  to create a VM or inspect every NSG rule. Ask the tenancy administrator for
  the required scope; do not grant `manage all-resources` as a shortcut.
  [Oracle instance IAM requirements](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/instances.htm)
- Confirm that public subnets and public IPs are allowed. If organization
  policies or a security zone prohibit them, stop and design a private-access
  lab with your administrator; do not bypass those controls.
- Agree on a spending allowance, end time and owner. Check current shape,
  image, storage and traffic charges for the selected region; this guide makes
  no Free Tier eligibility or capacity guarantee.
- Start a private **lab receipt** outside Git: date, owner, tenancy, region,
  compartment OCID, planned resources and cleanup deadline. Add each resource's
  OCID, cost inputs, result and keep/delete decision as you go. Never put private
  keys or tokens in this receipt; redact account identifiers before sharing it.

Use these names and IPv4 ranges only as **examples**, after checking for overlap
with your VPN, corporate network, other VCNs and future peering:

| Resource | Example | Purpose |
|---|---|---|
| VCN | `founder-lab-vcn`, `10.20.0.0/16` | Private network address space |
| Regional public subnet | `lab-public`, `10.20.10.0/24` | Smaller range inside the VCN |
| Internet gateway | `lab-igw` | Internet path for public-IP resources |
| Network security group | `lab-ssh-nsg` | SSH access from your current public IPv4 `/32` |
| Linux VM | `lab-vm` | One disposable learning machine |

The network path is your computer → internet → gateway → public VM in the
subnet. A public subnet alone does not supply the VM's public IP, the route or
traffic permission. [Oracle public-subnet scenario](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/scenarioa.htm)

## 2. Create the VCN and subnet

1. Open **Networking → Virtual cloud networks**. Select your lab compartment,
   then **Create VCN**. Use manual creation for this exercise, not the wizard.
2. Enter `founder-lab-vcn`, confirm the compartment and enter `10.20.0.0/16`.
   Enable DNS hostnames for this lab and let the Console generate its DNS label.
   Do not add IPv6 for this IPv4-only exercise. Review, then choose **Create VCN**.
3. Record the VCN OCID from its details. Open **Subnets → Create subnet**, or the
   **Create Subnet** action in the older layout.
4. Enter `lab-public`, the same compartment, **Regional**, `10.20.10.0/24`, and
   **Public subnet**. Use this new VCN's default route table and DHCP options.
   Enable subnet DNS hostnames consistently with the VCN.
5. Record the security-list and DHCP-options OCIDs. Review, then create the subnet
   and record its OCID. Inspect its actual route-table and security-list
   associations; the names alone are not proof of the right target.

The subnet range must fit inside the VCN and not overlap another subnet.
Sources: [VCN creation](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/create_vcn.htm),
[subnet creation](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/create_subnet.htm).

## 3. Add the internet path

1. On this VCN, open **Gateways → Internet Gateways → Create Internet Gateway**
   (older layout: **Resources → Internet Gateway**).
2. Name it `lab-igw`, confirm the compartment and create it. Confirm the gateway
   is enabled. Leave the advanced gateway **Route Table Association** unset for
   this simple lab; the next route belongs to the subnet's route table.
3. Open the VCN's **Routing** tab (older layout: **Resources → Route Tables**).
   Select the exact route table associated with `lab-public`.
4. Open **Route Rules → Add Route Rules**. Set destination CIDR `0.0.0.0/0`,
   target type **Internet Gateway**, and target `lab-igw`. Review and save.
5. Record gateway and route-table OCIDs and verify the saved target and subnet
   association in the receipt.

`0.0.0.0/0` in a **route** chooses a path; it does not authorize inbound SSH.
Sources: [internet gateway](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/create-ig.htm),
[route-table rules](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/update-rules-routetable.htm).

## 4. Restrict SSH before adding the VM

Find your current **public egress IPv4** using a trusted network tool or your
network administrator. It is not usually the laptop's `192.168.x.x` address.
Use that actual address followed by `/32`; it can change after switching Wi-Fi
or VPN. Do not copy a made-up IP or use `0.0.0.0/0` as the SSH source.

1. On the VCN, open **Security → Network Security Groups → Create Network
   Security Group** (older layout: **Resources → Network Security Groups**).
2. Create `lab-ssh-nsg` in the lab compartment with this rule:

   | Field | Value |
   |---|---|
   | Direction | Ingress |
   | Stateful | Yes; leave **Stateless** unchecked |
   | Source type / source | CIDR / your public IPv4 followed by `/32` |
   | Protocol | TCP |
   | Source port | All |
   | Destination port | `22` |

3. Record the NSG OCID. You will attach it to the VM's primary VNIC in step 5;
   creating the group does not automatically attach any VM.

Source: [creating an NSG](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/create-nsg.htm).

Before proceeding, open **Security → Security Lists** on the VCN (or
**Resources → Security Lists**) and review every list associated with the subnet.
In this dedicated lab, remove or narrow any broader SSH ingress rule. Preserve
needed non-SSH and outbound rules deliberately; do not clear the whole list.

**NSG and security-list allow rules combine.** A narrow NSG rule cannot cancel a
broad allowance in a security list or another attached NSG. Never change a
shared list without checking every affected workload. If ZPR security attributes
are present, their policies are an additional requirement, not a bypass.
[Oracle security rules](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/securityrules.htm)

## 5. Create one Linux VM

Open **Compute → Instances → Create instance**. The workflow has **Basic
Information, Security, Networking, Storage and Review**; field order can vary.

At the SSH-key section, generate a lab key pair and **save the private key
securely before continuing**, or upload only the public key of an existing
approved pair. Keep the private key outside Git and chats. This SSH key is not
your OCI API signing key. [SSH key pairs](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/managingkeypairs.htm)

- **Basic information:** `lab-vm`, lab compartment and an available availability
  domain. Select a current Oracle Linux or Ubuntu platform image and a compatible
  **virtual machine** shape. Review CPU, memory and security options.
- **Networking:** select the existing lab VCN and subnet, explicitly assign a
  public IPv4 and select `lab-ssh-nsg` for the primary VNIC.
- **Storage:** review boot-volume size, performance and cost; do not add extra
  disks for this exercise.
- **Review:** compare all values with the receipt. Only select **Create** after
  personally approving the exact target, resources, exposure and expected cost.

Source: [creating an instance](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/launchinginstance.htm).

Arm/aarch64 and x86 images and application binaries are not interchangeable;
confirm image/shape compatibility. Before keeping the VM beyond this lab, plan
OS security updates. [Platform images](https://docs.oracle.com/en-us/iaas/Content/Compute/References/images.htm)

Wait for **Running**. Record the instance, primary VNIC and boot-volume OCIDs,
image, shape, CPU, memory and public IP in the receipt. Confirm the VNIC's actual
subnet and NSG. One VM is not a highly available application deployment.

## 6. Connect, validate and record the result

On the instance details page, find **Instance access → Public access IP address**.
In a macOS/Linux terminal, replace both placeholders below with your local key
path and the VM's public IP:

```bash
chmod 400 /absolute/path/to/lab-ssh-private-key
ssh -i /absolute/path/to/lab-ssh-private-key opc@PUBLIC_IP
```

Use `opc` for Oracle Linux or `ubuntu` for Ubuntu. Windows users should follow
the private-key permission steps in [Oracle's SSH guide](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/connect-to-linux-instance.htm).
Verify an unfamiliar host fingerprint through a trusted channel; do not disable
host-key checking. Your OCI CLI session does not replace SSH authentication.

Once connected, run `uname -m` and `cat /etc/os-release` to inspect architecture
and OS, then `exit`. Record success/failure and time without publishing private
identifiers. No application installation or extra ingress port is part of this lab.

Open **Observability & Management → Monitoring → Service Metrics**. Select the
subnet compartment and namespace `oci_vcn`; inspect the lab VNIC's traffic and
security-rule drops. Record missing telemetry, not assumed monitoring coverage.
[Oracle VNIC metrics](https://docs.oracle.com/en-us/iaas/Content/Network/Reference/vnicmetrics.htm)

| Symptom | Inspect before making any change |
|---|---|
| SSH timeout | Public IP, enabled gateway, subnet route, current source `/32`, NSG membership, security lists and OS firewall |
| `Permission denied (publickey)` | Image's username and matching SSH private key; never print the key |
| Unauthorized / resource not found | Region, compartment, target OCID and permission for that particular operation |
| Shape unavailable | Image compatibility, availability domain, capacity and service limits; do not silently choose a more expensive shape |

For a failed step, capture the error and resource state, stop additional creation,
and revise the plan. Do not open SSH globally or broaden IAM by trial and error.
[Oracle SSH troubleshooting](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/troubleshooting-ssh-connection.htm)

## 7. End the lab and verify cleanup

Budget alerts are **not spending caps**. Track compute, boot/block volumes,
backups and traffic; alerts require their own IAM permissions.
[Oracle budgets](https://docs.oracle.com/en-us/iaas/Content/Billing/Concepts/budgetsoverview.htm)

**Stop is not cleanup.** Stopped-instance charges depend on the shape, volumes
remain, and shutting down inside Linux is not the same as stopping through
OCI. [Stopped-instance billing](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/resource-billing-stopped-instances.htm)

1. Use the receipt to resolve the exact instance and dependencies. Decide what
   data to preserve and preview a delete/keep list. If an agent is assisting,
   give separate explicit approval immediately before any destructive action.
2. In **Compute → Instances**, match the instance OCID. Choose its **Actions →
   Terminate**. Review the boot-volume and any block-volume deletion choices
   explicitly; do not rely on defaults. Confirm only after resolving retained
   data. [Termination and volume choices](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/terminatinginstance.htm)
3. Verify **Terminated**, then inspect the receipt's volumes, backups and IP
   resources. Retained storage may still cost money. Mark each retained resource
   with its owner and next review date; deletion is irreversible.
4. For this dedicated, empty lab VCN only, open its **Actions → Delete** and scan
   **Specific compartments**, selecting only the lab compartment. Inspect every
   discovered dependency against the receipt before confirming deletion. Stop
   if any resource is shared or unexpected; never clean a whole compartment.
   [VCN deletion workflow](https://docs.oracle.com/en-us/iaas/Content/Network/Tasks/delete_vcn.htm)
5. Confirm the intended network resources are gone and record deleted, retained
   or blocked outcomes individually. Review billing again when usage appears;
   disappearance from a list is not proof that the account has zero charges.

If Terraform created an environment, use its exact state and deployment receipt
instead of this manual cleanup path. Reconcile a partial failure before retrying;
never widen deletion scope to work around a dependency error.

## Ask the skill to help you reason

```text
Use the oci-founder skill. Review my first-VM lab plan, planning only.
Explain VCN, subnet, gateway, route, NSG, VNIC, image and shape in plain language.
Check my account scope, SSH exposure, cost inputs and cleanup checklist.
Do not use credentials, change IAM, create resources or run cleanup.
```

Next: [founder/developer recipes](USE-CASES.md), [OCI glossary](GLOSSARY.md), or
[Founder Baseline](FOUNDER-BASELINE.md) before designing an application environment.
