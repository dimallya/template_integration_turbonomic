terraform {
  required_version = "~> 1"

  required_providers {
    camc = {
      source  = "registry.ibm.com/cam/camc"
      version = "~> 0.2"
    }
  }
}

provider "camc" { }

##########################################################
# Get service instance values from camtags               #
##########################################################
module "camtags" {
  source  = "../Modules/camtags"
}

locals {
  service_instance_name = [
    for k, v in module.camtags.tagsmap : v
    if k  == "service_name"
  ]
  service_instance_identifier = [
    for k, v in module.camtags.tagsmap : v
    if k  == "service_identifier"
  ]

  # Names for Turbonomic resources
  service_name                 = "IA-${element(local.service_instance_name, 0)}-${element(local.service_instance_identifier, 0)}"
  virtual_machine_group_name   = "${local.service_name}-virtual-machines"
  database_group_name          = "${local.service_name}-databases"
  database_server_group_name   = "${local.service_name}-database-servers"
  virtual_machine_policy_name  = local.service_name

  # Tag filter for group resources
  tag_name  = "service_identifier"
  tag_value = element(local.service_instance_identifier, 0)  
}

############################################################
# Conditionally create a Turbonomic virtual machine group  #
############################################################
module "create_virtual_machine_group" {
  count     = var.create_virtual_machine_group ? 1 : 0
  source    = "./modules/create_group"
  name      = local.virtual_machine_group_name
  type      = "VirtualMachine"
  tag_name  = local.tag_name
  tag_value = local.tag_value
}

############################################################
# Conditionally create a Turbonomic database group         #
############################################################
module "create_database_group" {
  count     = var.create_database_group ? 1 : 0
  source    = "./modules/create_group"
  name      = local.database_group_name
  type      = "Database"
  tag_name  = local.tag_name
  tag_value = local.tag_value
}

############################################################
# Conditionally create a Turbonomic database server group  #
############################################################
module "create_database_server_group" {
  count     = var.create_database_server_group ? 1 : 0
  source    = "./modules/create_group"
  name      = local.database_server_group_name
  type      = "DatabaseServer"
  tag_name  = local.tag_name
  tag_value = local.tag_value
}

############################################################
# Conditionally create a Turbonomic virtual machine policy #
############################################################
module "create_virtual_machine_policy" {
  count     = var.create_virtual_machine_policy && var.create_virtual_machine_group ? 1 : 0
  source    = "./modules/create_policy"
  name      = local.virtual_machine_policy_name
  group_ids = module.create_virtual_machine_group[0].group_id
}

############################################################
# Conditionally create a Turbonomic service                #
############################################################
module "create_service" {
  depends_on = [module.create_virtual_machine_group, module.create_database_server_group]
  count      = var.create_service && (var.create_virtual_machine_group || var.create_database_server_group) ? 1 : 0
  source     = "./modules/create_service"
  name       = local.service_name
  group_ids  = format("%s,%s", var.create_virtual_machine_group ? module.create_virtual_machine_group[0].group_id : "", var.create_database_server_group ? module.create_database_server_group[0].group_id : "")
}
