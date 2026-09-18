# Forward evaluation: FastAPI from Cloud Run

- Date: 2026-09-17
- Related fixture: `translate-cloud-run` plus the `orient-fastapi-aws` planning contract
- Evaluator: independent agent review
- Environment: repository-only; no OCI tenancy or application repository was available
- Mutation attempted: none
- Result: pass with reservations

## What passed

- Treated repository facts separately from the user's description.
- Selected Container API only as a provisional path.
- Explicitly stated that Container Instances is not a Cloud Run equivalent.
- Preserved PostgreSQL engine compatibility as a separate qualification step.
- Included identity, networking, secrets, cost drivers, observability, approval
  gates, rollback, and exact-target teardown.
- Performed no repository or cloud mutation.

## Reservations found

- The initial skill lacked a precise Cloud Run feature-parity gate before
  recommending Container Instances.
- No reviewed upstream skill currently covers general Container Instances, API
  Gateway, Load Balancer, or OCI Database with PostgreSQL procedures.
- The ten-section plan contract can be heavy before the user answers the first
  material questions.

## Follow-up incorporated

`references/golden-paths.md` now requires an inventory of scaling, concurrency,
timeout, scale-to-zero, streaming, background-work, and rollout behavior before
selecting Container Instances for a Cloud Run migration. The upstream-routing
reference now labels the uncovered service procedures as documentation-led gaps.
