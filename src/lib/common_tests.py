'''
==================================================================================
Copyright 2020 T-Mobile USA, Inc.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
See the LICENSE file for additional language around the disclaimer of warranties.
Trademark Disclaimer: Neither the name of “T-Mobile, USA” nor the names of
its contributors may be used to endorse or promote products derived from this
software without specific prior written permission.
==================================================================================
'''
#!/usr/bin/env python
import json
import os
import time

import utils

try:
    foundation = os.environ['FOUNDATION']
    foundation_api_domain = os.environ['FOUNDATION_API_DOMAIN']
    foundation_apps_domain = os.environ['FOUNDATION_APPS_DOMAIN']
    smoke_test_user = os.environ['SMOKE_USER']
    smoke_test_pass = os.environ['SMOKE_PASSWORD']
    smoke_test_org = os.environ['SMOKE_ORG']
    smoke_test_space = os.environ['SMOKE_SPACE']
    pivnet_api_token = os.environ["PIVNET_API_TOKEN"]
except KeyError as e:
    print(str(e))
    exit(1)


def set_api():
    cmd = "cf api {} --skip-ssl-validation".format(foundation_api_domain)
    return utils.run_cmd(cmd)


def authenticate():
    cmd = "cf auth {}".format(smoke_test_user)
    print('>>> {} [Redacted Password]'.format(cmd))
    return utils.run_cmd("{} {}".format(cmd, smoke_test_pass), False)


def login(username, password, org, space):
    cmd = "cf login -a {} -o {} -s {} -u {} --skip-ssl-validation".format(foundation_api_domain, org, space, username)
    print('>>> {} -p [Redacted Password]'.format(cmd))
    return utils.run_cmd("{} -p {}".format(cmd, password), False)


def set_target():
    cmd = "cf target -o {} -s {}".format(smoke_test_org, smoke_test_space)
    return utils.run_cmd(cmd)


def list_marketplace_service(service_name):
    cmd = "cf marketplace -s {}".format(service_name)
    return utils.run_cmd(cmd)


def create_service(service_name, service_plan, service_instance_name, params=None):
    print_cmd = None
    if params:
        cmd = "cf create-service {} {} {} -c '{}'".format(service_name, service_plan, service_instance_name, json.dumps(params))
        if service_name == 'p-config-server':
            params['git']['privateKey'] = "[Redacted]"
        print_cmd = "cf create-service {} {} {} -c '{}'".format(service_name, service_plan, service_instance_name, json.dumps(params))
    else:
        cmd = "cf create-service {} {} {}".format(service_name, service_plan, service_instance_name)
        print_cmd = cmd

    print('>>> {}'.format(print_cmd))
    if utils.check_for_service_existence(service_instance_name):
        print('Service creation failed as a service-instance with the same name already exists. Attempting to clean-up before exiting.')
        return False

    if utils.run_cmd(cmd, False, True, False):
        utils.wait_for_service_creation(service_instance_name)
        return True
    else:
        return False


def show_service_info(service_instance_name):
    cmd = "cf service {}".format(service_instance_name)
    return utils.run_cmd(cmd)


def show_service_guid(service_instance_name):
    cmd = "cf service {} --guid".format(service_instance_name)
    status, out = utils.run_cmd(cmd, True, True, True)
    if not status:
        return False, None
    service_guid = out.splitlines()[-1]
    return True, service_guid


def delete_service(service_instance_name):
    cmd = "cf delete-service -f {}".format(service_instance_name)
    print('>>> {}'.format(cmd))
    if not utils.check_for_service_existence(service_instance_name):
        print('Service-instance with this name does not exist. Bailing out.')
        return True
    status, out = utils.run_cmd(cmd, False, True, True)
    if status:
        utils.wait_for_service_deletion(service_instance_name)
        return True
    else:
        if "status code: 409" in out:
            _, service_guid = show_service_guid(service_instance_name)
            print("Storing the service instance guid: {} for cleanup".format(service_guid))
            svc_info = {
                "foundation": foundation,
                "smoke_test_org": smoke_test_org,
                "smoke_test_space": smoke_test_space,
                "service_instance_name": service_instance_name,
                "service_guid": service_guid
            }
            utils.store_dangling_service_info(svc_info)
        return False


def create_service_key(service_instance_name, service_key_name):
    cmd = "cf create-service-key {} {}".format(service_instance_name, service_key_name)
    return utils.run_cmd(cmd)


def show_service_key_info(service_instance_name, service_key_name):
    cmd = "cf service-key {} {}".format(service_instance_name, service_key_name)
    status, out = utils.run_cmd(cmd, True, False, True)
    if not status:
        return False, None
    output_lines = out.splitlines()
    for line in output_lines:
        if 'password' in line:
            temp = line.split(':')
            line = "{}: [Redacted Password],".format(temp[0])
        print(line)
    service_key = json.loads(" ".join(output_lines[2:]))
    return True, service_key


def delete_service_key(service_instance_name, service_key_name):
    if not utils.check_for_service_key_existence(service_instance_name, service_key_name):
        return True
    cmd = "cf delete-service-key -f {} {}".format(service_instance_name, service_key_name)
    return utils.run_cmd(cmd)


def push_app(params):
    cmd = "cf push {}".format(params)
    return utils.run_cmd(cmd)


def show_app_info(app_name):
    cmd = "cf app {}".format(app_name)
    return utils.run_cmd(cmd)


def show_app_guid(app_name):
    cmd = "cf app {} --guid".format(app_name)
    status, out = utils.run_cmd(cmd, True, True, True)
    if not status:
        return False, None
    app_guid = out.splitlines()[-1]
    return True, app_guid


def delete_app(app_name):
    if not utils.check_for_app_existence(app_name):
        return True
    cmd = "cf delete -f -r {}".format(app_name)
    return utils.run_cmd(cmd)


def start_app(app_name):
    cmd = "cf start {}".format(app_name)
    return utils.run_cmd(cmd)


def stop_app(app_name):
    cmd = "cf stop {}".format(app_name)
    return utils.run_cmd(cmd)


def bind_service(app_name, service_instance_name):
    cmd = "cf bind-service {} {}".format(app_name, service_instance_name)
    return utils.run_cmd(cmd)


def unbind_service(app_name, service_instance_name):
    if not utils.check_for_app_existence(app_name) or \
       not utils.check_for_service_existence(service_instance_name):
        return True
    cmd = "cf unbind-service {} {}".format(app_name, service_instance_name)
    return utils.run_cmd(cmd)


def set_env(app_name, env_vars):
    results = []
    for var, value in env_vars.items():
        cmd = "cf set-env {} {} {}".format(app_name, var, value)
        results.append(utils.run_cmd(cmd))
    return all(results)


def scale_app(app_name, num_instances):
    cmd = "cf scale {} -i {}".format(app_name, num_instances)
    return utils.run_cmd(cmd)


def get_app_logs(app_name):
    cmd = "cf logs {} --recent".format(app_name)
    return utils.run_cmd(cmd)


def pivnet_login():
    cmd = 'pivnet login --api-token='
    print('>>> {} [Redacted API Token]'.format(cmd))
    return utils.run_cmd('{}\"{}\"'.format(cmd, pivnet_api_token), False)


def pivnet_get_product_id(product_slug, product_version, grep_keyword):
    cmd = "pivnet pfs -p {} -r {} | grep {} | awk {}".format(product_slug, product_version, grep_keyword, "'{print $2}'")
    returncode, out = utils.run_cmd(cmd, True, True, True)
    product_id = out.strip()
    return returncode, product_id


def pivnet_accept_eula(product_slug, product_version):
    cmd = "pivnet accept-eula -p {} -r {}".format(product_slug, product_version)
    return utils.run_cmd(cmd)


def pivnet_download_product_files(product_slug, product_version, product_id):
    cmd = "pivnet dlpf -p {} -r {} -i {} -d {}".format(product_slug, product_version, product_id, os.getcwd())
    return utils.run_cmd(cmd)


def pivnet_logout():
    cmd = "pivnet logout"
    return utils.run_cmd(cmd)