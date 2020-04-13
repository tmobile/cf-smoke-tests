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
import requests
import subprocess
import time


def run_cmd(cmd, print_cmd=True, print_stdout=True, return_stdout=False):
    if print_cmd:
        print('>>> {}'.format(cmd))
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True, universal_newlines=True)
    out, _ = proc.communicate()
    if print_stdout:
        print(out)
    if return_stdout:
        return proc.returncode == 0, out
    return proc.returncode == 0


def check_for_service_existence(service_instance_name):
    cmd = "cf service {}".format(service_instance_name)
    return run_cmd(cmd, False, False)


def check_for_service_key_existence(service_instance_name, service_key_name):
    cmd = "cf service-key {} {}".format(service_instance_name, service_key_name)
    return run_cmd(cmd, False, False)


def check_for_app_existence(app_name):
    cmd = "cf app {}".format(app_name)
    return run_cmd(cmd, False, False)


def wait_for_service_creation(service_instance_name):
    print("Waiting for service instance '{}' to be created...".format(service_instance_name))
    try:
        while True:
            service_info = get_service_info(service_instance_name)
            if service_info and service_info['total_results'] > 0:
                action = str(service_info['resources'][0]['entity']['last_operation']['type'])
                state = str(service_info['resources'][0]['entity']['last_operation']['state'])
                if action.lower() == 'create' and state.lower() == 'in progress':
                    print("Sevice creation is still in progress...")
                    time.sleep(60)
                    continue
                else:
                    break
            else:
                break
    except Exception as e:
        print(str(e))


def wait_for_service_deletion(service_instance_name):
    print("Waiting for service instance '{}' to be deleted...".format(service_instance_name))
    try:
        while True:
            service_info = get_service_info(service_instance_name)
            if service_info and service_info['total_results'] > 0:
                action = str(service_info['resources'][0]['entity']['last_operation']['type'])
                state = str(service_info['resources'][0]['entity']['last_operation']['state'])
                if action.lower() == 'delete' and state.lower() == 'in progress':
                    print("Sevice deletion is still in progress...")
                    time.sleep(60)
                    continue
                else:
                    break
            else:
                break
    except Exception as e:
        print(str(e))


def get_app_routes(app_name):
    cmd = "cf app {} | grep routes".format(app_name)
    status, out = run_cmd(cmd, False, False, True)
    if not status:
        return False, None
    routes = out.split(':')[1].split(',')
    return True, routes


def get_app_info(app_name):
    cmd = "cf curl /v2/apps?q=name:{}".format(app_name)
    status, out = run_cmd(cmd, False, False, True)
    if not status:
        return False, None
    app_info = json.loads(out)
    return app_info


def get_service_info(service_instance_name):
    cmd = "cf curl /v2/service_instances?q=name:{}".format(service_instance_name)
    status, out = run_cmd(cmd, False, False, True)
    if not status:
        return False, None
    service_info = json.loads(out)
    return service_info
