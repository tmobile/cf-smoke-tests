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
    pas_sample_app = os.environ['PAS_SAMPLE_APP']
    pas_sample_app_path = os.path.join(os.getcwd(), "cf-smoke-tests", "sample_apps", pas_sample_app)
except KeyError as e:
    print(str(e))
    exit(1)


def test_app_instances_connection(num_instances):
    max_attempts = 10
    app_instance_connection_results = {}
    try:
        for i in range(num_instances):
            app_instance_connection_results[i] = False

        _, appguid = common_tests.show_app_guid(pas_sample_app)
        _ , routes = utils.get_app_routes(pas_sample_app)
        url = "https://{}/".format(routes[0].strip())
        print("Trying to connect to all of the app-instances using end-point {}".format(url))

        for i in range(num_instances):
            for j in range(max_attempts):
                _header = {"X-Cf-App-Instance": "{}:{}".format(appguid, i)}
                resp = requests.get(url, headers=_header)
                print("Instance-index: {}, Attempt: {}, response: {}".format(i, j, resp.status_code))
                if resp.status_code == 200:
                    print("Connection to index {} was successful in {} attempts".format(i, j+1))
                    app_instance_connection_results[i] = True
                    break

        if not all(app_instance_connection_results.values()):
            print("Could not reach to all instances of sample-app in {} attempts.".format(max_attempts*num_instances))
    except Exception as e:
        print(str(e))

    return all(app_instance_connection_results.values())


def main():
    result = True
    results = {}
    print("Starting PAS smoke-test...")
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

        manifest_path = os.path.join(pas_sample_app_path, 'manifest.yml')
        params = "{} -f {} -p {} --no-start".format(pas_sample_app, manifest_path, pas_sample_app_path)
        results['push_app'] = common_tests.push_app(params)
        if not results['push_app']:
            results['get_app_logs'] = common_tests.get_app_logs(pas_sample_app)
            raise Exception('push_app failed')
     
        results['start_app'] = common_tests.start_app(pas_sample_app)
        if not results['start_app']:
            results['get_app_logs'] = common_tests.get_app_logs(pas_sample_app)
            raise Exception('start_app failed')

        num_instances = 5
        results['scale_up_app'] = common_tests.scale_app(pas_sample_app, num_instances)
        if not results['scale_up_app']:
            raise Exception('scale_up_app failed')

        print('Sleeping for 20 seconds to let all instances come up...')
        time.sleep(20)

        results['show_app_info'] = common_tests.show_app_info(pas_sample_app)
        if not results['show_app_info']:
            raise Exception('show_app_info failed')

        results['test_app_instances_connection'] = test_app_instances_connection(num_instances)
        if not results['test_app_instances_connection']:
            raise Exception('test_app_instances_connection failed')

        results['scale_down_app'] = common_tests.scale_app(pas_sample_app, 1)
        if not results['scale_down_app']:
            raise Exception('scale_down_app failed')

        results['get_app_logs'] = common_tests.get_app_logs(pas_sample_app)
        if not results['get_app_logs']:
            raise Exception('get_app_logs failed')

    except Exception as e:
        print(str(e))
        result = False
    finally:
        try:
            results['delete_app'] = common_tests.delete_app(pas_sample_app)
            if not results['delete_app']:
                print('delete_app failed')
        except Exception as e:
            print(str(e))
            result = False

    if result and not all(value == True for value in results.values()):
        result = False
    print("Finished PAS smoke-test...")
    print(json.dumps(results, indent=1))
    print("Overall result: {}".format("Passed" if result else "Failed"))
    end = time.time()
    minutes_taken = (end-start)/60
    print("Total time taken: {} minutes".format(minutes_taken))
    results['overall_result'] = result
    results['minutes_taken'] = minutes_taken
    report_results.send_metric_to_influxdb('pas', results)
    return not result


if __name__ == "__main__":
    sys.exit(main())
