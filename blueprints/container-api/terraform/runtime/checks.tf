# Deliberately no top-level `check` blocks: Terraform treats failed checks as
# warnings. The blocking network_cidr_contract is a lifecycle precondition on
# the VCN in network.tf so an invalid network cannot be planned or applied.
