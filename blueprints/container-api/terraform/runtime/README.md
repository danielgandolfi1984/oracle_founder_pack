# Runtime stack

This is the sandbox workload half of the [Container API field preview](../../README.md). It creates the network, private Container Instance, API Gateway, gateway service logs, metrics alarms, and notification subscription.

The runtime expects a private OCIR image from the bootstrap-approved repository, already pushed by immutable digest, and contains no IAM resource. The sample application cannot access a resource principal. It is one-instance evaluation infrastructure, not a production or availability design.
