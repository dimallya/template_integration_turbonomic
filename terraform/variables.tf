variable "create_database_group" {
  type = bool
  description = "Whether or not this service instance contains Azure SQL databases"
  default = false
}

variable "create_database_server_group" {
  type = bool
  description = "Whether or not this service instance contains database servers"
  default = false
}

variable "create_service" {
  type = bool
  description = "Whether or not to create a Turbonomic service"
  default = false
}

variable "create_virtual_machine_group" {
  type = bool
  description = "Whether or not this service instance contains virtual machines"
  default = false
}

variable "create_virtual_machine_policy" {
  type = bool
  description = "Whether or not to add a scale action policy to the virtual machine group"
  default = false
}
