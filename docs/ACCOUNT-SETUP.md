# Your OCI account and local access

Use this guide when you want to move from planning a backend to understanding
your own OCI account. You will locate identifiers in the Console, prepare local
authentication, and run one read-only network query. No VM or VCN is created.

You execute these steps yourself. The standalone `oci-founder` skill `v0.1.1`
can explain and review your plan, but remains at planning level without its
verified operational dependencies. This guide adds documentation, not a new
automatic account-setup feature or live-tested deployment claim.

Official sources checked on **2026-09-19**. Console labels can vary by language
and layout. You need an existing OCI account, permission to use it, and a local
terminal. New account signup and billing enrollment are outside this guide.
For skill installation, use the [quickstart](QUICKSTART.md).

These credentials let your tools call OCI cloud APIs; they are not your
application's end-user login. For app-user access tokens, provider settings
and a read-only Identity Domains discovery checklist, see the separate
[offline identity integration guide](../examples/local-backend/IDENTITY-INTEGRATION.md).
Never substitute an OCI API signing key or CLI session token for an app token.

## 1. Know what connects the agent to OCI

| Part | Purpose | Does not provide |
|---|---|---|
| Skill | Instructions for planning and reviewing the work | An authenticated connection or IAM grant |
| Executor | The terminal, CLI, SDK, or connector that performs a request | Authority merely because it can run a command |
| Profile and credential | Identify the caller and authenticate a request | Permission for every service or compartment |
| IAM policy | Authorize particular operations on a defined scope | Approval to perform every allowed action now |

For this lab, choose the **local terminal**. Logging into the Console does not
configure that terminal. A remote agent, container, or CI runner is a different
environment and needs its own reviewed authentication setup. Do not copy a
human credential to a remote runner to make an example work. See Oracle's
[authentication methods](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdk_authentication_methods.htm).

[Cloud Shell](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cloudshellintro.htm)
is a separate browser-based environment with a pre-authenticated CLI and its
own IAM access requirement. It does not authenticate the tools on your laptop.

## 2. Find the identifiers in the Console

Sign in to the [OCI Console](https://cloud.oracle.com/) yourself, including MFA.
Keep the following values in private local notes, outside your repository:

| Value | Console location | Use |
|---|---|---|
| Tenancy OCID | Profile menu, **Tenancy: your tenancy name**, **Tenancy Information**, **Copy** | Identify the account |
| User OCID | Profile menu, **User settings**, **User Information**, **Copy** | Identify the user for API signing setup |
| Region identifier | Region selector at the top, matched to the official region list | Choose where regional resources live |
| Compartment OCID | **Identity & Security**, **Compartments**, select the compartment OCID and **Copy** | Bound the project resource inventory |
| Existing resource OCID | The VM, VCN, or subnet details page | Target one specific resource |

São Paulo's region identifier is `sa-saopaulo-1`. Use your selected region,
not that example by default. An OCID identifies something; it is not a password
or an access grant. Share only necessary identifiers with a trusted executor
and redact them from public issues. Sources:
[locating IDs](https://docs.oracle.com/en-us/iaas/Content/GSG/Tasks/contactingsupport_topic-Locating_Oracle_Cloud_Infrastructure_IDs.htm),
[user identity](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/apisigningkey.htm),
[region identifiers](https://docs.oracle.com/en-us/iaas/Content/General/Concepts/regions.htm).

For the VM lab, select a dedicated project compartment outside root. If you
need a new one and are authorized, use **Identity & Security**, **Compartments**,
**Create Compartment**, choose its parent, and review the name and description
before creating it. Otherwise ask the account administrator for a suitable
compartment and scoped access. Follow Oracle's
[compartment creation procedure](https://docs.oracle.com/en-us/iaas/Content/Identity/compartments/To_create_a_compartment.htm).

## 3. Choose the credential for the job

| Credential | Intended use in this journey | Where the secret stays |
|---|---|---|
| Temporary CLI session | Interactive local OCI API access after browser login | Local session token and signing key files |
| API signing key | Alternative OCI API authentication with a configured profile | Local private key, with only the public key registered in OCI |
| SSH key pair | Login to the Linux VM, not to the OCI API | Private key on your computer, public key on the VM |
| OCIR auth token | Registry login when a later container workflow needs it | Approved local credential store, never a prompt |

Choose one OCI API authentication path below; you do not need both. This lab
does not need an OCIR token. Passwords, MFA codes, private keys and token files
must stay out of prompts, Git, logs, screenshots and support attachments. Sources:
[OCI authentication methods](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdk_authentication_methods.htm),
[SSH keys](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/managingkeypairs.htm),
[registry auth tokens](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsgenerateauthtokens.htm).

## 4. Install or check the local OCI CLI

In the terminal you intend to use, run `oci --version`. If it is missing, use
the [official OCI CLI installation guide](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm)
for your operating system. On macOS with Homebrew already available:

```bash
brew update
brew install oci-cli
oci --version
```

Installation changes your computer, not OCI resources. The following examples
use Bash/Zsh syntax on macOS or Linux. In PowerShell, enter each OCI command on
one line instead of copying the `\` line continuations.

## 5. Start with a temporary local session

Use a new profile name if `FOUNDER` already exists. Substitute that chosen name
for `FOUNDER` in every command and context example below. In your terminal:

```bash
oci session authenticate --profile-name FOUNDER
```

Select the region in the CLI's interactive prompt. Complete browser login and
MFA yourself, then return to the terminal and finish the prompts. The CLI saves
the session configuration locally. Validate the generated profile:

```bash
oci session validate --profile FOUNDER --auth security_token
```

Success reports the session's expiration date. It does not prove permission to
create resources. Keep `--auth security_token` on subsequent commands using this
profile. If the session expires, authenticate again deliberately, reviewing any
profile replacement prompt. Do not publish or export its token to chat. See
[token-based CLI authentication](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/clitoken.htm)
and the [`authenticate` options](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/session/authenticate.html).

## Alternative: API signing key from the Console

Use this path only if you deliberately choose API key authentication instead of
the temporary session:

1. Open your **User settings**, then **Token and keys** / **API Keys**. Older
   layouts list **API Keys** under **Resources**.
2. Select **Add API Key**. Generate a pair and save the private key securely
   outside Git, or upload an existing **public** API signing key in PEM format.
3. Review the user, then confirm **Add**. Registering a key changes the account's
   authentication configuration. This key is distinct from a VM's SSH key.
4. Use **Configuration File Preview** to prepare a new named profile in your
   local `~/.oci/config`. Preserve existing profiles and set the correct local
   private-key path. Restrict key-file access to your user. If `FOUNDER_API`
   already exists, choose a new name and substitute it in every API key example.

The configuration has this structure. Replace every placeholder locally:

```ini
[FOUNDER_API]
user=<user-ocid>
fingerprint=<key-fingerprint>
tenancy=<tenancy-ocid>
region=<region-id>
key_file=/absolute/private/path/to/api-signing-key.pem
```

Follow Oracle's [key and configuration procedure](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/apisigningkey.htm)
for key protection and the generated snippet. Do not paste private-key contents
into the configuration or an agent prompt. A generated session profile also
uses a `security_token_file`; the API key example above is not a replacement
for that profile. See [authentication configuration](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdk_authentication_methods.htm).

## 6. Test access to the project's VCN inventory

Replace the quoted placeholders before running this **read-only** request.
For the temporary session:

```bash
oci network vcn list \
  --compartment-id '<compartment-ocid>' --region '<region-id>' \
  --profile FOUNDER --auth security_token --all
```

If you chose API signing instead, run this version:

```bash
oci network vcn list \
  --compartment-id '<compartment-ocid>' --region '<region-id>' \
  --profile FOUNDER_API --auth api_key --all
```

The result is a VCN list, which can be empty. Check the exact compartment and
region before interpreting it. The API key alternative applies to this query,
**not** to `oci session validate`. See the
[`vcn list` reference](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/network/vcn/list.html).

A successful list does not prove permission to inspect every network setting
or create a VM. Ask the administrator to review the exact operations and target
scope, including networking and Compute dependencies, against Oracle's
[Core Services policy reference](https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/corepolicyreference.htm).
Do not solve an error by granting `manage all-resources`.

| Symptom | Check first |
|---|---|
| `oci` is not found | Installation and PATH in this specific executor |
| Session validation fails / 401 | Selected profile, authentication method, expiry and local clock |
| API key authentication fails | Locally confirm the user, registered fingerprint and private-key pairing without printing the key |
| `NotAuthorizedOrNotFound` | Region, compartment, resource identifier and the exact IAM operation |

These are initial checks, not a diagnosis. Share only redacted error text. The
[OCI API error guide](https://docs.oracle.com/en-us/iaas/Content/API/References/apierrors.htm)
explains why an error can conceal whether a resource exists.

## 7. Give the agent safe context, then plan the lab

After installation, ask the `oci-founder` skill:

```text
I want to plan my first Linux VM in OCI. My executor is local.
The profile is FOUNDER and the authentication method is security_token.
Region: [region-id]. Project compartment: [compartment-ocid].
Explain the read-only checks and review a VCN, subnet, and VM proposal.
Do not open credential files, execute OCI commands, or create resources.
```

Use `FOUNDER_API` and `api_key` in that context if you chose the alternative.
Provide no private key, token, password, or full configuration dump. Review
the host's permissions and data-handling settings before allowing credential
use. A prompt alone is not an access-control boundary.

You are ready for the [first VCN and Linux VM lab](FIRST-VM.md) when you know
the target account and region, have a suitable compartment, have tested the
chosen local authentication method, and understand which changes need review.
Keep the [Founder Baseline](FOUNDER-BASELINE.md) alongside the lab.
