output "group_id" {
  description = "The ID of the group"
  value = lookup(camc_scriptpackage.create_group.result, "group_id")
}