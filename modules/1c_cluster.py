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

def get_cluster_list(module, result, full_path):
    command = full_path + "/rac cluster list"
    rc, out, err = module.run_command(command)
    
    result['rc'] = rc
    result['changed'] = False
    
    res = dict()
    for i in out.split('\n\n'):

        if len(i.strip()) > 0:
            res_sup = dict()
            for j in i.split('\n'):
                inner = list(map(str.strip, j.split(':')))
                if len(inner) > 1:
                    res_sup[inner[0]] = inner[1]

            cluster = res_sup['cluster']
            res[cluster] = res_sup
    

    if rc == 0:             
        result['clusters'] = res
        module.exit_json(**result)
    else:	
    	module.fail_json(msg=err.strip('\n'), **result)


def get_parameter(module, parameter, is_req):
    v = module.params[parameter]
    if v == None and is_req == True:
        module.fail_json(msg='Не задан парметр ' + parameter)
    else:
        return v


def create_admin(module, result, full_path):
    cluster_id = get_parameter(module, 'cluster_id', True)
    admin_name = get_parameter(module, 'admin_name', True)
    admin_pwd = get_parameter(module, 'admin_pwd', True)
    cluster_user = get_parameter(module, 'cluster_user', False)
    
    command = full_path + '/rac cluster admin --cluster="%s" register --name="%s" --pwd="%s" --auth=pwd' % (cluster_id, admin_name, admin_pwd)
    
    if cluster_user != None:
        cluster_pwd = get_parameter(module, 'cluster_pwd', True)
        command = command + (' --cluster-user="%s" --cluster-pwd="%s"' % (cluster_user, cluster_pwd))
    
    rc, out, err = module.run_command(command)
    
    result['rc'] = rc
    
    if rc == 0:
        
        result['message'] = 'Администратор кластера добавлен'
        module.exit_json(**result)
    else:
        module.fail_json(msg=(" ".join(err.split())), **result)
        
    

    
def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        version=dict(type='str', required=False, default='8.3.20.1710'),
        c1_path=dict(type='str', required=False, default=None),
        state=dict(type='str', required=True),
        
        cluster_id=dict(type='str', required=False, default=None),
        admin_name=dict(type='str', required=False, default=None),
        admin_pwd=dict(type='str', required=False, default=None),
        cluster_user=dict(type='str', required=False, default=None),
        cluster_pwd=dict(type='str', required=False, default=None),
        
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
    if state == 'start_rac':
        start_ras_daemon_cluster(module, result, full_c1_path, True)
    elif state == 'list':
        get_cluster_list(module, result, full_c1_path)
    elif state == 'admin':
        create_admin(module, result, full_c1_path)
    else:
        module.fail_json(msg='Некорректный параметр state', **result)
    
    
    
    
    


def main():
    run_module()


if __name__ == '__main__':
    main()
