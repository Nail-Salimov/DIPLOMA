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
import subprocess
import os
import requests
from os.path import expanduser

def execute_command(command, module, result, req):
    p = subprocess.run(command, universal_newlines=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0 and req:
        if p.stdout == '':
            module.fail_json(msg=p.stderr, **result)
        else:
            module.fail_json(msg=p.stderr, **result)
        

def run_module():
    encode_status = False
    decode_status = False
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        postgres_user_password=dict(type='str', required=True),
    )

    result = dict(
        changed=False,
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        module.exit_json(**result)

    postgres_user_password = module.params['postgres_user_password']
    
    command1 = "sudo -u postgres psql -c \"ALTER USER postgres PASSWORD '{}';\"".format(postgres_user_password)
    
    execute_command(command1, module, result, True)
    
    str_line = 'localhost:*:*:postgres:' + postgres_user_password
    home = expanduser("~")
    
    pgpass_file_path = home + '/.pgpass'
    with open (pgpass_file_path, 'w') as f:
        f.write(str_line + "\n")
    
    os.chmod(pgpass_file_path, 0o600)
    
    result['changed'] = True
    result['message'] = 'Database restored' 
    module.exit_json(**result) 

def main():
    run_module()


if __name__ == '__main__':
    main()
