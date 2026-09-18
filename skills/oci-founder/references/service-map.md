# AWS, Google Cloud, and Azure mental models for OCI

These mappings accelerate orientation. They are not claims of feature or lifecycle equivalence. Validate identity scope, network behavior, scaling, availability, and pricing before choosing a service.

## Organization and identity

| Familiar concept | OCI concept | Important difference |
|---|---|---|
| AWS account / Azure subscription / GCP project | OCI tenancy plus compartments | A tenancy is the account-level security boundary. Compartments are tenancy-wide logical access and governance boundaries, not physical containers and not billing accounts. |
| AWS Organizations OU / Azure management group / GCP folders | Compartment hierarchy, and OCI Organizations for multi-tenancy needs | Do not create multiple tenancies merely to imitate projects. Start with compartments unless strong isolation or organizational requirements justify more. |
| AWS IAM policy / Azure RBAC / GCP IAM policy | OCI IAM policy | OCI policies use subject, verb, resource type, location, and optional conditions. Translate intent, not syntax. |
| EC2 instance role / GCP service account on a workload / Azure managed identity | Instance principals, resource principals, workload identity, and dynamic groups | The correct OCI principal depends on the runtime. Avoid distributing user API keys to workloads. |
| Resource group / project labels / AWS tags | Compartments plus defined or free-form tags | Compartments primarily organize access and quotas; tags add cross-cutting ownership and cost metadata. |

## Networking

| Familiar concept | OCI concept | Important difference |
|---|---|---|
| AWS VPC / GCP VPC / Azure VNet | Virtual Cloud Network (VCN) | CIDR, subnet, routing, gateway, DNS, and regional behavior must be reviewed rather than mechanically converted. |
| AWS security group / GCP firewall rule / Azure NSG | Network Security Group (NSG), plus security lists | Prefer NSGs for resource-level policy. Security lists apply at subnet scope. |
| AWS Availability Zone / GCP zone / Azure availability zone | Availability Domain (AD), with Fault Domains inside an AD | Region topology differs. Do not assume every OCI region has the same number of ADs. |
| NAT Gateway | NAT Gateway | Similar purpose, but routes, service access, and cost behavior still require OCI-specific design. |
| AWS VPC endpoint / GCP Private Service Connect patterns / Azure Private Link | Service Gateway, private endpoints, and service-specific private access | There is no single universal translation; choose based on the target OCI service. |

## Compute and application runtime

| AWS | Google Cloud | Azure | OCI | Translation note |
|---|---|---|---|---|
| EC2 | Compute Engine | Virtual Machines | Compute | The closest VM-level model. Shapes, OCPUs, images, and pricing units differ. |
| Lambda | Cloud Functions | Azure Functions | OCI Functions | Function packaging, triggers, limits, networking, and invocation authentication differ. Reuse the official Functions skills. |
| Fargate / App Runner | Cloud Run | Container Apps / Container Instances | Container Instances, often with API Gateway or Load Balancer | OCI Container Instances runs containers without managing servers, but it is not a request-autoscaling drop-in replacement for Cloud Run or App Runner. |
| EKS | GKE | AKS | OKE | Choose only when Kubernetes is a requirement. Upstream Oracle skills cover design and troubleshooting. |
| ECR | Artifact Registry | ACR | OCI Container Registry (OCIR) | Registry authentication, repository naming, scanning, and network access differ. |
| API Gateway | API Gateway | API Management | API Gateway | OCI API Gateway can front Functions and other HTTP backends and can enforce authentication and rate limiting. |

## Data and storage

| Familiar concept | OCI options | Selection rule |
|---|---|---|
| S3 / Cloud Storage / Blob Storage | Object Storage | Use for objects and artifacts; verify namespace, bucket policy, pre-authenticated requests, lifecycle, and egress needs. |
| RDS PostgreSQL / Cloud SQL PostgreSQL / Azure Database for PostgreSQL | OCI Database with PostgreSQL | Use for PostgreSQL compatibility after confirming extensions, connection topology, region availability, HA, and cost. |
| RDS MySQL / Cloud SQL MySQL / Azure Database for MySQL | MySQL HeatWave Service | Use for MySQL compatibility; HeatWave features are optional, not a reason to change workload semantics. |
| Managed Oracle or serverless relational database | Autonomous AI Database | Consider when Oracle Database capabilities, autonomous operations, JSON, vector, APEX, or existing Oracle compatibility are valuable. |
| DynamoDB / Firestore / Cosmos DB | NoSQL Database and other OCI data services | Data model, consistency, query model, SDK, capacity, and migration effort require a workload-specific analysis. |

## Operations, security, and delivery

| Familiar concept | OCI concept | Important difference |
|---|---|---|
| CloudWatch / Cloud Monitoring / Azure Monitor | Monitoring, Logging, Alarms, Notifications, APM, and Connector Hub | OCI separates telemetry capabilities across services. Define the signal and notification path explicitly. |
| Secrets Manager + KMS / Secret Manager + Cloud KMS / Key Vault | OCI Vault keys and Secret Management | Keep secret values out of IaC source and application configuration; use workload identity to retrieve them. |
| CloudFormation / Deployment Manager / ARM-Bicep | OCI Resource Manager with Terraform, or the OCI Terraform provider locally | Terraform is the portable canonical choice. Treat Terraform state as sensitive. |
| AWS Budgets / GCP budgets / Azure budgets | OCI Budgets | OCI budgets alert on actual or forecasted spend; they do not stop resource consumption. Use quotas for enforceable compartment limits where supported. |

## Translation rules

1. Translate the workload contract first: request model, state, identity, scaling, availability, and operations.
2. Mark mappings as close, approximate, or no direct equivalent.
3. Never translate IAM syntax mechanically.
4. Never infer region availability, Free Tier eligibility, limits, or prices from another cloud.
5. Prefer a reversible OCI-native design over reproducing an accidental source-cloud architecture.

## Sources and claim coverage

- Tenancy and account model: [OCI account concepts](https://docs.oracle.com/en-us/iaas/Content/GSG/Concepts/concepts-account.htm).
- Compartment scope and hierarchy: [Working with compartments](https://docs.oracle.com/en-us/iaas/Content/Identity/compartments/Working_with_Compartments.htm).
- VCN, subnet, routing, and gateway model: [Networking overview](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/overview.htm).
- Container runtime comparison input: [Container Instances overview](https://docs.oracle.com/en-us/iaas/Content/container-instances/overview-of-container-instances.htm).
- Function runtime comparison input: [OCI Functions](https://docs.oracle.com/en-us/iaas/Content/Functions/home.htm).
- Kubernetes comparison input: [Oracle Container Engine for Kubernetes](https://docs.oracle.com/en-us/iaas/Content/ContEng/home.htm).
- API front-door capabilities: [API Gateway](https://docs.oracle.com/en-us/iaas/Content/APIGateway/).
- Terraform execution choices: [OCI Terraform provider](https://docs.oracle.com/en-us/iaas/Content/dev/terraform/home.htm).
- Budget alert semantics: [Budgets overview](https://docs.oracle.com/en-us/iaas/Content/Billing/Concepts/budgetsoverview.htm).
