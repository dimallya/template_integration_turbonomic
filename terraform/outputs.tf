output "database_group_id" {
  description = "The ID of the Turbonomic database group"
  value = var.create_database_group ? module.create_database_group[0].group_id : "No database group created"
}

output "database_group_name" {
  description = "The name of the Turbonomic database group"
  value = var.create_database_group ? local.database_group_name: "No database group created"
}

output "database_server_group_id" {
  description = "The ID of the Turbonomic database server group"
  value = var.create_database_server_group ? module.create_database_server_group[0].group_id : "No database server group created"
}

output "database_server_group_name" {
  description = "The name of the Turbonomic database server group"
  value = var.create_database_server_group ? local.database_server_group_name: "No database server group created"
}

output "service_id" {
  description = "The ID of the Turbonomic service"
  value = var.create_service && (var.create_virtual_machine_group || var.create_database_server_group) ? module.create_service[0].service_id : "No service created"
}

output "service_name" {
  description = "The name of the Turbonomic service"
  value = var.create_service && (var.create_virtual_machine_group || var.create_database_server_group) ? local.service_name : "No service created"
}

output "virtual_machine_group_id" {
  description = "The ID of the Turbonomic virtual machine group"
  value = var.create_virtual_machine_group ? module.create_virtual_machine_group[0].group_id : "No virtual machine group created"
}

output "virtual_machine_group_name" {
  description = "The name of the Turbonomic virtual machine group"
  value = var.create_virtual_machine_group ? local.virtual_machine_group_name : "No virtual machine group created"
}

output "virtual_machine_policy_id" {
  description = "The ID of the Turbonomic virtual machine policy"
  value = var.create_virtual_machine_policy && var.create_virtual_machine_group ? module.create_virtual_machine_policy[0].policy_id : "No virtual machine policy created"
}

output "virtual_machine_policy_name" {
  description = "The name of the Turbonomic virtual machine policy"
  value = var.create_virtual_machine_policy && var.create_virtual_machine_group ? local.virtual_machine_policy_name : "No virtual machine policy created"
}
