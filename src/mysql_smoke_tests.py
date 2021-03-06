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
    foundation = os.environ['FOUNDATION']
    mysql_service_name = os.environ['MYSQL_SERVICE_NAME']
    mysql_service_plan = os.environ['MYSQL_SERVICE_PLAN']
    mysql_service_instance = os.environ['MYSQL_SERVICE_INSTANCE']
    mysql_sample_app = os.environ['MYSQL_SAMPLE_APP']
    mysql_sample_app_path = os.path.join(os.getcwd(), "cf-smoke-tests", "sample_apps", mysql_sample_app)
except KeyError as e:
    print(str(e))
    exit(1)


def test_mysql_app():
    results = {}
    results['read'] = False
    results['write'] = False
    try:
        _ , routes = utils.get_app_routes(mysql_sample_app)
        url = "https://{}/user".format(routes[0].strip())

        print("Writing into mysql instance via sample-app endpoint: {}".format(url))
        resp = requests.post(url)
        results['write'] = (resp.status_code == 201)
        print("status: {}, content: {}\n".format(resp.status_code, resp.content))

        print("Reading from mysql instance via sample-app endpoint: {}".format(url))
        resp = requests.get(url)
        results['read'] = (resp.status_code == 200)
        print("status: {}, content: {}\n".format(resp.status_code, resp.content))
    except Exception as e:
        print(str(e))
    return results


def main():
    result = True
    results = {}
    print("Starting MySQL smoke-test...")
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

        results['list_marketplace_service'] = common_tests.list_marketplace_service(mysql_service_name)
        if not results['list_marketplace_service']:
            raise Exception('list_marketplace_service failed')

        results['create_service'] = common_tests.create_service(mysql_service_name, mysql_service_plan, mysql_service_instance)
        if not results['create_service']:
            raise Exception('create_service failed')

        results['show_service_info'] = common_tests.show_service_info(mysql_service_instance)
        if not results['show_service_info']:
            raise Exception('show_service_info failed')

        manifest_path = os.path.join(mysql_sample_app_path, 'manifest.yml')
        params = "{} -f {} -p {} --no-start".format(mysql_sample_app, manifest_path, mysql_sample_app_path)
        results['push_app'] = common_tests.push_app(params)
        if not results['push_app']:
            raise Exception('push_app failed')

        results['bind_service'] = common_tests.bind_service(mysql_sample_app, mysql_service_instance)
        if not results['bind_service']:
            raise Exception('bind_service failed')

        results['start_app'] = common_tests.start_app(mysql_sample_app)
        if not results['start_app']:
            results['get_app_logs'] = common_tests.get_app_logs(mysql_sample_app)
            raise Exception('start_app failed')

        test_app_result = test_mysql_app()
        results['test_app_write'] = test_app_result['write']
        if not results['test_app_write']:
            raise Exception('test_app_write failed')
        results['test_app_read'] = test_app_result['read']
        if not results['test_app_read']:
            raise Exception('test_app_read failed')

    except Exception as e:
        print(str(e))
        result = False
    finally:
        try:
            results['unbind_service'] = common_tests.unbind_service(mysql_sample_app, mysql_service_instance)
            if not results['unbind_service']:
                print('unbind_service failed')
        except Exception as e:
            print(str(e))
            result = False

        try:
            results['delete_app'] = common_tests.delete_app(mysql_sample_app)
            if not results['delete_app']:
                print('delete_app failed')
        except Exception as e:
            print(str(e))
            result = False

        try:
            results['delete_service'] = common_tests.delete_service(mysql_service_instance)
            if not results['delete_service']:
                print('delete_service failed')
        except Exception as e:
            print(str(e))
            result = False

    if result and not all(value == True for value in results.values()):
        result = False
    print("Finished MySQL smoke-test...")
    print(json.dumps(results, indent=1))
    print("Overall result: {}".format("Passed" if result else "Failed"))
    end = time.time()
    minutes_taken = (end-start)/60
    print("Total time taken: {} minutes".format(minutes_taken))
    results['overall_result'] = result
    results['minutes_taken'] = minutes_taken
    report_results.send_metric_to_influxdb('mysql', results)
    return not result


if __name__ == "__main__":
    sys.exit(main())
