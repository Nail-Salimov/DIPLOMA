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

def execute_command(command, module, result, req):
    p = subprocess.run(['sudo', '-S'] + command.split(), universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0 and req:
        if p.stdout == '':
            module.fail_json(msg=p.stderr, **result)
        else:
            module.fail_json(msg=p.stdout, **result)
        

def get_parameter(module, parameter, is_req):
    v = module.params[parameter]
    if v == None and is_req == True:
        module.fail_json(msg='Не задан парметр ' + parameter)
    else:
        return v


def find_backupninja(module):
    command = 'dpkg -s backupninja'
    rc, out, err = module.run_command(command)
    
    if not rc == 0:
        module.fail_json(msg=(' '.join(err.split()))) 
    if out.find('Package: backupninja') == -1:
        return False
    else:
        return True



def backupninja(module, result):
    database = get_parameter(module, 'database', True)
    pg_user = get_parameter(module, 'pg_user', True)
    pg_psw = get_parameter(module, 'pg_psw', True)
    backup_path = get_parameter(module, 'backup_path', True)
    period = get_parameter(module, 'period', True)
    backup_format = get_parameter(module, 'backup_format', True)
    compress= get_parameter(module, 'compress', True)
    file_name = get_parameter(module, 'file_name', True)
    
    
    str_line1 = 'when = ' + period
    str_line2 = 'databases = ' + database
    str_line2 = 'backupdir = ' + backup_path
    str_line3 = 'dbusername = ' + pg_user
    str_line4 = 'dbpassword = ' + pg_psw
    str_line5 = 'format = ' + backup_format
    str_line6 = 'compress = ' + compress
    
    if not find_backupninja(module):
        module.fail_json(msg='Backup Ninja не установлен')
    
    backup_file = "/etc/backup.d/" + file_name + ".pgsql"
    with open (backup_file, 'w') as f:
        f.write(str_line1 + "\n")
        f.write(str_line2 + "\n")
        f.write(str_line3 + "\n")
        f.write(str_line4 + "\n")
        f.write(str_line5 + "\n")
        f.write(str_line6 + "\n")
    
    os.chmod(backup_file, 600)
    
    result['changed'] = True
    result['message'] = 'Ninjabackup config file created' 
    module.exit_json(**result) 


def cron(module, result):

    database = get_parameter(module, 'database', True)
    pg_user = get_parameter(module, 'pg_user', True)
    backup_path = get_parameter(module, 'backup_path', True)
    life_days = get_parameter(module, 'life_days', True)
    period = get_parameter(module, 'period', True)
    ip_address = get_parameter(module, 'ip_address', True)
    
    str_line1 = '#!/bin/sh'
    str_line2 = 'DATA=`date +"%Y-%m-%d"`'
    str_line3 = 'database=' + database
    str_line4 = 'pg_dump -h ' + ip_address +' -U ' + pg_user +' -Fc -d $database >  ' + backup_path +'/$DATA-$database.bak'
    str_line5 = '/usr/bin/find ' + backup_path +' -type f -mtime +' + life_days +' -exec rm -rf {} \;'
    
    backup_file = backup_path + "/" +database + "_backup.sh"
    with open (backup_file, 'w') as f:
    	f.write(str_line1 + "\n")
    	f.write(str_line2 + "\n")
    	f.write(str_line3 + "\n")
    	f.write(str_line4 + "\n")
    	f.write(str_line5 + "\n")
    
    os.chmod(backup_file, 0o777)
    
    crontab_text = subprocess.run(['crontab', '-l'], stdout=subprocess.PIPE).stdout.decode('utf-8')
    crontab_text = crontab_text + period + " " + backup_file + "\n"
    backup_cron = backup_path + "/" +database + "_cron"
    with open (backup_cron, 'w') as f:
        f.write(crontab_text)
    
    command1 = "crontab " + backup_cron  
    execute_command(command1, module, result, True)
    
    result['changed'] = True
    result['message'] = 'Cron Backup installed' 
    module.exit_json(**result) 

def run_module():
    encode_status = False
    decode_status = False
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        state  = dict(type='str', required=False, default='cron'),
        database=dict(type='str', required=False, default=None),
        pg_user=dict(type='str', required=False, default=None),
        backup_path=dict(type='str', required=False, default=None),
        life_days = dict(type='str', required=False, default=None),
        period = dict(type='str', required=False, default=None),
        ip_address = dict(type='str', required=False, default='localhost'),
        
        backup_format = dict(type='str', required=False, default='plain'),
        compress= dict(type='str', required=False, default='no'),
        file_name = dict(type='str', required=False),
        pg_psw =  dict(type='str', required=False),
    )
    
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    
    if module.check_mode:
        module.exit_json(**result)
    
    
    state = module.params['state']
    
    result = dict(
        changed=False,
        message=''
    )
    
    if state == 'cron':
        cron(module, result)
    elif state == 'backupninja':
        backupninja(module, result)

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )
    
    
    


def main():
    run_module()


if __name__ == '__main__':
    main()
