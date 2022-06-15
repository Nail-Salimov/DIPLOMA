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
from os.path import expanduser

def stop_server(srv1cv83, result, module):
    rc, stdout, stderr = module.run_command([srv1cv83, 'stop'])
    
    result['rc'] = rc
    
    if rc == 0:
        if stderr == 'Warning: server not running!\n':
            result['status'] = "Server not running!"
            module.exit_json(**result)
        elif stderr == '':
            result['changed'] = True
            result['status'] = "Server stopped"
            module.exit_json(**result)
        else:
            module.fail_json(msg=stderr.splitlines(), **result)           
    else:   	
    	module.fail_json(msg=stderr.splitlines(), **result)


def restart_server(srv1cv83, result, module):
    rc, stdout, stderr = module.run_command([srv1cv83, 'restart'])
    
    result['rc'] = rc
    
    if rc == 0:
        if stderr == 'Warning: server not running!\n':
            result['changed'] = True
            result['status'] = "Server started"
            result['message'] = "Server was down"
            module.exit_json(**result)
        elif stderr == '':
            result['changed'] = True
            result['status'] = "Server restarted"
            module.exit_json(**result)
        else:
            module.fail_json(msg=stderr.splitlines(), **result)           
    else:   	
    	module.fail_json(msg=stderr.splitlines(), **result)


def start_server(srv1cv83, result, module):
    rc, stdout, stderr = module.run_command([srv1cv83, 'start'])
    
    result['rc'] = rc
    
    if rc == 0:
        if stderr == 'Warning: already started!\n':
            result['status'] = "Server already started!"
            module.exit_json(**result)
        elif stderr == '':
            result['changed'] = True
            result['status'] = "Server started"
            module.exit_json(**result)
        else:
            module.fail_json(msg=stderr.splitlines(), **result)           
    else:   	
    	module.fail_json(msg=stderr.splitlines(), **result)


def status_server(srv1cv83, result, module):
    rc, stdout, stderr = module.run_command([srv1cv83, 'status'])
       
    result['rc'] = rc
    
    if rc == 0:
        result['status'] = [(stdout.splitlines()[1]).strip(), (stdout.splitlines()[2]).strip()] 
        module.exit_json(**result)
    else:
    	
    	module.fail_json(msg=stderr.splitlines(), **result)

    module.exit_json(**result)



def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        version=dict(type='str', required=False, default='8.3.20.1710'),
        srv1cv83_path=dict(type='str', required=False, default=None),
        state =dict(type='str', required=True)
    )

    result = dict(
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        module.exit_json(**result)

    version = module.params['version']
    srv1cv83_path = module.params['srv1cv83_path']
    state = module.params['state']
    
    path = '/opt/1cv8/x86_64/';
    srv1cv83_name = 'srv1cv83'
    
    srv1cv83 = None

    if not srv1cv83_path == None:
        srv1cv83 = srv1cv83_path
    else:
        srv1cv83 = path + version + "/" + srv1cv83_name
    
    if state == 'status':
        status_server(srv1cv83, result, module)
    elif state == 'start':
        start_server(srv1cv83, result, module)
    elif state == 'restart':
        restart_server(srv1cv83, result, module)
    elif state == 'stop':
        stop_server(srv1cv83, result, module)
    else:
        result['failed'] = True
        module.fail_json(msg='Не задан параметр state', **result)
    


def main():
    run_module()


if __name__ == '__main__':
    main()
