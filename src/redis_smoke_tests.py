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
import sys	
import time	

from  lib import common_tests, utils, report_results	

try:	
   redis_service_name = os.environ['REDIS_SERVICE_NAME']	
   redis_service_shared_plan = os.environ['REDIS_SERVICE_SHARED_VM_PLAN']	
   redis_service_dedicated_plan = os.environ['REDIS_SERVICE_DEDICATED_VM_PLAN']	
   redis_service_instance_shared_vm = os.environ['REDIS_SERVICE_INSTANCE_SHARED_VM']	
   redis_service_key_shared_vm = os.environ['REDIS_SERVICE_KEY_SHARED_VM']	
   redis_service_instance_dedicated_vm = os.environ['REDIS_SERVICE_INSTANCE_DEDICATED_VM']	
   redis_service_key_dedicated_vm = os.environ['REDIS_SERVICE_KEY_DEDICATED_VM']	
   redis_sample_app = os.environ['REDIS_SAMPLE_APP']	
   redis_sample_app_path = os.path.join(os.getcwd(), "cf-smoke-tests", "sample_apps", redis_sample_app)
except KeyError as e:	
    print(str(e))	
    exit(1)	


def test_redis_app():	
    results = {}
    results['read'] = False
    results['write'] = False
    try:
        _ , routes = utils.get_app_routes(redis_sample_app)
        url = "https://{}".format(routes[0].strip())

        print("Writing into redis instance via sample-app endpoint: {}".format(url))
        resp = requests.post("{}/write".format(url), data=json.dumps({"foo":"bar"}))
        results['write'] = (resp.status_code == 201)
        print("status: {}, content: {}\n".format(resp.status_code, resp.content))

        print("Reading from redis instance via sample-app endpoint: {}".format(url))
        resp = requests.get("{}/read/foo".format(url))
        results['read'] = (resp.status_code == 200 and str(json.loads(resp.content)['foo']) == 'bar')
        print("status: {}, content: {}\n".format(resp.status_code, resp.content))
    except Exception as e:
        print(str(e))
    return results


def test_shared_plan():
    shared_vm_results = {}
    result = True

    try:  # leave service instances between uses to minimize window where customers can snatch final shared redis instance
        shared_vm_results['delete_service'] = common_tests.delete_service(redis_service_instance_shared_vm)
        if not shared_vm_results['delete_service']:
            print('(nonfatal) delete_service failed for shared-vm plan')
    except Exception as e:
        print(str(e))

    try:
        shared_vm_results['create_service'] = common_tests.create_service(redis_service_name, redis_service_shared_plan, redis_service_instance_shared_vm)	
        if not shared_vm_results['create_service']:	
            raise Exception('create_service failed for shared-vm plan')	

        shared_vm_results['show_service_info'] = common_tests.show_service_info(redis_service_instance_shared_vm)	
        if not shared_vm_results['show_service_info']:	
            raise Exception('show_service_info failed for shared-vm plan')	

        shared_vm_results['create_service_key'] = common_tests.create_service_key(redis_service_instance_shared_vm, redis_service_key_shared_vm)	
        if not shared_vm_results['create_service_key']:	
            raise Exception('create_service_key failed for shared-vm plan')	

        shared_vm_results['show_service_key_info'], _ = common_tests.show_service_key_info(redis_service_instance_shared_vm, redis_service_key_shared_vm)	
        if not shared_vm_results['show_service_key_info']:	
            raise Exception('show_service_key_info failed for shared-vm plan')	

        manifest_path = os.path.join(redis_sample_app_path, 'manifest.yml')
        params = "{} -f{} -p {} --no-start".format(redis_sample_app, manifest_path, redis_sample_app_path)
        shared_vm_results['push_app'] = common_tests.push_app(params)
        if not shared_vm_results['push_app']:
            raise Exception('push_app failed for shared-vm plan')

        shared_vm_results['bind_service'] = common_tests.bind_service(redis_sample_app, redis_service_instance_shared_vm)	
        if not shared_vm_results['bind_service']:	
            raise Exception('bind_service failed for shared-vm plan')	

        shared_vm_results['start_app'] = common_tests.start_app(redis_sample_app)	
        if not shared_vm_results['start_app']:	
            shared_vm_results['get_app_logs'] = common_tests.get_app_logs(redis_sample_app)	
            raise Exception('start_app failed for shared-vm plan')	

        test_app_result = test_redis_app()	

        shared_vm_results['test_app_write'] = test_app_result['write']	
        if not shared_vm_results['test_app_write']:	
            raise Exception('test_app_write failed for shared-vm plan')

        shared_vm_results['test_app_read'] = test_app_result['read']	
        if not shared_vm_results['test_app_read']:	
            raise Exception('test_app_read failed for shared-vm plan')	
    except Exception as e:	
        print(str(e))
        result = False
    finally:	
        try:	
            shared_vm_results['unbind_service'] = common_tests.unbind_service(redis_sample_app, redis_service_instance_shared_vm)	
            if not shared_vm_results['unbind_service']:	
                print('unbind_service failed for shared-vm plan')	
        except Exception as e:
            print(str(e))
            result = False

        try:
            shared_vm_results['delete_service_key'] = common_tests.delete_service_key(redis_service_instance_shared_vm, redis_service_key_shared_vm)	
            if not shared_vm_results['delete_service_key']:	
                print('delete_service_key failed for shared-vm plan')	
        except Exception as e:
            print(str(e))
            result = False

        try:
            shared_vm_results['delete_app'] = common_tests.delete_app(redis_sample_app)	
            if not shared_vm_results['delete_app']:	
                print('delete_app failed for shared-vm plan')	
        except Exception as e:
            print(str(e))
            result = False

    return shared_vm_results, result	


def test_dedicated_plan():	
    dedicated_vm_results = {}	
    result = True	
    try:	
        dedicated_vm_results['create_service'] = common_tests.create_service(redis_service_name, redis_service_dedicated_plan, redis_service_instance_dedicated_vm)
        if not dedicated_vm_results['create_service']:	
            raise Exception('create_service failed for dedicated-vm plan')	

        dedicated_vm_results['show_service_info'] = common_tests.show_service_info(redis_service_instance_dedicated_vm)	
        if not dedicated_vm_results['show_service_info']:	
            raise Exception('show_service_info failed for dedicated-vm plan')	

        dedicated_vm_results['create_service_key'] = common_tests.create_service_key(redis_service_instance_dedicated_vm, redis_service_key_dedicated_vm)	
        if not dedicated_vm_results['create_service_key']:	
            raise Exception('create_service_key failed for dedicated-vm plan')	

        dedicated_vm_results['show_service_key_info'], _ = common_tests.show_service_key_info(redis_service_instance_dedicated_vm, redis_service_key_dedicated_vm)	
        if not dedicated_vm_results['show_service_key_info']:
            raise Exception('show_service_key_info failed for dedicated-vm plan')

        manifest_path = os.path.join(redis_sample_app_path, 'manifest.yml')
        params = "{} -f {} -p {} --no-start".format(redis_sample_app, manifest_path, redis_sample_app_path)
        dedicated_vm_results['push_app'] = common_tests.push_app(params)	
        if not dedicated_vm_results['push_app']:	
            raise Exception('push_app failed for dedicated-vm plan')	

        dedicated_vm_results['bind_service'] = common_tests.bind_service(redis_sample_app, redis_service_instance_dedicated_vm)	
        if not dedicated_vm_results['bind_service']:	
            raise Exception('bind_service failed for dedicated-vm plan')	

        dedicated_vm_results['start_app'] = common_tests.start_app(redis_sample_app)	
        if not dedicated_vm_results['start_app']:	
            dedicated_vm_results['get_app_logs'] = common_tests.get_app_logs(redis_sample_app)	
            raise Exception('start_app failed for dedicated-vm plan')	

        test_app_result = test_redis_app()

        dedicated_vm_results['test_app_write'] = test_app_result['write']	
        if not dedicated_vm_results['test_app_write']:	
            raise Exception('test_app_write failed for dedicated-vm plan')
	
        dedicated_vm_results['test_app_read'] = test_app_result['read']	
        if not dedicated_vm_results['test_app_read']:	
            raise Exception('test_app_read failed for dedicated-vm plan')	
    except Exception as e:	
        print(str(e))	
        result = False	
    finally:	
        try:	
            dedicated_vm_results['unbind_service'] = common_tests.unbind_service(redis_sample_app, redis_service_instance_dedicated_vm)	
            if not dedicated_vm_results['unbind_service']:	
                print('unbind_service failed for dedicated-vm plan')	
        except Exception as e:
            print(str(e))
            result = False

        try:
            dedicated_vm_results['delete_service_key'] = common_tests.delete_service_key(redis_service_instance_dedicated_vm, redis_service_key_dedicated_vm)	
            if not dedicated_vm_results['delete_service_key']:	
                print('delete_service_key failed for dedicated-vm plan')	
        except Exception as e:
            print(str(e))
            result = False

        try:
            dedicated_vm_results['delete_app'] = common_tests.delete_app(redis_sample_app)	
            if not dedicated_vm_results['delete_app']:	
                print('delete_app failed for dedicated-vm plan')	
        except Exception as e:
            print(str(e))
            result = False

        try:
            dedicated_vm_results['delete_service'] = common_tests.delete_service(redis_service_instance_dedicated_vm)	
            if not dedicated_vm_results['delete_service']:	
                print('delete_service failed for dedicated-vm plan')	
        except Exception as e:	
            print(str(e))	
            result = False	

    return dedicated_vm_results, result	


def main():	
    result = True	
    results = {}	
    print("Starting Redis smoke-test...")	
    start = time.time()	
    try:	
        results['set_api'] = common_tests.set_api()	
        if not results['set_api']:	
            raise Exception('set_api failed')	

        results['authenticate'] = common_tests.authenticate()	
        if not results['authenticate']:	
            raise Exception('authenticate failed')	

        results['set_target'] = common_tests.set_target()	
        if not results['set_target']:	
            raise Exception('set_target failed')	

        results['list_marketplace_service'] = common_tests.list_marketplace_service(redis_service_name)	
        if not results['list_marketplace_service']:	
            raise Exception('list_marketplace_service failed')	

        print("Testing shared-vm plan...")	
        shared_vm_results, result = test_shared_plan()	
        for key, value in shared_vm_results.items():	
            results['shared_vm.{}'.format(key)] = value	

        #print("Testing dedicated-vm plan...")	
        #dedicated_vm_results, result = test_dedicated_plan()	
        #for key, value in dedicated_vm_results.items():	
        #    results['dedicated_vm.{}'.format(key)] = value	
    except Exception as e:	
        print(str(e))	
        result = False	

    if result and not all(value == True for value in results.values()):	
        result = False	
    print("Finished Redis smoke-test...")	
    print(json.dumps(results, indent=1))	
    print("Overall result: {}".format("Passed" if result else "Failed"))	
    end = time.time()	
    minutes_taken = (end-start)/60	
    print("Total time taken: {} minutes".format(minutes_taken))	
    results['overall_result'] = result	
    results['minutes_taken'] = minutes_taken	
    report_results.send_metric_to_influxdb('redis', results)	
    return not result	


if __name__ == "__main__":	
    sys.exit(main())