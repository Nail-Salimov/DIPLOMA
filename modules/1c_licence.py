#!/usr/bin/python3.8

from __future__ import (absolute_import, division, print_function)
import base64

__metaclass__ = type

DOCUMENTATION = r'''
---
module: install_1c
short_description: 1c installation module
# If this is part of a collection, you need to use semantic versioning,
# i.e. the version is of the form "2.5.0" and not "2.4".
version_added: "1.0.0"
description: This is my longer description explaining my test module.
options:
    name:
        description: This is the message to send to the test module.
        required: true
        type: str
    new:
        description:
            - Control to demo if the result of this module is changed or not.
            - Parameter description can be a list as well.
        required: false
        type: bool
# Specify this value according to your collection
# in format of namespace.collection.doc_fragment_name
extends_documentation_fragment:
    - my_namespace.my_collection.my_doc_fragment_name
author:
    - Your Name (@yourGitHubHandle)
'''

EXAMPLES = r'''
# Pass in a message
- name: Test with a message
  my_namespace.my_collection.base64mod:
    name: hello world
# pass in a message and have changed true
- name: Test with a message and changed output
  my_namespace.my_collection.base64mod:
    name: hello world
    new: true
# fail the module
- name: Test failure of the module
  my_namespace.my_collection.base64mod:
    name: fail me
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
original_message:
    description: The original name param that was passed in.
    type: str
    returned: always
    sample: 'hello world'
message:
    description: The output message that the base64mod module generates.
    type: str
    returned: always
    sample: 'goodbye'
'''

from ansible.module_utils.basic import AnsibleModule
import os


def get_full_c1_path(version, c1_path):
    
    default_version_path = '/opt/1cv8/x86_64/'
    
    if not c1_path == None:
        return c1_path
    else:  
        return default_version_path + "/" + version 

def start_ras_daemon_cluster(module, result, full_path, is_req):
    command = full_path + "/ras --daemon cluster"
    rc, out, err = module.run_command(command)
    
    result['rc'] = rc

    if rc == 0 and is_req:             
        result['changed'] = True
        result['message'] = "Запущено"
        module.exit_json(**result)
    elif rc == 0 and not is_req:
        a = 1
    else:	
    	module.fail_json(msg=err.strip('\n'), **result)
    	

def get_parameter(module, parameter, is_req):
    v = module.params[parameter]
    if v == None and is_req == True:
        module.fail_json(msg='Не задан парметр ' + parameter)
    else:
        return v


def get_sub_command(command, parameter):
    if parameter is None:
        return ''
    else:
        return ' ' + command + '="' + parameter + '"'


def install_licence_server(module, result, full_path):
    cluster_id = get_parameter(module, 'cluster_id', True)
    agent_host = get_parameter(module, 'agent_host', False)
    agent_port = get_parameter(module, 'agent_port', False)
    port_range = get_parameter(module, 'port_range', False)
    name = get_parameter(module, 'name', False)
    using = get_parameter(module, 'using', False)
    cluster_user = get_parameter(module, 'cluster_user', True)
    cluster_pwd = get_parameter(module, 'cluster_pwd', True)
    
    command = full_path + '/rac server --cluster=%s insert' % (cluster_id)
    command = command + get_sub_command('--agent-host', agent_host)
    command = command + get_sub_command('--agent-port', agent_port)
    command = command + get_sub_command('--port-range', port_range)
    command = command + get_sub_command('--name', name)
    command = command + get_sub_command('--using', using)
    command = command + get_sub_command('--cluster-user', cluster_user)
    command = command + get_sub_command('--cluster-pwd', cluster_pwd)
    
    rc, out, err = module.run_command(command)
    
    result['rc'] = rc
    
    if not rc == 0:
        module.fail_json(msg=(" ".join(err.split())), **result)
    
    server_id = (out.split(":")[1]).strip()
    
    command2 = full_path + '/rac rule --cluster=%s insert --server=%s --position=0 --object-type=LicenseService --rule-type=always' % (cluster_id, server_id)
    command2 = command2 + get_sub_command('--cluster-user', cluster_user)
    command2 = command2 + get_sub_command('--cluster-pwd', cluster_pwd)
    
    command3 = full_path + '/rac rule --cluster=%s insert --server=%s --position=1 --rule-type=never' % (cluster_id, server_id)
    command3 = command3 + get_sub_command('--cluster-user', cluster_user)
    command3 = command3 + get_sub_command('--cluster-pwd', cluster_pwd)
    
    rc, out, err = module.run_command(command2)
    if not rc == 0:
        module.fail_json(msg=(" ".join(err.split())), **result)
    
    rc, out, err = module.run_command(command3)
    if not rc == 0:
        module.fail_json(msg=(" ".join(err.split())), **result)
    
    result['changed'] = True
    result['message'] =  "Сервер лицензирования создан"
    module.exit_json(**result)


def ring_acquire(module, result, full_path):
    request_file= get_parameter(module, 'request_file', True)
    response_file= get_parameter(module, 'response_file', True)
    conf_location= get_parameter(module, 'conf_location', False)
    send_statistics= get_parameter(module, 'send_statistics', True)
    
    send_statistics_str = None
    
    if send_statistics:
        send_statistics_str = 'true'
    else:
        send_statistics_str = 'false'
    
    command = full_path + '/ring license acquire --request "%s" --response "%s" --send-statistics "%s"' % (request_file, response_file, send_statistics_str)
    
    if not conf_location == None:
        command = command + (' --conf-location "%s"' % conf_location)
    
    rc, out, err = module.run_command(command)
    if not rc == 0:
        result['out'] = out
        module.fail_json(msg=(" ".join(err.split())), **result)
    
    result['changed'] = True
    result['message'] =  out
    module.exit_json(**result)


def ring_generate(module, result, full_path):
    request_file= get_parameter(module, 'request_file', True)
    response_file= get_parameter(module, 'response_file', True)
    license_file= get_parameter(module, 'license_file', True)
    send_statistics= get_parameter(module, 'send_statistics', True)
    
    send_statistics_str = None
    
    if send_statistics:
        send_statistics_str = 'true'
    else:
        send_statistics_str = 'false'
    
    command = full_path + '/ring license acquire --request "%s" --response "%s" --send-statistics "%s" --license "%s"' % (request_file, response_file, send_statistics_str, license_file)
    
    rc, out, err = module.run_command(command)
    if not rc == 0:
        result['out'] = out
        module.fail_json(msg=(" ".join(err.split())), **result)
    
    result['changed'] = True
    result['message'] =  out
    module.exit_json(**result)

def ring_get(module, result, full_path):
    name= get_parameter(module, 'name', True)
    path= get_parameter(module, 'path', True)
    license_file= get_parameter(module, 'license_file', True)
    send_statistics= get_parameter(module, 'send_statistics', True)
    
    send_statistics_str = None
    
    if send_statistics:
        send_statistics_str = 'true'
    else:
        send_statistics_str = 'false'
    
    command = full_path + '/ring license get --name "%s" --license "%s" --path "%s" --send-statistics "%s"' % (name, license_file, path, send_statistics)
    
    rc, out, err = module.run_command(command)
    if not rc == 0:
        result['out'] = out
        module.fail_json(msg=(" ".join(err.split())), **result)
    
    result['changed'] = True
    result['message'] =  out
    module.exit_json(**result)


def ring_info(module, result, full_path):
    name= get_parameter(module, 'name', True)
    path= get_parameter(module, 'path', True)
    send_statistics= get_parameter(module, 'send_statistics', True)
    
    send_statistics_str = None
    
    if send_statistics:
        send_statistics_str = 'true'
    else:
        send_statistics_str = 'false'
    
    command = full_path + '/ring license info --name "%s" --path "%s" --send-statistics "%s"' % (name, path, send_statistics)
    
    rc, out, err = module.run_command(command)
    if not rc == 0:
        result['out'] = out
        module.fail_json(msg=(" ".join(err.split())), **result)
    
    result['changed'] = True
    result['message'] =  out
    module.exit_json(**result)


def ring_list(module, result, full_path):

    path= get_parameter(module, 'path', True)
    send_statistics= get_parameter(module, 'send_statistics', True)
    
    send_statistics_str = None
    
    if send_statistics:
        send_statistics_str = 'true'
    else:
        send_statistics_str = 'false'
    
    command = full_path + '/ring license list --path "%s" --send-statistics "%s"' % (path, send_statistics)
    
    rc, out, err = module.run_command(command)
    if not rc == 0:
        result['out'] = out
        module.fail_json(msg=(" ".join(err.split())), **result)
    
    result['changed'] = True
    result['message'] =  out
    module.exit_json(**result)
     

def ring_put(module, result, full_path):
    license_file= get_parameter(module, 'license_file', True)
    path= get_parameter(module, 'path', True)
    send_statistics= get_parameter(module, 'send_statistics', True)
    
    send_statistics_str = None
    
    if send_statistics:
        send_statistics_str = 'true'
    else:
        send_statistics_str = 'false'
    
    command = full_path + '/ring license put --license "%s" --path "%s" --send-statistics "%s"' % (license_file, path, send_statistics)
    
    rc, out, err = module.run_command(command)
    if not rc == 0:
        result['out'] = out
        module.fail_json(msg=(" ".join(err.split())), **result)
    
    result['changed'] = True
    result['message'] =  out
    module.exit_json(**result)


def ring_remove(module, result, full_path):
    name= get_parameter(module, 'name', True)
    path= get_parameter(module, 'path', True)
    send_statistics= get_parameter(module, 'send_statistics', True)
    remove_all= get_parameter(module, 'remove_all', True)
    
    
    send_statistics_str = None
    
    if send_statistics:
        send_statistics_str = 'true'
    else:
        send_statistics_str = 'false'
    
    command = full_path + '/ring license remove --name "%s" --path "%s" --send-statistics "%s"' % (name, path, send_statistics)
    
    if remove_all:
        command = command + " --all"
    
    rc, out, err = module.run_command(command)
    if not rc == 0:
        result['out'] = out
        module.fail_json(msg=(" ".join(err.split())), **result)
    
    result['changed'] = True
    result['message'] =  out
    module.exit_json(**result)


def ring_validate(module, result, full_path):
    name= get_parameter(module, 'name', True)
    path= get_parameter(module, 'path', True)
    send_statistics= get_parameter(module, 'send_statistics', True)
    
    send_statistics_str = None
    
    if send_statistics:
        send_statistics_str = 'true'
    else:
        send_statistics_str = 'false'
    
    command = full_path + '/ring license validate --name "%s" --path "%s" --send-statistics "%s"' % (name, path, send_statistics)
    
    rc, out, err = module.run_command(command)
    if not rc == 0:
        result['out'] = out
        module.fail_json(msg=(" ".join(err.split())), **result)
    
    result['changed'] = True
    result['message'] =  out
    module.exit_json(**result)


def ring_prepare_request(module, result, full_path):
        first_name= get_parameter(module, 'first_name', True)
        middle_name= get_parameter(module, 'middle_name', True)
        last_name= get_parameter(module, 'last_name', True)
        email= get_parameter(module, 'email', True)
        company= get_parameter(module, 'company', True)
        country= get_parameter(module, 'country', True)
        zip_code= get_parameter(module, 'zip_code', True)
        region= get_parameter(module, 'region', True)
        district= get_parameter(module, 'district', True)
        town= get_parameter(module, 'town', True)
        street= get_parameter(module, 'street', True)
        house= get_parameter(module, 'house', True)
        building= get_parameter(module, 'building', True)
        apartment= get_parameter(module, 'apartment', True)
        serial= get_parameter(module, 'serial', True)
        pin= get_parameter(module, 'pin', True)
        previos_pin= get_parameter(module, 'previos_pin', True)
        path= get_parameter(module, 'path', True)
        validate= get_parameter(module, 'validate', False)
        conf_location= get_parameter(module, 'conf_location', True)
        send_statistics= get_parameter(module, 'cluster_id', True)
        
        command = full_path + '/ring license prepare-request'
        command = command + get_sub_command('--first-name', first_name)
        command = command + get_sub_command('--middle-name', middle_name)
        command = command + get_sub_command('--last-name', last_name)
        command = command + get_sub_command('--email', email)     
        command = command + get_sub_command('--company', company)
        command = command + get_sub_command('--country', country)
        command = command + get_sub_command('--zip-code', zip_code)
        command = command + get_sub_command('--region', region)
        command = command + get_sub_command('--district', district)
        command = command + get_sub_command('--town', town)        
        command = command + get_sub_command('--street', street)
        command = command + get_sub_command('--house', house)
        command = command + get_sub_command('--building', building)
        command = command + get_sub_command('--apartment', apartment)
        command = command + get_sub_command('--serial', serial)
        command = command + get_sub_command('--pin', pin)
        command = command + get_sub_command('--previos-pin', previos_pin)        
        command = command + get_sub_command('--path', path)
        command = command + get_sub_command('--conf-location', conf_location)
        command = command + get_sub_command('--send-statistics', send_statistics)
        
        if vaildate:
            command = command + ' --validate'
            
        rc, out, err = module.run_command(command)
        if not rc == 0:
            result['out'] = out
            module.fail_json(msg=(" ".join(err.split())), **result)
    
        result['changed'] = True
        result['message'] =  out
        module.exit_json(**result)


def ring_activate(module, result, full_path):
        first_name= get_parameter(module, 'first_name', True)
        middle_name= get_parameter(module, 'middle_name', True)
        last_name= get_parameter(module, 'last_name', True)
        email= get_parameter(module, 'email', True)
        company= get_parameter(module, 'company', True)
        country= get_parameter(module, 'country', True)
        zip_code= get_parameter(module, 'zip_code', True)
        region= get_parameter(module, 'region', True)
        district= get_parameter(module, 'district', True)
        town= get_parameter(module, 'town', True)
        street= get_parameter(module, 'street', True)
        house= get_parameter(module, 'house', True)
        building= get_parameter(module, 'building', True)
        apartment= get_parameter(module, 'apartment', True)
        serial= get_parameter(module, 'serial', True)
        pin= get_parameter(module, 'pin', True)
        previos_pin= get_parameter(module, 'previos_pin', True)
        validate= get_parameter(module, 'validate', False)
        
        command = full_path + '/ring license activate'
        command = command + get_sub_command('--first-name', first_name)
        command = command + get_sub_command('--middle-name', middle_name)
        command = command + get_sub_command('--last-name', last_name)
        command = command + get_sub_command('--email', email)     
        command = command + get_sub_command('--company', company)
        command = command + get_sub_command('--country', country)
        command = command + get_sub_command('--zip-code', zip_code)
        command = command + get_sub_command('--region', region)
        command = command + get_sub_command('--district', district)
        command = command + get_sub_command('--town', town)        
        command = command + get_sub_command('--street', street)
        command = command + get_sub_command('--house', house)
        command = command + get_sub_command('--building', building)
        command = command + get_sub_command('--apartment', apartment)
        command = command + get_sub_command('--serial', serial)
        command = command + get_sub_command('--pin', pin)
        command = command + get_sub_command('--previos-pin', previos_pin)        
        
        if vaildate:
            command = command + ' --validate'
            
        rc, out, err = module.run_command(command)
        if not rc == 0:
            result['out'] = out
            module.fail_json(msg=(" ".join(err.split())), **result)
    
        result['changed'] = True
        result['message'] =  out
        module.exit_json(**result)

    
def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        version=dict(type='str', required=False, default='8.3.20.1710'),
        c1_path=dict(type='str', required=False, default=None),
        state=dict(type='str', required=True),
        
        cluster_id=dict(type='str', required=False, default=None),
        agent_host=dict(type='str', required=False, default=None),
        agent_port=dict(type='str', required=False, default=None),
        port_range=dict(type='str', required=False, default=None),
        name=dict(type='str', required=False, default=None),
        using=dict(type='str', required=False, default=None),
        cluster_user=dict(type='str', required=False, default=None),
        cluster_pwd=dict(type='str', required=False, default=None),
        
        request_file=dict(type='str', required=False, default=None),
        response_file=dict(type='str', required=False, default=None),
        conf_location=dict(type='str', required=False, default=None),
        send_statistics=dict(type='bool', required=False, default=True),
        
        first_name=dict(type='str', required=False, default=None),
        middle_name=dict(type='str', required=False, default=None),
        last_name=dict(type='str', required=False, default=None),
        email=dict(type='str', required=False, default=None),
        company=dict(type='str', required=False, default=None),
        country=dict(type='str', required=False, default=None),
        zip_code=dict(type='str', required=False, default=None),
        region=dict(type='str', required=False, default=None),
        district=dict(type='str', required=False, default=None),
        town=dict(type='str', required=False, default=None),
        street=dict(type='str', required=False, default=None),
        house=dict(type='str', required=False, default=None),
        building=dict(type='str', required=False, default=None),
        apartment=dict(type='str', required=False, default=None),
        serial=dict(type='str', required=False, default=None),
        pin=dict(type='str', required=False, default=None),
        previos_pin=dict(type='str', required=False, default=None),
        path=dict(type='str', required=False, default=None),
        validate=dict(type='bool', required=False, default=False),
        
        license_file=dict(type='str', required=False, default=None),
        
        delete_all=dict(type='bool', required=False, default=False),
        
        force=dict(type='bool', required=False, default=False),

    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    
    result = dict(
    )
    
    if module.check_mode:
        module.exit_json(**result)
        
    version = module.params['version']
    c1_path = module.params['c1_path']    
    full_c1_path = get_full_c1_path(version, c1_path)
    c1_path_is_exist = os.path.exists(full_c1_path)
    if c1_path_is_exist == False:
        msg = "Путь " + full_c1_path + " недоступен или неверен"
        module.fail_json(msg=msg, **result)
    
    state = module.params['state']
    if state == 'create_server':
        install_licence_server(module, result, full_c1_path)
    elif state == 'ring_acquire':
        ring_acquire(module, result, full_c1_path)  
    elif state == 'ring_activate':
        ring_activate(module, result, full_c1_path)  
    elif state == 'ring_generate':
        ring_generate(module, result, full_c1_path)  
    elif state == 'ring_get':
        ring_get(module, result, full_c1_path)  
    elif state == 'ring_info':
        ring_info(module, result, full_c1_path)  
    elif state == 'ring_list':
        ring_list(module, result, full_c1_path)
    elif state == 'ring_prepare_request':
        ring_prepare_request(module, result, full_c1_path)
    elif state == 'ring_put':
        ring_put(module, result, full_c1_path)
    elif state == 'ring_remove':
        ring_remove(module, result, full_c1_path)
    elif state == 'ring_validate':
        ring_validate(module, result, full_c1_path)     
    else:
        module.fail_json(msg='Некорректный параметр state', **result)
    
    
    
    


def main():
    run_module()


if __name__ == '__main__':
    main()
