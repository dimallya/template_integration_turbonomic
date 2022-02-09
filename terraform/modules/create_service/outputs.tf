output "service_id" {
  description = "The ID of the service"
  value = lookup(camc_scriptpackage.create_service.result, "service_id")
}