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

from ansible.module_utils.basic import AnsibleModule
from os.path import expanduser


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        version=dict(type='str', required=False, default='8.3.20.1710'),
        srv1cv83_path=dict(type='str', required=False, default=None),
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
    path = '/opt/1cv8/x86_64/';
    srv1cv83_name = 'srv1cv83'
    
    srv1cv83 = None

    if not srv1cv83_path == None:
        srv1cv83 = srv1cv83_path
    else:
        srv1cv83 = path + version + "/" + srv1cv83_name

    com_result = module.run_command([srv1cv83, 'start'])
    rc = com_result[0]
    stdout = com_result[1]
    stderr = com_result[2]
    
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


def main():
    run_module()


if __name__ == '__main__':
    main()
