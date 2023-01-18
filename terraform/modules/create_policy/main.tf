terraform {
  required_version = "~> 1"

  required_providers {
    camc = {
      source  = "registry.ibm.com/cam/camc"
      version = "~> 0.2"
    }
  }
}

##############################################
# Create a virtual machine policy            #
##############################################
resource "camc_scriptpackage" "create_policy" {
  program = ["/usr/bin/python3", "${path.module}/../scripts/turbonomic_server.py", "-p", "${var.name}", "-G", "${var.group_ids}"]
  on_create = true
}

##############################################
# Delete a virtual machine policy            #
##############################################
resource "camc_scriptpackage" "delete_policy" {
  depends_on = [camc_scriptpackage.create_policy]
  program = ["/usr/bin/python3", "${path.module}/../scripts/turbonomic_server.py", "-d", "-P", lookup(camc_scriptpackage.create_policy.result, "policy_id")]
  on_delete = true
}
