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

def delete_db_info(module, result, webinst, web_server, wsdir):
        
    command = webinst + ' -delete -"%s" -wsdir "%s"' % (web_server, wsdir)

    rc, out, err = module.run_command(command)
    
    result['rc'] = rc
    
    if rc == 0:        
        
        result['status'] = out.strip('\n')
        result['changed'] = True
        module.exit_json(**result)
               
    else:	
    	module.fail_json(msg=out.strip('\n'), **result)


def publish_db_info(module, result, webinst, web_server, wsdir, info_base_cluster, info_base_name, web_server_confpath):
    
    if info_base_cluster == None or info_base_name == None:
        module.fail_json(msg='Не заданы данные подключения к базе данных', **result)
    
    
    directory = '/var/www/"%s"' % (wsdir)
    connection = 'Srvr="%s";Ref="%s";' % (info_base_cluster, info_base_name)
        
    command = webinst + ' -publish -"%s" -wsdir "%s" -dir "%s" -connstr "%s" -confpath "%s"' % (web_server, wsdir, directory, connection, web_server_confpath)

    rc, out, err = module.run_command(command)
    
    result['rc'] = rc
    
    if rc == 0:        
        
        result['status'] = out.strip('\n')
        result['changed'] = True
        module.exit_json(**result)
               
    else:	
    	module.fail_json(msg=out.strip('\n'), **result)

def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        state=dict(type='str', required=True),
        version=dict(type='str', required=False, default='8.3.20.1710'),
        web_server=dict(type='str', required=False, default='apache24'),
        web_server_confpath=dict(type='str', required=False, default='/etc/apache2/apache2.conf'),
        
        wsdir=dict(type='str', required=True),
        info_base_cluster=dict(type='str', required=False, default=None),
        info_base_name=dict(type='str', required=False, default=None)
    )

    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    if module.check_mode:
        module.exit_json(**result)

    state = module.params['state']
    version = module.params['version']
    web_server = module.params['web_server']
    web_server_confpath = module.params['web_server_confpath']
    wsdir = module.params['wsdir']
    info_base_cluster = module.params['info_base_cluster']
    info_base_name = module.params['info_base_name']
    
    
    path = '/opt/1cv8/x86_64/';
    webinst_name = 'webinst'
    wsap22_name = 'wsap22.so'
    wsap24_name = 'wsap24.so'
    
    webinst = path + version + "/" + webinst_name
    wsap22 = path + version + "/" + wsap22_name
    wsap24 = path + version + "/" + wsap24_name
    
    webinst_path_res = os.path.exists(webinst)
    wsap22_path_res = os.path.exists(wsap22)
    wsap24_path_res = os.path.exists(wsap24)   
    
    if webinst_path_res == False or wsap22_path_res == False or wsap24_path_res == False:
        msg =  'Модули расширения веб-сервера (ws) не установлены'
        module.fail_json(msg=msg, **result)
    
    if state == 'publish':
    	publish_db_info(module, result, webinst, web_server, wsdir, info_base_cluster, info_base_name, web_server_confpath)
    elif state == 'delete':
       delete_db_info(module, result, webinst, web_server, wsdir)
    else:
       module.fail_json(msg='Не задан параметр state', **result)
    
    

def main():
    run_module()


if __name__ == '__main__':
    main()
