variable "name" {
  type = string
  description = "The name of the service"
}

variable "type" {
  type = string
  description = "The group type"
}

variable "tag_name" {
  type = string
  description = "Resources with this tag name and value are added to the group"
}

variable "tag_value" {
  type = string
  description = "Resources with this tag name and value are added to the group"
}