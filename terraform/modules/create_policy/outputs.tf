output "policy_id" {
  description = "The ID of the policy"
  value = lookup(camc_scriptpackage.create_policy.result, "policy_id")
}