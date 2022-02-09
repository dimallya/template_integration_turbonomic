# Turbonomic Integration
Copyright IBM Corp. 2022

This code is released under the Apache 2.0 License.

## Overview
This template automates the creation of Turbonomic resources. These resources enable you to gain insights and take action on the cloud resources provisioned by a service.

## Prerequisites
1. A Turbonomic instance
2. A Turbonomic cloud connection
3. The Turbonomic instance must be network accessible from the Terraform Runtime Service.

## Turbonomic Resources Managed
1. Service
2. Database group
3. Database server group
4. Virtual machine group
5. Virtual machine scale action policy

## Usage and Special Notes
1. This template is intended to be used in a service, not as a standalone template.
2. In order for cloud resources to be included in a Turbonomic group they must have the **service_name** and **service_identifier** tags applied.

## Input Parameters

| Input                         | Description                                                                                                 |
| ----------------------------- | ----------------------------------------------------------------------------------------------------------- |
| create_database_group         | Whether or not to create a Turbonomic group that references the Azure SQL databases created by this service |
| create_database_server_group  | Whether or not to create a Turbonomic group that references the database servers created by this service    |
| create_service                | Whether or not to create a Turbonomic service for this service instance                                     |
| create_virtual_machine_group  | Whether or not to create a Turbonomic group that references the virtual machines created by this service    |
| create_virtual_machine_policy | Whether or not to add the custom IA scale action policy to the virtual machine group                        |

## Output Parameters

| Output                      | Description                                      |
| --------------------------- | ------------------------------------------------ |
| database_group_id           | The ID of the Turbonomic database group          |
| database_group_name         | The name of the Turbonomic database group        |
| database_server_group_id    | The ID of the Turbonomic database server group   |
| database_server_group_name  | The name of the Turbonomic database server group |
| service_id                  | The ID of the Turbonomic service                 |
| service_name                | The name of the Turbonomic service               |
| virtual_machine_group_id    | The ID of the Turbonomic virtual machine group   |
| virtual_machine_group_name  | The name of the Turbonomic virtual machine group |
| virtual_machine_policy_id   | The ID of the Turbonomic virtual machine policy  |
| virtual_machine_policy_name | The ID of the Turbonomic virtual machine policy  |
