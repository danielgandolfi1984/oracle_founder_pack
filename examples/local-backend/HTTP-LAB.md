# Optional local HTTP and signed-token lab

Use `curl` to practice the backend contract with **synthetic users on your own
machine**. This optional lab adds HTTP and RS256-signed JWT verification; it does
not add account signup, a login screen, or a real identity provider. No OCI
account, cloud resource, customer data, or real credential belongs here.

The original [in-process lesson](README.md) still works without third-party
packages or a listening port. This additional source example is on `main` only;
it does not change the released skill archives or Container API blueprint.

## 1. Install the optional dependencies

Prerequisites: a source checkout, **CPython 3.12**, `curl`, a POSIX shell, and
permission to create private temporary files and open a loopback socket. The
binary dependency lock targets macOS Apple Silicon and Linux x86_64; other
Python versions and platforms are not qualified for this optional exercise.
Run from the repository root. Installation needs access to PyPI; the running
lab and its HTTP requests stay on `127.0.0.1`.

```sh
LAB_ENV_DIR=$(mktemp -d)
python3.12 -m venv "$LAB_ENV_DIR/venv"
"$LAB_ENV_DIR/venv/bin/python" -m pip install \
  --require-hashes --only-binary=:all: \
  -r examples/local-backend/requirements-http.txt
```

Keep this terminal open. The environment is outside the repository. If your
platform has no matching pinned wheel or a hash check fails, stop and inspect
the dependency error; do not bypass hashes, add an unreviewed package source,
or install into your system Python to force the exercise through.

## 2. Start one short-lived lab session

```sh
"$LAB_ENV_DIR/venv/bin/python" -B examples/local-backend/http_lab.py
```

The script prints `LAB_URL` and `LAB_SESSION_DIR`, not raw tokens. It listens
only on `127.0.0.1` and chooses an available random port. Its lifetime is limited
to 900 seconds plus completion of a bounded in-flight request; **Ctrl+C** stops
it sooner. It creates its own private temporary SQLite database and three
synthetic subjects:

| Workspace | Subject | Initial role | Private curl configuration |
|---|---|---|---|
| `w-a` | `alice` | Owner | `alice.curl` |
| `w-a` | `amy` | Member | `amy.curl` |
| `w-b` | `bob` | Owner | `bob.curl` |

The configurations live inside the printed session directory with POSIX mode
`0600`. They contain bearer credentials for this local, short-lived session,
not credentials for OCI or any external account. The temporary RSA signing key
stays in memory. Tokens use issuer `https://local-lab.invalid` and audience
`oci-founder-local-backend`; that issuer is a fixed identifier, not a website
to visit or an identity service to contact.

## 3. Make requests from a second terminal

Copy the **exact values printed by your own running session** into these two
assignments. Replace the placeholders; do not guess a port, search other
users' temporary directories, or reuse values from an earlier run.

```sh
LAB_URL='PASTE_PRINTED_LAB_URL'
LAB_SESSION_DIR='PASTE_PRINTED_LAB_SESSION_DIR'
```

Each command below displays the HTTP status with `-i`. `-q` avoids loading a
default curl configuration, and `--noproxy '*'` bypasses proxy environment
settings for this local exercise. Keep the URL on the printed `127.0.0.1` port;
never send these configurations to an external URL or follow redirects.

Check anonymous health (**200**) and a business request without a token (**401**):

```sh
curl -q --noproxy '*' -i "$LAB_URL/healthz"
curl -q --noproxy '*' -i "$LAB_URL/workspaces"
```

List Alice's memberships (**200**, `w-a` only):

```sh
curl -q --config "$LAB_SESSION_DIR/alice.curl" \
  --noproxy '*' -i "$LAB_URL/workspaces"
```

Create one project (**201**), then list it (**200**):

```sh
curl -q --config "$LAB_SESSION_DIR/alice.curl" \
  --noproxy '*' -i -X POST \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: curl-project-1' \
  --data '{"name":"First local project"}' \
  "$LAB_URL/workspaces/w-a/projects"

curl -q --config "$LAB_SESSION_DIR/alice.curl" \
  --noproxy '*' -i "$LAB_URL/workspaces/w-a/projects"
```

Repeat the identical POST: expect the same **201** response snapshot and one
project, not two. Change its name while keeping the key: expect **409**.
The [application contract](README.md#application-contract) explains key scope.

Try accessing Alice's workspace with Bob's valid token (**403**):

```sh
curl -q --config "$LAB_SESSION_DIR/bob.curl" \
  --noproxy '*' -i "$LAB_URL/workspaces/w-a/projects"
```

A verified signature establishes a subject; it does **not** grant access to
another workspace. Current membership and role still control each operation.
Amy can use projects in `w-a`, but cannot promote herself or remove its owner.

Do not print or copy the configuration contents, put a bearer value directly
in a command, enable `curl -v`/trace or shell tracing, or attach credentials to
chat, logs, screenshots, issues, or commits. Config-file loading keeps the
bearer value out of the command arguments; it does not make the file public.

## 4. Run the optional checks

After stopping the interactive server, run these from the first terminal:

```sh
"$LAB_ENV_DIR/venv/bin/python" -B -m unittest discover \
  -s examples/local-backend/http-tests -v
"$LAB_ENV_DIR/venv/bin/python" -B examples/local-backend/http_smoke.py
```

The smoke exercise briefly opens its own loopback listener, performs local
checks, and stops it. Passing tests prove only the exercised local behavior,
not production authentication, internet-facing safety, or OCI qualification.

## 5. Stop, clean up, and understand the boundary

Press **Ctrl+C** in the server terminal, or allow its 15-minute session deadline
to pass. Shutdown may finish a bounded in-flight request; it is not an
instantaneous cutoff. Normal shutdown removes that run's temporary database
and credential files. A fresh run starts with new synthetic fixtures and new
signing material; there is no rollback or teardown of cloud resources.

A forced termination or machine crash may leave files. Identify the exact
printed session path before removing leftover synthetic data. The separate
virtual environment also remains in your exact `LAB_ENV_DIR`; remove that
specific directory when finished if you no longer need it. Never clean up
broad temporary, home, repository, tenancy, or account scopes.

This server is deliberately limited: strict local `Host`, rejected `Origin`
requests, no browser/CORS workflow, no public bind, no proxy or tunnel, and no
container-deployment path. Do not modify it to listen on `0.0.0.0` or expose it
to a network. Python explicitly does **not** recommend `http.server` for
production; see the [official Python warning](https://docs.python.org/3.12/library/http.server.html).

RS256 verification here checks locally issued test tokens, not a real user's
identity. There is no external issuer/JWKS integration, registration, login,
MFA, password recovery, TLS, key rotation service, production database,
centralized observability, or production availability/capacity evidence.
Continue with the [reference backend design](../../docs/REFERENCE-BACKEND.md)
before planning a real identity-provider and deployment integration.
