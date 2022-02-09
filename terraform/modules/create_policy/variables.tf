variable "name" {
  type = string
  description = "The name of the virtual machine policy"
}

variable "group_ids" {
  type = string
  description = "Comma separated list of group ids to which this policy is to be added"
}