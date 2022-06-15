#!/usr/bin/python3.8

from __future__ import (absolute_import, division, print_function)
import base64

__metaclass__ = type

DOCUMENTATION = r'''
---
module: 1C infobase
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
import subprocess

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


def create_infobase(module, result, full_path):
    cluster_id = get_parameter(module, 'cluster_id', True)
    infobase_name = get_parameter(module, 'infobase_name', True)
    dbms = get_parameter(module, 'dbms', True)
    db_server = get_parameter(module, 'db_server', True)
    db_name = get_parameter(module, 'db_name', True)
    db_user= get_parameter(module, 'db_user', True)
    db_pwd= get_parameter(module, 'db_pwd', True)
    locale= get_parameter(module, 'locale', True)
    license_distr_bool = get_parameter(module, 'license_distr', True)
    cluster_user = get_parameter(module, 'cluster_user', True)
    cluster_pwd = get_parameter(module, 'cluster_pwd', True)
    descr= get_parameter(module, 'descr', False)
    
    license_distr = None
    if license_distr_bool == True:
        license_distr = 'allow'
    else:
        license_distr = 'deny'
    
    command = full_path + '/rac infobase --cluster="%s" create --create-database --name="%s" --dbms="%s" --db-server="%s" --db-name="%s" --locale="%s" --db-user="%s" --db-pwd="%s" --license-distribution="%s" --cluster-user="%s" --cluster-pwd="%s" --descr=%s' % (cluster_id, infobase_name, dbms, db_server, db_name, locale, db_user, db_pwd, license_distr, cluster_user, cluster_pwd, descr)
    
    rc, out, err = module.run_command(command)
    
    result['rc'] = rc
    
    if rc == 0:
        result['changed'] = True
        result['message'] =  "Создана новая информационная база"
        result['infobase_id'] = (out.split(":")[1]).strip()
        module.exit_json(**result)
    else:
        module.fail_json(msg=(" ".join(err.split())), **result)


def get_infobase_dict(module, result, full_path):
    cluster_id = get_parameter(module, 'cluster_id', True)
    cluster_user=get_parameter(module, 'cluster_user', True)
    cluster_pwd=get_parameter(module, 'cluster_pwd', True)
    
    command = full_path + '/rac infobase --cluster="%s" summary list --cluster-user=%s --cluster-pwd=%s'  % (cluster_id, cluster_user, cluster_pwd)

    rc, out, err = module.run_command(command)
    
    result['rc'] = rc
    
    if rc == 0:
        out = out.strip()
        infobase_list = out.split("\n\n")
        infobase_list = [x.split('\n') for x in infobase_list]
        infobase_list = [[y.split(":") for y in x] for x in infobase_list]
        infobase_list = [[[z.strip(' ') for z in y] for y in x] for x in infobase_list]

        infobase_dict = dict()

        for infobase in infobase_list:
            ib_dict = dict()
            for i in infobase:
                ib_dict[i[0]] = i[1]

            infobase_dict[ib_dict['infobase']] = ib_dict
        
        return infobase_dict
    else:
        module.fail_json(msg=(" ".join(err.split())), **result)


def get_infobase_list(module, result, full_path):
    infobase_dict = get_infobase_dict(module, result, full_path)
    result['message'] = infobase_dict
    module.exit_json(**result)
    

def find_hasp_usb(module):
    command = 'lsusb'
    rc, out, err = module.run_command(command)
    if rc == 0:
        i = out.find('0529:0001 Aladdin Knowledge Systems HASP copy protection dongle')
        if i == -1:
            return False
        return True
    else:
        module.fail_json(msg=(" ".join(err.split())))


def find_xvfb(module):
    command = 'dpkg -s xvfb'
    rc, out, err = module.run_command(command)
    
    if not rc == 0:
        module.fail_json(msg=(' '.join(err.split()))) 
    if out.find('Provides: xserver') == -1:
        return False
    else:
        return True


def check_path(module, path):
    return os.path.exists(path.rsplit('/', 1)[0])
           

def dump_infobase(module, result, full_path):
    licence_type= get_parameter(module, 'licence_type', True)
    dump_path= get_parameter(module, 'dump_path', True)
    cluster_url= get_parameter(module, 'cluster_url', True)
    infobase_name= get_parameter(module, 'infobase_name', True)
    
    cluster_id = get_parameter(module, 'cluster_id', True)
    cluster_user=get_parameter(module, 'cluster_user', True)
    cluster_pwd=get_parameter(module, 'cluster_pwd', True)
    
    command = 'xvfb-run -a ' + full_path + '/1cv8 DESIGNER /S "%s\\%s" /DumpIB "%s"' % (cluster_url, infobase_name, dump_path)
    
    user_name=get_parameter(module, 'user_name', False)
    user_psw=get_parameter(module, 'user_psw', False)
    
    if not user_name == None:
        command = command + " /N " + user_name
        
    if not user_psw == None:
        command = command + " /P " + user_psw
    
    f = False
    
    d = get_infobase_dict(module, result, full_path)
    for key in d:
        i = d[key]['name']
        if i == infobase_name:
            f = True
    
    if not f:
        module.fail_json(msg=('Информационая база %s не существует' % (infobase_name)))
        
    
    if not licence_type == 'usb':
        module.fail_json(msg='Не поддерживается лицензия')
    
    if not find_hasp_usb(module):
        module.fail_json(msg='USB HASP не найден')
    
    if not find_xvfb(module):
        module.fail_json(msg='xvfb не установлен')
        
    if not check_path(module, dump_path):
        module.fail_json(msg='Dump_path не верен')
    
    rc, out, err = module.run_command(command)
    result['rc'] = rc
    
    if rc == 0:
        result['changed'] = True
        result['message'] =  'Выгрузка сделана'
        module.exit_json(**result)
    else:
        result['out'] = out
        module.fail_json(msg=(" ".join(err.split())), **result)


def restore_infobase(module, result, full_path):
    licence_type= get_parameter(module, 'licence_type', True)
    dump_path= get_parameter(module, 'dump_path', True)
    cluster_url= get_parameter(module, 'cluster_url', True)
    infobase_name= get_parameter(module, 'infobase_name', True)
    
    cluster_id = get_parameter(module, 'cluster_id', True)
    cluster_user=get_parameter(module, 'cluster_user', True)
    cluster_pwd=get_parameter(module, 'cluster_pwd', True)
    
    jobs_count=get_parameter(module, 'jobs_count', True)
    
    command = 'xvfb-run -a ' + full_path + '/1cv8 DESIGNER /S "%s\\%s" /RestoreIB "%s" -JobsCount %s' % (cluster_url, infobase_name, dump_path, jobs_count)
    
    user_name=get_parameter(module, 'user_name', False)
    user_psw=get_parameter(module, 'user_psw', False)
    
    if not user_name == None:
        command = command + " /N " + user_name
        
    if not user_psw == None:
        command = command + " /P " + user_psw
    
    f = False
    
    d = get_infobase_dict(module, result, full_path)
    for key in d:
        i = d[key]['name']
        if i == infobase_name:
            f = True
    
    if not f:
        module.fail_json(msg=('Информационая база %s не существует' % (infobase_name)))
        
    
    if not licence_type == 'usb':
        module.fail_json(msg='Не поддерживается лицензия')
    
    if not find_hasp_usb(module):
        module.fail_json(msg='USB HASP не найден')
    
    if not find_xvfb(module):
        module.fail_json(msg='xvfb не установлен')
        
    if not check_path(module, dump_path):
        module.fail_json(msg='Dump_path не верен')
    
    rc, out, err = module.run_command(command)
    result['rc'] = rc
    
    if rc == 0:
        result['changed'] = True
        result['message'] =  'Загрузка сделана'
        module.exit_json(**result)
    else:
        result['out'] = out
        module.fail_json(msg=(" ".join(err.split())), **result)


def restore_integrity_infobase(module, result, full_path):
    licence_type= get_parameter(module, 'licence_type', True)
    cluster_url= get_parameter(module, 'cluster_url', True)
    infobase_name= get_parameter(module, 'infobase_name', True)
    
    cluster_id = get_parameter(module, 'cluster_id', True)
    cluster_user=get_parameter(module, 'cluster_user', True)
    cluster_pwd=get_parameter(module, 'cluster_pwd', True)
    
    
    command = 'xvfb-run -a ' + full_path + '/1cv8 DESIGNER /S "%s\\%s" /IBRestoreIntegrity' % (cluster_url, infobase_name)
    
    user_name=get_parameter(module, 'user_name', False)
    user_psw=get_parameter(module, 'user_psw', False)
    
    if not user_name == None:
        command = command + " /N " + user_name
        
    if not user_psw == None:
        command = command + " /P " + user_psw
    
    f = False
    
    d = get_infobase_dict(module, result, full_path)
    for key in d:
        i = d[key]['name']
        if i == infobase_name:
            f = True
    
    if not f:
        module.fail_json(msg=('Информационая база %s не существует' % (infobase_name)))
        
    
    if not licence_type == 'usb':
        module.fail_json(msg='Не поддерживается лицензия')
    
    if not find_hasp_usb(module):
        module.fail_json(msg='USB HASP не найден')
    
    if not find_xvfb(module):
        module.fail_json(msg='xvfb не установлен')
        
    if not check_path(module, dump_path):
        module.fail_json(msg='Dump_path не верен')
    
    rc, out, err = module.run_command(command)
    result['rc'] = rc
    
    if rc == 0:
        result['changed'] = True
        result['message'] =  'Востоновлена'
        module.exit_json(**result)
    else:
        result['out'] = out
        module.fail_json(msg=(" ".join(err.split())), **result)


def dump_cfg(module, result, full_path):
    licence_type= get_parameter(module, 'licence_type', True)
    dump_cfg_path= get_parameter(module, 'dump_cfg_path', True)
    cluster_url= get_parameter(module, 'cluster_url', True)
    infobase_name= get_parameter(module, 'infobase_name', True)
    
    cluster_id = get_parameter(module, 'cluster_id', True)
    cluster_user=get_parameter(module, 'cluster_user', True)
    cluster_pwd=get_parameter(module, 'cluster_pwd', True)
    
    command = 'xvfb-run -a ' + full_path + '/1cv8 DESIGNER /S "%s\\%s" /DumpCfg "%s"' % (cluster_url, infobase_name, dump_cfg_path)
    
    user_name=get_parameter(module, 'user_name', False)
    user_psw=get_parameter(module, 'user_psw', False)
    
    if not user_name == None:
        command = command + " /N " + user_name
        
    if not user_psw == None:
        command = command + " /P " + user_psw
    
    f = False
    
    d = get_infobase_dict(module, result, full_path)
    for key in d:
        i = d[key]['name']
        if i == infobase_name:
            f = True
    
    if not f:
        module.fail_json(msg=('Информационая база %s не существует' % (infobase_name)))
        
    
    if not licence_type == 'usb':
        module.fail_json(msg='Не поддерживается лицензия')
    
    if not find_hasp_usb(module):
        module.fail_json(msg='USB HASP не найден')
    
    if not find_xvfb(module):
        module.fail_json(msg='xvfb не установлен')
        
    if not check_path(module, dump_path):
        module.fail_json(msg='Dump_path не верен')
    
    rc, out, err = module.run_command(command)
    result['rc'] = rc
    
    if rc == 0:
        result['changed'] = True
        result['message'] =  'Выгрузка конфигурации сделана'
        module.exit_json(**result)
    else:
        result['out'] = out
        module.fail_json(msg=(" ".join(err.split())), **result)
    
def restore_cfg(module, result, full_path):
    licence_type= get_parameter(module, 'licence_type', True)
    dump_cfg_path= get_parameter(module, 'dump_cfg_path', True)
    cluster_url= get_parameter(module, 'cluster_url', True)
    infobase_name= get_parameter(module, 'infobase_name', True)
    
    cluster_id = get_parameter(module, 'cluster_id', True)
    cluster_user=get_parameter(module, 'cluster_user', True)
    cluster_pwd=get_parameter(module, 'cluster_pwd', True)
    
    
    command = 'xvfb-run -a ' + full_path + '/1cv8 DESIGNER /S "%s\\%s" /LoadCfg "%s"' % (cluster_url, infobase_name, dump_cfg_path)
    
    user_name=get_parameter(module, 'user_name', False)
    user_psw=get_parameter(module, 'user_psw', False)
    
    if not user_name == None:
        command = command + " /N " + user_name
        
    if not user_psw == None:
        command = command + " /P " + user_psw
    
    f = False
    
    d = get_infobase_dict(module, result, full_path)
    for key in d:
        i = d[key]['name']
        if i == infobase_name:
            f = True
    
    if not f:
        module.fail_json(msg=('Информационая база %s не существует' % (infobase_name)))
        
    
    if not licence_type == 'usb':
        module.fail_json(msg='Не поддерживается лицензия')
    
    if not find_hasp_usb(module):
        module.fail_json(msg='USB HASP не найден')
    
    if not find_xvfb(module):
        module.fail_json(msg='xvfb не установлен')
        
    if not check_path(module, dump_path):
        module.fail_json(msg='Dump_path не верен')
    
    rc, out, err = module.run_command(command)
    result['rc'] = rc
    
    if rc == 0:
        result['changed'] = True
        result['message'] =  'Загрузка сделана'
        module.exit_json(**result)
    else:
        result['out'] = out
        module.fail_json(msg=(" ".join(err.split())), **result)


def check_and_repair_infobase(module, result, full_path):
    
    licence_type= get_parameter(module, 'licence_type', True)
    cluster_url= get_parameter(module, 'cluster_url', True)
    infobase_name= get_parameter(module, 'infobase_name', True)
    
    cluster_id = get_parameter(module, 'cluster_id', True)
    cluster_user=get_parameter(module, 'cluster_user', True)
    cluster_pwd=get_parameter(module, 'cluster_pwd', True)
    
    check_and_repair_states = module.params['check_and_repair_states']
    
    command = 'xvfb-run -a ' + full_path + '/1cv8 DESIGNER /S "%s\\%s" /IBCheckAndRepair ' % (cluster_url, infobase_name)
    
    for i in check_and_repair_states:
        command = command + " -" + i
    
    user_name=get_parameter(module, 'user_name', False)
    user_psw=get_parameter(module, 'user_psw', False)
    
    if not user_name == None:
        command = command + " /N " + user_name
        
    if not user_psw == None:
        command = command + " /P " + user_psw
    
    f = False
    
    d = get_infobase_dict(module, result, full_path)
    for key in d:
        i = d[key]['name']
        if i == infobase_name:
            f = True
    
    if not f:
        module.fail_json(msg=('Информационая база %s не существует' % (infobase_name)))
        
    
    if not licence_type == 'usb':
        module.fail_json(msg='Не поддерживается лицензия')
    
    if not find_hasp_usb(module):
        module.fail_json(msg='USB HASP не найден')
    
    if not find_xvfb(module):
        module.fail_json(msg='xvfb не установлен')
    
    result['c'] = command    
    rc, out, err = module.run_command(command)
    result['rc'] = rc
    
    if rc == 0:
        result['changed'] = True
        result['message'] =  'Тестирование и востановление завершено'
        module.exit_json(**result)
    else:
        result['out'] = out
        module.fail_json(msg=(" ".join(err.split())), **result)


def add_user(module, result, full_path):
    
    licence_type= get_parameter(module, 'licence_type', True)
    cluster_url= get_parameter(module, 'cluster_url', True)
    infobase_name= get_parameter(module, 'infobase_name', True)
    
    cluster_id = get_parameter(module, 'cluster_id', True)
    cluster_user=get_parameter(module, 'cluster_user', True)
    cluster_pwd=get_parameter(module, 'cluster_pwd', True)
    
    epf_file_path=get_parameter(module, 'epf_file_path', True)
    
    command = 'xvfb-run -a ' + full_path + '/1cv8 ENTERPRISE /S "%s\\%s" /Execute "%s"' % (cluster_url, infobase_name, epf_file_path)
    
    user_name=get_parameter(module, 'user_name', True)
    user_psw=get_parameter(module, 'user_psw', True)
    
    if not user_name == None:
        command = command + " /N " + user_name
        
    if not user_psw == None:
        command = command + " /P " + user_psw
    
    new_user_name=get_parameter(module, 'new_user_name', True)
    new_user_full_name=get_parameter(module, 'new_user_full_name', True)
    new_user_auth_standart=get_parameter(module, 'new_user_auth_standart', True)
    new_user_psw=get_parameter(module, 'new_user_psw', True)
    new_user_role=get_parameter(module, 'new_user_role', True)
    new_user_show_in_list=get_parameter(module, 'new_user_show_in_list', True)
    new_user_language=get_parameter(module, 'new_user_language', True)
    
    new_user_auth_standart_str = 'Нет'
    
    if new_user_auth_standart == True:
         new_user_auth_standart_str = 'Да'
    
    new_user_show_in_list_str = 'Нет'
    
    if new_user_show_in_list == True:
         new_user_show_in_list_str = 'Да'
    
    c = new_user_name + "," + new_user_full_name + "," + new_user_auth_standart_str + "," + new_user_psw + "," + new_user_role + "," + new_user_show_in_list_str + "," + new_user_language
    
    command = command + ' /C "' + c + '"' 
    
    f = False
    
    d = get_infobase_dict(module, result, full_path)
    for key in d:
        i = d[key]['name']
        if i == infobase_name:
            f = True
    
    if not f:
        module.fail_json(msg=('Информационая база %s не существует' % (infobase_name)))
        
    
    if not licence_type == 'usb':
        module.fail_json(msg='Не поддерживается лицензия')
    
    if not find_hasp_usb(module):
        module.fail_json(msg='USB HASP не найден')
    
    if not find_xvfb(module):
        module.fail_json(msg='xvfb не установлен')
    
    file_path_is_exist = os.path.exists(epf_file_path)
    if file_path_is_exist == False:
        msg = "Путь " + epf_file_path + " недоступен или неверен"
        module.fail_json(msg=msg, **result)
        
    rc, out, err = module.run_command(command)
    result['rc'] = rc
    
    
    if rc == 0:
        result['changed'] = True
        result['message'] =  'Пользователь ' + new_user_name + " создан"
        module.exit_json(**result)
    else:
        result['out'] = out
        module.fail_json(msg=(" ".join(err.split())), **result)
    
def get_db_action_command(db_action, module):
    if db_action is None:
        return ''
    elif db_action == 'drop':
        return '--drop-database'
    elif db_action == 'clear':
        return '--clear-database'
    else:
        module.fail_json(msg='Неверный парамметр db_action, доступно: drop, clear')


def delete_infobase(module, result, full_path):
    cluster_id = get_parameter(module, 'cluster_id', True)
    infobase_id = get_parameter(module, 'infobase_id', True)
    cluster_user=get_parameter(module, 'cluster_user', True)
    cluster_pwd=get_parameter(module, 'cluster_pwd', True)
    db_action=get_parameter(module, 'db_action', False)
    db_acion_command=get_db_action_command(db_action, module)
    
    command = full_path + '/rac infobase --cluster="%s" drop --infobase="%s" %s --cluster-user="%s" --cluster-pwd="%s"' % (cluster_id, infobase_id, db_acion_command, cluster_user, cluster_pwd)
    
    rc, out, err = module.run_command(command)
    
    result['rc'] = rc
    result['infobase_id'] = infobase_id
    
    if rc == 0:
        result['changed'] = True
        result['message'] =  "Информационная база удалена"
        module.exit_json(**result)
    else:
        module.fail_json(msg=(" ".join(err.split())), **result)
  
def get_sub_command(command, parameter):
    if parameter is None:
        return ''
    else:
        return ' ' + command + '="' + parameter + '"'


def update_infobase(module, result, full_path):
    cluster_id = get_parameter(module, 'cluster_id', True)
    infobase_id = get_parameter(module, 'infobase_id', True)
    infobase_user=get_parameter(module, 'infobase_user', False)
    infobase_pwd=get_parameter(module, 'infobase_pwd', False)
    dbms = get_parameter(module, 'dbms', False)
    db_server = get_parameter(module, 'db_server', False)
    db_name = get_parameter(module, 'db_name', False)
    db_user= get_parameter(module, 'db_user', False)
    db_pwd= get_parameter(module, 'db_pwd', False)
    descr= get_parameter(module, 'descr', False)
    denied_from = get_parameter(module, 'denied_from', False)
    denied_message= get_parameter(module, 'denied_message', False)
    denied_parameter= get_parameter(module, 'denied_parameter', False)
    denied_to= get_parameter(module, 'denied_to', False)
    permission_code= get_parameter(module, 'permission_code', False)
    sessions_deny= get_parameter(module, 'sessions_deny', False)
    scheduled_jobs_deny= get_parameter(module, 'scheduled_jobs_deny', False)
    external_session_manager_connection_string= get_parameter(module, 'external_session_manager_connection_string', False)
    external_session_manager_required= get_parameter(module, 'external_session_manager_required', False)
    reserver_working_processes= get_parameter(module, 'reserver_working_processes', False)
    security_profile_name= get_parameter(module, 'security_profile_name', False)
    safe_mode_security_profile_name= get_parameter(module, 'safe_mode_security_profile_name', False)
    
    cluster_user=get_parameter(module, 'cluster_user', False)
    cluster_pwd=get_parameter(module, 'cluster_pwd', False)
    
    license_distr_bool = get_parameter(module, 'license_distr', False)
    license_distr = None
    if license_distr_bool == True:
        license_distr = 'allow'
    else:
        license_distr = 'deny'
        
    command = full_path + '/rac infobase --cluster="%s" update --infobase="%s"' % (cluster_id, infobase_id)
    command = command + get_sub_command('--infobase-user', infobase_user)
    command = command + get_sub_command('--infobase-pwd', infobase_pwd)
    command = command + get_sub_command('--db_server', db_server)
    command = command + get_sub_command('--dbms', dbms)
    command = command + get_sub_command('--db-name', db_name)
    command = command + get_sub_command('--db-user', db_user)
    command = command + get_sub_command('--db-pwd', db_pwd)
    command = command + get_sub_command('--descr', descr)
    command = command + get_sub_command('--denied-from', denied_from)
    command = command + get_sub_command('--denied-message', denied_message)
    command = command + get_sub_command('--denied-parameter', denied_parameter)
    command = command + get_sub_command('--denied-to', denied_to)
    command = command + get_sub_command('--permission-code', permission_code)
    command = command + get_sub_command('--sessions-deny', sessions_deny)
    command = command + get_sub_command('--scheduled-jobs-deny', scheduled_jobs_deny)
    command = command + get_sub_command('--license-distribution', license_distr)
    command = command + get_sub_command('--external-session-manager-connection-string', external_session_manager_connection_string)
    command = command + get_sub_command('--external-session-manager-required', external_session_manager_required)
    command = command + get_sub_command('--reserver-working-processes', reserver_working_processes)
    command = command + get_sub_command('--security-profile-name', security_profile_name)
    command = command + get_sub_command('--safe-mode-security-profile-name', safe_mode_security_profile_name)
    
    command = command + get_sub_command('--cluster-user', cluster_user)
    command = command + get_sub_command('--cluster-pwd', cluster_pwd)
    
    rc, out, err = module.run_command(command)
    
    result['rc'] = rc
    result['infobase_id'] = infobase_id
    
    if rc == 0:
        result['changed'] = True
        result['message'] =  "Информационная база изменена"
        module.exit_json(**result)
    else:
        module.fail_json(msg=(" ".join(err.split())), **result)
    
  
    
def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        version=dict(type='str', required=False, default='8.3.20.1710'),
        c1_path=dict(type='str', required=False, default=None),
        state=dict(type='str', required=True, default=None),
        
        user_name=dict(type='str', required=False, default=None),
        user_psw=dict(type='str', required=False, default=None),
        
        cluster_id=dict(type='str', required=False, default=None),
        infobase_name=dict(type='str', required=False, default=None),
        dbms=dict(type='str', required=False, default='PostgreSQL'),
        db_server=dict(type='str', required=False, default=None),
        db_name=dict(type='str', required=False, default=None),
        locale=dict(type='str', required=False, default='ru'),
        db_user=dict(type='str', required=False, default=None),
        db_pwd=dict(type='str', required=False, default=None),
        license_distr=dict(type='bool', required=False, default=False),
        cluster_user=dict(type='str', required=False, default=None),
        cluster_pwd=dict(type='str', required=False, default=None),
        descr=dict(type='str', required=False, default=""),
        
        infobase_id=dict(type='str', required=False, default=None),
        
        db_action=dict(type='str', required=False, default=None),
        
        infobase_user=dict(type='str', required=False, default=None),
        infobase_pwd=dict(type='str', required=False, default=None),
        denied_from=dict(type='str', required=False, default=None),
        denied_message=dict(type='str', required=False, default=None),
        denied_parameter=dict(type='str', required=False, default=None),
        denied_to=dict(type='str', required=False, default=None),
        permission_code=dict(type='str', required=False, default=None),
        sessions_deny=dict(type='str', required=False, default=None),
        scheduled_jobs_deny=dict(type='str', required=False, default=None),
        external_session_manager_connection_string=dict(type='bool', required=False, default=None),
        external_session_manager_required=dict(type='str', required=False, default=None),
        reserver_working_processes=dict(type='str', required=False, default=None),
        security_profile_name=dict(type='str', required=False, default=None),
        safe_mode_security_profile_name=dict(type='str', required=False, default=None),
        
        licence_type=dict(type='str', required=False, default=None),
        dump_path=dict(type='str', required=False, default=None),
        cluster_url=dict(type='str', required=False, default='localhost'),
        
        jobs_count=dict(type='str', required=False, default='0'),
        
        dump_cfg_path=dict(type='str', required=False, default=None),
        
        check_and_repair_states=dict(type='list', elements='str', required=False),
        
        epf_file_path=dict(type='str', required=False, default=None),
        new_user_name=dict(type='str', required=False, default=None),
        new_user_full_name=dict(type='str', required=False, default=None),
        new_user_auth_standart=dict(type='bool', required=False, default=False),
        new_user_psw=dict(type='str', required=False, default=None),
        new_user_role=dict(type='str', required=False, default=None),
        new_user_show_in_list=dict(type='bool', required=False, default=False),
        new_user_language=dict(type='str', required=False, default='Русский'),
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
    elif state == 'create':
        create_infobase(module, result, full_c1_path)
    elif state == 'drop':
        delete_infobase(module, result, full_c1_path)
    elif state == 'list':
        get_infobase_list(module, result, full_c1_path)
    elif state == 'update':
        update_infobase(module, result, full_c1_path)
    elif state == 'dump':
        dump_infobase(module, result, full_c1_path)
    elif state == 'restore_integrity':
        restore_integrity_infobase(module, result, full_c1_path)
    elif state == 'restore':
        restore_infobase(module, result, full_c1_path)
    elif state == 'dump_cfg':
        dump_cfg(module, result, full_c1_path)
    elif state == 'restore_cfg':
        restore_cfg(module, result, full_c1_path)
    elif state == 'check_and_repair':
        check_and_repair_infobase(module, result, full_c1_path)
    elif state == 'add_user':
        add_user(module, result, full_c1_path)
    else:
        module.fail_json(msg='Некорректный параметр state', **result)
    
    
    
    
    


def main():
    run_module()


if __name__ == '__main__':
    main()
