#!/usr/bin/python
# =================================================================
# Copyright 2022 IBM Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =================================================================

import argparse
import json
import os
import requests
import sys
from urllib3.exceptions import InsecureRequestWarning

#####################################################################
# Supported Turbonomic group types                                  #
#####################################################################
VIRTUAL_MACHINE       = 'VirtualMachine'
VIRTUAL_MACHINE_LOWER = 'virtualmachine'
DATABASE              = 'Database'
DATABASE_LOWER        = 'database'
DATABASE_SERVER       = 'DatabaseServer'
DATABASE_SERVER_LOWER = 'databaseserver'

#####################################################################
# Custom IA scale action workflow display name                      #
#####################################################################
ia_workflow_name = 'IAScaleAction'

def get_authentication_cookie(host, user, password):
    '''
    Return an authentication cookie used for subsequent requests.
    
    Parameters:
        host     : URL for the Turbonomic server
        user     : Turbonomic user
        password : Turbonomic users password

    Returns:
        An authentication cookie
    '''
    print_to_stderr('Authenticating user ' + user + ' against host ' + host)
    auth_cookie = None

    endpoint = host + '/api/v3/login?username='+user+'&password='+password
    response = requests.post(endpoint, verify=False)
    if response.status_code == 200:
        auth_cookie = response.headers['set-cookie'].split(';')[0]
    else:
        print_to_stderr('Error ' + str(response.status_code) + ' authenticating user ' + user)

    return auth_cookie

def create_service(host, auth_cookie, name, group_ids):
    '''
    Create a Turbonomic service.
    
    Parameters:
        host        : URL for the Turbonomic server
        auth_cookie : Authorization cookie
        name        : Service name
        group_ids   : Comma separated list of groups to add to the service

    Returns:
        status_code : The HTTP status code for the request
        id          : The ID of the service, if created, or None
    '''
    print_to_stderr('Creating service ' + name + ' in host ' + host)

    id = None
    vm_groups = []
    db_server_groups = []

    endpoint = host + '/api/v3/topologydefinitions'
    headers = {'cookie': auth_cookie}

    # Validate the groups to be added to this service
    #   - Only 1 group of each type is supported
    for id in group_ids.split(','):
        if id != '':
            response = get_group(host, auth_cookie, id)
            if response['status_code'] != 200:
                return {'status_code':response['status_code'], 'id':id}
            type = response['details']['groupType']
            if type == VIRTUAL_MACHINE:
                vm_groups.append(id)
            elif type == DATABASE_SERVER:
                db_server_groups.append(id)
            else:
                print_to_stderr(type + ' groups can not be added to a service. Group ID ' + id + ' will be ignored')

    # Impose restrictions on groups
    if len(vm_groups) == 0 and len(db_server_groups) == 0:
        print_to_stderr('At least one group must be added to a service')
        return {'status_code':'400', 'id':id}

    if len(vm_groups) > 1:
        print_to_stderr('Only one VirtualMachine group can be added to a service')
        return {'status_code':'400', 'id':id}

    if len(db_server_groups) > 1:
        print_to_stderr('Only one DatabaseServer group can be added to a service')
        return {'status_code':'400', 'id':id}

    # Build the JSON request body
    body = {}
    body['displayName'] = name
    body['entityType'] = 'Service'
    body['entityDefinitionData'] = {}

    connected_groups = {}
    if len(vm_groups) == 1:
        connected_groups[VIRTUAL_MACHINE] = {
            "connectedGroup": {
                "uuid": vm_groups[0]
            }
        }

    if len(db_server_groups) == 1:
        connected_groups[DATABASE_SERVER] = {
            "connectedGroup": {
                "uuid": db_server_groups[0]
            }
        }

    body['entityDefinitionData']['manualConnectionData'] = connected_groups

    response = requests.post(endpoint, verify=False, headers=headers, json=body)
    if response.status_code == 200:
        id = response.json()['uuid']
        print_to_stderr('Service ' + name + ' was created successfully')
    else:
        print_to_stderr('Error ' + str(response.status_code) + ' creating service ' + name)
        print_to_stderr('response.txt: ' + response.text)

    return {'status_code':response.status_code, 'id':id}

def create_group(host, auth_cookie, name, type, tag_name, tag_value):
    '''
    Create a Turbonomic group (VirtualMachine, Database, or DatabaseServer).
    
    Parameters:
        host        : URL for the Turbonomic server
        auth_cookie : Authorization cookie
        name        : Group name
        type        : Group type - VirtualMachine, Database, or DatabaseServer
        tag_name    : Tag name to find resources to include in this group
        tag_value   : Tag value to find resources to include in this group

    Returns:
        status_code : The HTTP status code for the request
        id          : The ID of the group, if created, or None
    '''
    print_to_stderr('Creating group ' + name + ' with type ' + type + ' in host ' + host)

    id = None

    # Validate group type
    if type != VIRTUAL_MACHINE and type != DATABASE and type != DATABASE_SERVER:
        print_to_stderr('The specified group type "' + type +'" is not valid. Valid values are ' + VIRTUAL_MACHINE + ', ' + DATABASE + ', and ' + DATABASE_SERVER)
        return {'status_code':'400', 'id':id}

    expVal = tag_name+'='+tag_value
    filter_type = 'vmsByTag'
    if type == DATABASE_SERVER:
        filter_type = 'databaseServerByTag'
    elif type == DATABASE:
        filter_type = 'databaseByTag'

    endpoint = host + '/api/v3/groups'
    headers = {'cookie': auth_cookie}
    body = {
               'isStatic':False,
               'displayName':name,
               'memberUuidList':[],
               'criteriaList':[{'expType':'EQ','expVal':expVal,'filterType':filter_type,'caseSensitive':False}],
               'groupType':type
           }

    response = requests.post(endpoint, verify=False, headers=headers, json=body)
    if response.status_code == 200:
        id = response.json()['uuid']
        print_to_stderr('Group ' + name + ' with id ' + id + ' was created successfully')
    else:
        print_to_stderr('Error ' + str(response.status_code) + ' creating group ' + name)
        print_to_stderr('response.txt: ' + response.text)

    return {'status_code':response.status_code, 'id':id}

def create_ia_vm_scale_policy(host, auth_cookie, name, group_ids):
    '''
    Create a Turbonomic virtual machine policy and add it to a group.
    
    Parameters:
        host        : URL for the Turbonomic server
        auth_cookie : Authorization cookie
        name        : Policy name
        group_ids   : Comma separated list of groups to which this policy will be added

    Returns:
        status_code : The HTTP status code for the request
        id          : The ID of the policy, if created, or None
    '''
    print_to_stderr('Creating virtual machine policy "' + name + '" in host ' + host)

    endpoint = host + '/api/v3/settingspolicies'
    headers = {'cookie': auth_cookie}

    # Automation and Orchestration -> Action Types : overridden by this policy
    automation_settings = [{'uuid': 'cloudComputeScale', 'value': 'MANUAL'}]

    # Scaling Constraint that needs to be set for some reason
    market_settings = [{'uuid': 'ignoreNvmePreRequisite','value': True}]

    # Get the workflow ID for the custom virtual machine scale action
    ia_scale_action_workflow_id = get_workflow(host, auth_cookie, ia_workflow_name, 'VIRTUAL_MACHINE', 'SCALE')
    if ia_scale_action_workflow_id is None:
        return {'status_code':404}

    # Settings for workflows that replace native action handling
    control_settings = [{'uuid': 'cloudComputeScaleActionWorkflow', 'value': ia_scale_action_workflow_id}]

    # Get the groups (scope) to which this policy is to be added
    scopes = []
    if group_ids is not None:
        for id in group_ids.split(','):
            scopes.append( {'uuid':id} )
    body = {
               'disabled': False,
               'entityType': VIRTUAL_MACHINE,
               'displayName': name,
               'scopes': scopes,
               'settingsManagers': [
                   {'uuid': 'automationmanager',    'settings':automation_settings},
                   {'uuid': 'marketsettingsmanager','settings':market_settings},
                   {'uuid': 'controlmanager',       'settings':control_settings}
               ]
           }
    print_to_stderr('body for create policy REST API')
    print_to_stderr(json.dumps(body))
    id = None

    response = requests.post(endpoint, verify=False, headers=headers, json=body)
    if response.status_code == 200:
        id = response.json()['uuid']
        print_to_stderr('Virtual machine policy "' + name + '" was created successfully')
    else:
        print_to_stderr('Error ' + str(response.status_code) + ' creating virtual machine policy ' + name)
        print_to_stderr('response.txt: ' + response.text)

    return {'status_code':response.status_code, 'id':id}

def get_workflow(host, auth_cookie, name, entity_type, action_type):
    '''
    Get the ID for a Turbonomic workflow.
    
    Parameters:
        host        : URL for the Turbonomic server
        auth_cookie : Authorization cookie
        name        : The workflow display name
        entity_type : The workflow entity type
        action_type : The workflow action type

    Returns:
        workflow_id : The ID of the workflow, if found, or None
    '''
    print_to_stderr('Getting details for workflow with displayName ' + name + ' entity_type ' + entity_type + ' action_type ' + action_type)

    workflow_id = None

    endpoint = host + '/api/v3/workflows'
    headers = {'cookie': auth_cookie }
    response = requests.get(endpoint, verify=False, headers=headers)
    if response.status_code == 200:
        workflows = response.json()
        for wf in workflows:
            if wf['displayName'] == name and wf['entityType'] == entity_type and wf['actionType'] == action_type:
                workflow_id = wf['uuid']
                print_to_stderr('Workflow ' + name + ' was found')
                break
    else:
        print_to_stderr('Error ' + str(response.status_code) + ' getting workflow ' + name)
        print_to_stderr('response.txt: ' + response.text)
        return None
    
    if workflow_id is None:
        print_to_stderr('Workflow with displayName ' + name + ' does not exist')

    return workflow_id

def get_group(host, auth_cookie, id):
    '''
    Get details for a Turbonomic group.

    Parameters:
        host        : URL for the Turbonomic server
        auth_cookie : Authorization cookie
        id          : The ID of the group

    Returns:
        status_code : The HTTP status code for the request
        details     : The group details
    '''
    print_to_stderr('Getting details for group with id ' + id)

    details = None

    endpoint = host + '/api/v3/groups/'+id
    headers = {'cookie': auth_cookie }
    response = requests.get(endpoint, verify=False, headers=headers)
    if response.status_code == 200:
        details = response.json()
    else:
        print_to_stderr('Error ' + str(response.status_code) + ' getting group with id ' + id)
        print_to_stderr('response.txt: ' + response.text)

    return {'status_code':response.status_code, 'details':details}

def delete_group(host, auth_cookie, id):
    '''
    Delete a Turbonomic group.

    Parameters:
        host        : URL for the Turbonomic server
        auth_cookie : Authorization cookie
        id          : The ID of the group to delete

    Returns:
        status_code : The HTTP status code for the request
    '''
    print_to_stderr('Deleting group with id ' + id)
    endpoint = host + '/api/v3/groups'
    return delete_resource(endpoint, auth_cookie, 'Group', id)

def delete_service(host, auth_cookie, id):
    '''
    Delete a Turbonomic service.

    Parameters:
        host        : URL for the Turbonomic server
        auth_cookie : Authorization cookie
        id          : The ID of the service to delete

    Returns:
        status_code : The HTTP status code for the request
    '''
    print_to_stderr('Deleting service with id ' + id)
    endpoint = host + '/api/v3/topologydefinitions'
    return delete_resource(endpoint, auth_cookie, 'Service', id)

def delete_policy(host, auth_cookie, id):
    '''
    Delete a Turbonomic policy.

    Parameters:
        host        : URL for the Turbonomic server
        auth_cookie : Authorization cookie
        id          : The ID of the policy to delete

    Returns:
        status_code : The HTTP status code for the request
    '''

    print_to_stderr('Deleting policy with id ' + id)
    endpoint = host + '/api/v3/settingspolicies'
    return delete_resource(endpoint, auth_cookie, 'Policy', id)

def delete_resource(endpoint, auth_cookie, resource_type, id):
    '''
    Delete a Turbonomic resource.

    Parameters:
        endpoint      : Turbonomic REST API endpoint
        auth_cookie   : Authorization cookie
        resource_type : The resource type to delete. Used for logging.
        id            : The ID of the resource to delete

    Returns:
        status_code : The HTTP status code for the request
    '''
    endpoint = endpoint + '/' + id
    headers = {'cookie': auth_cookie}

    try_again = True
    attempted = 1
    while try_again:
        try_again = False
        response = requests.delete(endpoint, verify=False, headers=headers)
        if response.status_code == 200:
            print_to_stderr(resource_type + ' with id ' + id + ' was deleted successfully')
        elif response.status_code == 404:
            print_to_stderr(resource_type + ' with id ' + id + ' does not exist')
        else:
            # There is a race condition when deleting a service. If a group in the service
            # is deleted while the service is being deleted you may get a status code
            # 500 and the service is not deleted. To avoid any race conditions, attempt to
            # delete the resource a second time.
            if response.status_code == 500 and attempted == 1:
                print_to_stderr('Error 500 while deleting a ' + resource_type + ' with id ' + id + '. Try again.')
                attempted += 1
                try_again = True
            else:
                print_to_stderr('Error ' + str(response.status_code) + ' deleting ' + resource_type + ' with id ' + id)
                print_to_stderr('response.txt: ' + response.text)

    return response.status_code


def print_to_stderr(message):
    '''
    Write a message to stderr. The camc_scriptpackage Terraform 
    resource reads from stdout so we need to control what is sent
    to stdout.

    Parameters:
        message : The message to write
    '''
    # print >> sys.stderr, message
    print(message, file=sys.stderr)

#####################################################################
# Main                                                              #
#####################################################################
def main(argv=sys.argv):

    # Get connection information
    user = os.environ['TURBONOMIC_USER']
    password = os.environ['TURBONOMIC_PASSWORD']
    host = os.environ['TURBONOMIC_ENDPOINT']

    host = host.strip().rstrip('/')

    requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

    # Get the authentication cookie
    auth_cookie = get_authentication_cookie(host, user, password)
    if auth_cookie is None:
        return(1)

    # Process Command Line Parameters
    parser = argparse.ArgumentParser(
             description='Create resources in Turbonomic. ',
             epilog='')

    # Usage:
    # Create a service and add one or more groups to it.
    # -s service_name -G groupd_ids
    #
    # Create a group. Add entities to this group based on a tag and tag value.
    # -g group_name -T VirtualMachine|Database|DatabaseServer -t tag_nam> -v tag_value
    #
    # Create an IA Scale Action virtual machine policy and add it to one or more virtual machine groups
    # -p group_name -G group_ids
    #
    # Delete resources. Optionally specify a list of service, group, or policy ids to delete.
    # -d [-S service_ids] [-G groud_ids] [-P policy_ids]
    #
    parser.add_argument('-s', '--create_service', dest='service_name', default=None, required=False)
    parser.add_argument('-g', '--create_group', dest='group_name', default=None, required=False)
    parser.add_argument('-T', '--group_type', dest='group_type', default=None, required=False)
    parser.add_argument('-t', '--tag_name', dest='tag_name', required=False)
    parser.add_argument('-v', '--tag_value', dest='tag_value', required=False)
    parser.add_argument('-p', '--create_vm_policy', dest='vm_policy_name', default=None)
    parser.add_argument('-d', '--delete', action='store_true', default=False)
    parser.add_argument('-S', '--service_ids', dest='service_ids', default=None, required=False)
    parser.add_argument('-G', '--group_ids', dest='group_ids', default=None, required=False)
    parser.add_argument('-P', '--policy_ids', dest='policy_ids', default=None, required=False)

    args = parser.parse_args()

    service_name = args.service_name
    group_name = args.group_name
    group_type = args.group_type
    tag_name = args.tag_name
    tag_value = args.tag_value
    vm_policy_name = args.vm_policy_name
    delete = args.delete
    service_ids = args.service_ids
    group_ids = args.group_ids
    policy_ids = args.policy_ids

    # Validate arguments
    if service_name is not None and group_ids is None:
        print_to_stderr('Syntax error: To create a service at least one group id must be given')
        return(1)

    # Handle group type
    if group_type is not None:
        if group_type.lower() == VIRTUAL_MACHINE_LOWER:
            group_type = VIRTUAL_MACHINE
        elif group_type.lower() == DATABASE_LOWER:
            group_type = DATABASE
        elif group_type.lower() == DATABASE_SERVER_LOWER:
            group_type = DATABASE_SERVER

        if group_type != VIRTUAL_MACHINE and group_type != DATABASE and group_type != DATABASE_SERVER:
            print_to_stderr('The specified group type "' + type +'" is not valid. Valid values are ' + VIRTUAL_MACHINE + ', ' + DATABASE + ', and ' + DATABASE_SERVER)
            return(1)

    # Create group - check for required arguments
    if group_name is not None:
        error = False
        if group_type is None:
            print_to_stderr('Syntax error: "--create_group" requires "--group_type"')
            error = True

        if tag_name is None:
            print_to_stderr('Syntax error: "--create_group" requires "--tag_name"')
            error = True

        if tag_value is None:
            print_to_stderr('Syntax error: "--create_group" requires "--tag_value"')
            error = True

        if error:
            return(1)

    # Validate create policy arguments
    if vm_policy_name is not None:
        if group_ids is None:
            print_to_stderr('Syntax error: "--create_vm_policy" requires "--group_ids"')
            return(1)

    if delete:
        print_to_stderr('Deleting Turbnonomic resources...')

        # Delete Policies
        if policy_ids is not None:
            for id in policy_ids.split(','):
                status_code = delete_policy(host, auth_cookie, id)
                if status_code != 200 and status_code != 404:
                    return(1)

        # Delete Groups
        if group_ids is not None:
            for id in group_ids.split(','):
                status_code = delete_group(host, auth_cookie, id)
                if status_code != 200 and status_code != 404:
                    return(1)

        # Delete Service
        if service_ids is not None:
            for id in service_ids.split(','):
                status_code = delete_service(host, auth_cookie, id)
                if status_code != 200 and status_code != 404:
                    return(1)

    else:
        print_to_stderr('Creating Turbnonomic resources...')

        service_id = None
        group_id = None
        policy_id = None

        # Create a service and attach the specified groups
        if service_name is not None:
            status = create_service(host, auth_cookie, service_name, group_ids)
            if status['status_code'] != 200:
                return(1)
            service_id = status['id']
            print_to_stderr('Turbnonomic service ' + service_name + ' was created successfully')

        # Create a group and add entities based on tag name and value
        if group_name is not None:
            status = create_group(host, auth_cookie, group_name, group_type, tag_name, tag_value)
            if status['status_code'] != 200:
                return(1)
            group_id = status['id']
            print_to_stderr('Turbnonomic group ' + group_name + ' was created successfully')

        # Create a virtual machine policy scoped to group_ids
        if vm_policy_name is not None:
            status = create_ia_vm_scale_policy(host, auth_cookie, vm_policy_name, group_ids)
            if status['status_code'] != 200:
                return(1)
            policy_id = status['id']
            print_to_stderr('Turbnonomic policy ' + vm_policy_name + ' was created successfully')

        # Data returned to the camc_scriptpackage resource
        return_data = {
                           'service_id' : service_id,
                           'group_id'   : group_id,
                           'policy_id'  : policy_id
                      }
        print(json.dumps(return_data))

    return(0)

if __name__ == '__main__':
    sys.exit(main(sys.argv))
