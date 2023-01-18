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
# Create a service                           #
##############################################
resource "camc_scriptpackage" "create_service" {
  program = ["/usr/bin/python3", "${path.module}/../scripts/turbonomic_server.py", "-s", "${var.name}", "-G", "${var.group_ids}"]
  on_create = true
}

##############################################
# Delete a service                           #
##############################################
resource "camc_scriptpackage" "delete_service" {
  depends_on = [camc_scriptpackage.create_service]
  program = ["/usr/bin/python3", "${path.module}/../scripts/turbonomic_server.py", "-d", "-S", lookup(camc_scriptpackage.create_service.result, "service_id")]
  on_delete = true
}
