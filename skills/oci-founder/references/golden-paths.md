# Founder golden paths

Golden paths are defaults for a stage, not universal architectures. Re-evaluate when traffic, availability, compliance, team size, or workload behavior changes.

## Decision table

| Workload signal | Primary candidate | Avoid when |
|---|---|---|
| Existing Dockerized HTTP service; persistent process; ordinary API or web app; no Kubernetes contract | Container API | Request-level scale-to-zero is mandatory, the process model is function-native, or Kubernetes APIs are required |
| Small event or request handlers; intermittent or bursty traffic; function-compatible timeout and state model | Function API | Long-running processes, unsupported runtime behavior, persistent connections, or predictable steady load makes a container simpler |
| Kubernetes manifests, operators/controllers, advanced scheduling, service mesh, or a platform team | OKE graduation path | Kubernetes is only being chosen because it is familiar |
| VM-specific software, privileged host needs, legacy agents, or OS-level control | Compute path | The workload can use a managed container or function safely |

The table qualifies only the runtime shapes it names. A persistent queue worker,
scheduled or batch job, cache, WebSocket or streaming endpoint, and non-HTTP
protocol require a workload-specific review of lifetime, trigger, concurrency,
retry, ordering, durability, connection behavior, scaling, availability, and
supervision. Do not silently classify one as a Container API or Function API.
When no reviewed toolkit or upstream path covers the workload, provide a
requirements decision and current official sources rather than an operational
recipe.

## Golden path A: Container API

### Best fit

An existing Dockerized backend that listens on an HTTP port and should run without a Kubernetes control plane.

### Proposed service composition

- OCI Container Registry for the application image.
- Container Instances for the running container.
- API Gateway or Load Balancer according to ingress, protocol, health-check, and policy needs.
- A minimal VCN with explicit public/private subnet decisions and NSGs. Use a Service Gateway for OCIR-backed images; add NAT only when the workload requires public egress.
- Vault Secret Management for application secrets, with an explicit resource-principal retrieval design and least-privilege policy. Do not assume automatic runtime injection.
- Container log retrieval for immediate diagnosis (the native command returns
  only the most recent 256 KB), front-door service logs, Monitoring metrics,
  Alarms, and Notifications. If centralized application-log search or retention
  is required, design and verify an ingestion path explicitly.
- Terraform locally first; OCI Resource Manager is a later, separately tested
  execution variant and must use a currently supported Terraform version.
- Optional Object Storage and a selected managed database only after the stateless path works.

### Why it is founder-friendly

Container Instances runs containers without managing servers and is documented for APIs and web applications that do not need Kubernetes. It preserves a conventional container process model.

### Important non-equivalence

Do not describe this path as OCI Cloud Run or OCI App Runner. Validate scaling, restart behavior, ingress, deployment replacement, availability, and billing for the actual design.

### Repository preview

When this skill is used from the toolkit source repository, an explicitly
requested sandbox implementation may start from `blueprints/container-api`.
Its `0.2.0-preview.3` contract is a single private Container Instance behind API
Gateway, split into privileged bootstrap and routine runtime stacks. Read its
README before generating commands. It is not a production template, does not
provide autoscaling or zero-downtime replacement, and must not be used for a
production request.

### Cloud Run migration gate

Before recommending Container Instances for a Cloud Run workload, inventory the
current service's minimum and maximum instances, concurrency, CPU allocation,
request timeout, scale-to-zero dependence, streaming or WebSocket behavior,
background work, and revision or traffic-splitting requirements.

If request-driven autoscaling, scale-to-zero, or managed revision traffic is
material, label Container Instances non-equivalent and pause architecture
selection. Do not imply feature parity. A single Container Instance may be used
for a smoke test only; production requires an explicit availability, capacity,
replacement, and rollback design.

### Verification contract

- Image digest is recorded.
- Platform image pull uses a narrowly scoped Container Instance resource identity. Expose a resource principal inside the application only when the application has a reviewed OCI API need and an exact policy; the current sandbox sample keeps it disabled.
- Health endpoint returns the expected response.
- The selected gateway or load balancer access log shows the request.
- Container stdout/stderr can be retrieved; any required centralized ingestion and retention path is verified.
- Container metrics and an alarm-to-notification path are visible.
- Budget target and ownership tags cover the resources.
- Rollback image and teardown scope are documented.

## Golden path B: Function API

### Best fit

An event-driven or HTTP-triggered unit of work with function-compatible execution, intermittent traffic, and no reliance on a persistent local process.

### Proposed service composition

- OCI Functions application and functions.
- OCI Container Registry for function images.
- API Gateway for governed public HTTP access when needed.
- VCN/subnets according to downstream private access.
- Vault Secret Management and resource-principal access.
- Logging, tracing/metrics where supported, Alarms, and Notifications.
- Events or other service triggers when the use case is not HTTP.

### Upstream reuse

Use the official `oci-functions-deploy` skill for workstation deployment and `oci-functions-troubleshoot` for failures. This toolkit adds the founder baseline, gateway choice, cost framing, verification, and teardown sequence.

### Verification contract

- Direct signed invocation works before adding public ingress.
- API Gateway authentication and rate limiting match the threat model.
- Logs and metrics correlate with a test invocation.
- Cold-start and timeout behavior are measured for the actual runtime.
- Failed invocation and rollback paths are demonstrated.

## Data add-ons

Keep the first smoke deployment stateless unless data is the purpose of the workload.

| Need | Candidate | Verify before choosing |
|---|---|---|
| Existing PostgreSQL application | OCI Database with PostgreSQL | Extensions, version, private connectivity, pooling, migrations, HA, backup/restore, region, and cost |
| Existing MySQL application | MySQL HeatWave Service | Engine/version compatibility, network path, backup/restore, HA, region, and whether HeatWave is needed |
| Oracle, JSON, vector, APEX, or autonomous operational value | Autonomous AI Database | Driver, SQL compatibility, wallet/TLS model, autoscaling, backup, region, and cost |
| Files, uploads, artifacts, or static objects | Object Storage | Access pattern, pre-authenticated access, lifecycle, encryption, egress, and retention |

## Graduation signals

Graduate from the Founder Baseline when one or more of these become real requirements:

- multiple teams need independent access boundaries;
- production and non-production need stronger isolation and release controls;
- regulated controls require an enterprise landing zone;
- the application becomes a multi-service Kubernetes platform;
- multi-region recovery objectives are explicit;
- continuous cost allocation, policy-as-code, or central security operations are required.

Graduation is a planned redesign, not an automatic service upgrade.

## Sources and claim coverage

- Container process model and use cases: [Container Instances overview](https://docs.oracle.com/en-us/iaas/Content/container-instances/overview-of-container-instances.htm).
- OCIR network reachability and Service Gateway requirement: [Creating a Container Instance](https://docs.oracle.com/en-us/iaas/Content/container-instances/creating-a-container-instance.htm).
- Container identity and OCIR access policy: [Container Instances IAM policies](https://docs.oracle.com/en-us/iaas/Content/container-instances/permissions/policy-reference.htm).
- Container stdout/stderr retrieval: [Retrieving Container Instance logs](https://docs.oracle.com/en-us/iaas/Content/container-instances/retrieve-logs.htm).
- Container metrics and alarms: [Container Instance metrics](https://docs.oracle.com/en-us/iaas/Content/container-instances/container-instance-metrics.htm).
- Current native service-log coverage: [OCI Logging service log reference](https://docs.oracle.com/en-us/iaas/Content/Logging/Reference/service_log_reference.htm).
- Load Balancer access and error logs: [Load Balancer log reference](https://docs.oracle.com/en-us/iaas/Content/Logging/Reference/details_for_load_balancer_logs.htm).
- Function runtime and application model: [OCI Functions](https://docs.oracle.com/en-us/iaas/Content/Functions/home.htm).
- Direct signed Function invocation: [Invoking Functions](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsinvokingfunctions.htm).
- Function resource-principal access: [Accessing OCI resources from Functions](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsaccessingociresources.htm).
- API Gateway authentication and authorization: [API deployment authentication](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayaddingauthzauthn.htm).
- API Gateway rate limiting: [Limiting backend requests](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewaylimitingbackendaccess.htm).
- API Gateway access and execution logs: [API Gateway log reference](https://docs.oracle.com/en-us/iaas/Content/Logging/Reference/details_for_api_gateway.htm).
- Resource Manager Terraform compatibility: [Supported Terraform versions](https://docs.oracle.com/en-us/iaas/Content/ResourceManager/Reference/terraformversions.htm).
- Runtime secret retrieval API: [Getting a secret's contents](https://docs.oracle.com/en-us/iaas/Content/secret-management/Tasks/get-secrets-contents.htm).
- Budget alert semantics: [Budgets overview](https://docs.oracle.com/en-us/iaas/Content/Billing/Concepts/budgetsoverview.htm).
- Ownership and cost-attribution tags: [Tagging overview](https://docs.oracle.com/en-us/iaas/Content/Tagging/Concepts/taggingoverview.htm).
- PostgreSQL compatibility candidate: [OCI Database with PostgreSQL](https://docs.oracle.com/en-us/iaas/Content/postgresql/).
- MySQL compatibility candidate: [MySQL HeatWave Service](https://docs.oracle.com/en-us/iaas/mysql-database/index.html).
- Autonomous database candidate: [Autonomous AI Database](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/getting-started.html).
- Enterprise graduation boundary: [OCI Core Landing Zone](https://docs.oracle.com/en-us/iaas/Content/cloud-adoption-framework/oci-core-landing-zone.htm).
- Reusable Functions and OKE procedures: [Oracle Skills OCI domain](https://github.com/oracle/skills/tree/main/oci).
