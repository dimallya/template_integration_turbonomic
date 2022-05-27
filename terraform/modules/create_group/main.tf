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
# Create a group                             #
##############################################
resource "camc_scriptpackage" "create_group" {
  program = ["/usr/bin/python", "${path.module}/../scripts/turbonomic_server.py", "-g", "${var.name}", "-T", "${var.type}", "-t", "${var.tag_name}", "-v", "${var.tag_value}"]
  on_create = true
}

##############################################
# Delete a group                             #
##############################################
resource "camc_scriptpackage" "delete_group" {
  depends_on = [camc_scriptpackage.create_group]
  program = ["/usr/bin/python", "${path.module}/../scripts/turbonomic_server.py", "-d", "-G", lookup(camc_scriptpackage.create_group.result, "group_id")]
  on_delete = true
}
