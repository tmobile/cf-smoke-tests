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
import glob
import json
import os
import requests
import sys
import time

from  lib import common_tests, utils, report_results

try:
    foundation = os.environ['FOUNDATION']
    autoscaler_sample_app = os.environ['AUTOSCALER_SAMPLE_APP']
    autoscaler_sample_app_path = os.path.join(os.getcwd(), "cf-smoke-tests", "sample_apps", "pas-sample-app")
    autoscaler_product = os.environ['AUTOSCALER_PRODUCT']
    autoscaler_product_version = os.environ["AUTOSCALER_VERSION"]
    autoscaler_service_name = os.environ["AUTOSCALER_SERVICE_NAME"]
    autoscaler_service_plan = os.environ["AUTOSCALER_SERVICE_PLAN"]
    autoscaler_service_instance = os.environ["AUTOSCALER_SERVICE_INSTANCE"]
except KeyError as e:
    print(str(e))
    exit(1)

def generate_http_traffic():
    try:
        _ , routes = utils.get_app_routes(autoscaler_sample_app)
        url = "https://{}/".format(routes[0].strip())

        print("Sending HTTP GET requests to the app for 15 min without any delays between each request...")
        t_end = time.time() + 60*15
        num_requests = 0
        while time.time() < t_end:
            resp = requests.get(url)
            num_requests = num_requests + 1
        print("Sent {} requests in last 15 min".format(num_requests))

        num_requests = 0
        print("Sending HTTP GET requests to the app for 10 min with 10 seconds delay between each request...")
        t_end = time.time() + 60*10
        while time.time() < t_end:
            time.sleep(10)
            resp = requests.get(url)
            num_requests = num_requests + 1
        print("Sent {} requests in last 10 min".format(num_requests))

    except Exception as e:
        print(str(e))


def check_autoscaling_app_state(appname):
    if not common_tests.login(os.environ["SMOKE_USER"], os.environ["SMOKE_PASSWORD"], "system", "autoscaling"):
        return False
    cmd = "cf curl /v2/apps?q=name:{}".format(appname)
    status, out = utils.run_cmd(cmd, True, False, True)
    if status and json.loads(out)['total_results'] > 0:
        if json.loads(out)['resources'][0]['entity']['state'] == 'STARTED':
            return True
        else:
            print("Going to start the {} app...".format(appname))
            if not common_tests.start_app(appname):
                raise Exception('Attempt to start the {} app failed'.format(appname))
    elif status and json.loads(out)['total_results'] == 0:
        raise Exception('{} app was not found'.format(appname))
    else:
        return False


def main():
    result = True
    results = {}
    print("Starting AUTO-SCALING smoke-test...")
    start = time.time()
    try:
        os.environ['CF_DIAL_TIMEOUT'] = "30"
        print(os.environ['CF_DIAL_TIMEOUT'])

        results['autoscale_state'] = check_autoscaling_app_state('autoscale')
        if not results['autoscale_state']:
            raise Exception('autoscale app is down')

        results['autoscale_api_state'] = check_autoscaling_app_state('autoscale-api')
        if not results['autoscale_api_state']:
            raise Exception('autoscale-api app is down')

        results['set_api'] = common_tests.set_api()
        if not results['set_api']:
            raise Exception('set_api failed')

        results['authenticate'] = common_tests.authenticate()
        if not results['authenticate']:
            raise Exception('authenticate failed')

        results['set_target'] = common_tests.set_target()
        if not results['set_target']:
            raise Exception('set_target failed')

        results['pivnet_login' ] = common_tests.pivnet_login()
        if not results['pivnet_login']:
            raise Exception('pivnet_login failed')

        results['pivnet_get_product_id'], product_id = common_tests.pivnet_get_product_id(autoscaler_product, autoscaler_product_version, 'linux64')
        if not results['pivnet_get_product_id']:
            raise Exception('pivnet_get_product_id failed')

        results['pivnet_accept_eula'] = common_tests.pivnet_accept_eula(autoscaler_product, autoscaler_product_version)
        if not results['pivnet_accept_eula']:
            raise Exception('pivnet_accept_eula failed')

        results['pivnet_download_product_files'] = common_tests.pivnet_download_product_files(autoscaler_product, autoscaler_product_version, product_id)
        if not results['pivnet_download_product_files']:
            raise Exception('pivnet_download_product_files failed')

        results['pivnet_logout'] = common_tests.pivnet_logout()
        if not results['pivnet_logout']:
            raise Exception('pivnet_logout failed')

        results['install_autoscaler_plugin'] = utils.run_cmd("cf install-plugin -f {}".format(os.path.join(os.getcwd(), glob.glob('autoscaler-for-pcf-*')[0])))
        if not results['install_autoscaler_plugin']:
            raise Exception('install_autoscaler_plugin failed')

        results['create_service'] = common_tests.create_service(autoscaler_service_name, autoscaler_service_plan, autoscaler_service_instance)
        if not results['create_service']:
            raise Exception('create_service failed')

        manifest_path = os.path.join(autoscaler_sample_app_path, 'manifest.yml')
        params = "{} -f {} -p {} --no-start".format(autoscaler_sample_app, manifest_path, autoscaler_sample_app_path)
        results['push_app'] = common_tests.push_app(params)
        if not results['push_app']:
            results['get_app_logs'] = common_tests.get_app_logs(autoscaler_sample_app)
            raise Exception('push_app failed')

        results['bind_service'] = common_tests.bind_service(autoscaler_sample_app, autoscaler_service_instance)
        if not results['bind_service']:
            raise Exception('bind_service failed')

        results['start_app'] = common_tests.start_app(autoscaler_sample_app)
        if not results['start_app']:
            results['get_app_logs'] = common_tests.get_app_logs(autoscaler_sample_app)
            raise Exception('start_app failed')

        min_instances = 3
        max_instances = 5
        results['update_autoscaling_limits'] = utils.run_cmd("cf update-autoscaling-limits {} {} {}".format(autoscaler_sample_app, min_instances, max_instances))
        if not results['update_autoscaling_limits']:
            raise Exception('update_autoscaling_limits failed')

        results['enable_autoscaling'] = utils.run_cmd("cf enable-autoscaling {}".format(autoscaler_sample_app))
        if not results['enable_autoscaling']:
            raise Exception('enable_autoscaling failed')

        results['autoscaling_apps'] = utils.run_cmd("cf autoscaling-apps")
        if not results['autoscaling_apps']:
            raise Exception('autoscaling_apps failed')

        results['autoscaling_rules'] = utils.run_cmd("cf autoscaling-rules {}".format(autoscaler_sample_app))
        if not results['autoscaling_rules']:
            raise Exception('autoscaling_rules failed')

        results['create_rule_http_throughput'] = utils.run_cmd("cf create-autoscaling-rule {} http_throughput 10 50".format(autoscaler_sample_app))
        if not results['create_rule_http_throughput']:
            raise Exception('create_rule_http_throughput failed')

        results['create_rule_http_latency'] = utils.run_cmd("cf create-autoscaling-rule {} http_latency 10 20 -s avg_99th".format(autoscaler_sample_app))
        if not results['create_rule_http_latency']:
            raise Exception('create_rule_http_latency failed')

        results['create_rule_cpu'] = utils.run_cmd("cf create-autoscaling-rule {} cpu 10 60".format(autoscaler_sample_app))
        if not results['create_rule_cpu']:
            raise Exception('create_rule_cpu failed')

        results['create_rule_memory'] = utils.run_cmd("cf create-autoscaling-rule {} memory 20 80".format(autoscaler_sample_app))
        if not results['create_rule_memory']:
            raise Exception('create_rule_memory failed')

        results['autoscaling_rules'] = utils.run_cmd("cf autoscaling-rules {}".format(autoscaler_sample_app))
        if not results['autoscaling_rules']:
            raise Exception('autoscaling_rules failed')

        generate_http_traffic()

        results['autoscaling_events'] = utils.run_cmd("cf autoscaling-events {}".format(autoscaler_sample_app))
        if not results['autoscaling_events']:
            raise Exception('autoscaling_events failed')

    except Exception as e:
        print(str(e))
        result = False
    finally:
        try:
            results['delete_autoscaling_rules'] = utils.run_cmd("cf delete-autoscaling-rules -f {}".format(autoscaler_sample_app))
            if not results['delete_autoscaling_rules']:
                print('delete_autoscaling_rules failed')
        except Exception as e:
            print(str(e))
            result = False

        try:
            results['disable_autoscaling'] = utils.run_cmd('cf disable-autoscaling {}'.format(autoscaler_sample_app))
            if not results['disable_autoscaling']:
                print('disable_autoscaling failed')
        except Exception as e:
            print(str(e))
            result = False

        try:
            results['unbind_service'] = common_tests.unbind_service(autoscaler_sample_app, autoscaler_service_instance)
            if not results['unbind_service']:
                print('unbind_service failed')
        except Exception as e:
            print(str(e))
            result = False

        try:
            results['delete_app'] = common_tests.delete_app(autoscaler_sample_app)
            if not results['delete_app']:
                print('delete_app failed')
        except Exception as e:
            print(str(e))
            result = False

        try:
            results['delete_service'] = common_tests.delete_service(autoscaler_service_instance)
            if not results['delete_service']:
                print('delete_service failed')
        except Exception as e:
            print(str(e))
            result = False

    if result and not all(value == True for value in results.values()):
        result = False
    print("Finished AUTO-SCALING smoke-test...")
    print(json.dumps(results, indent=1))
    print("Overall result: {}".format("Passed" if result else "Failed"))
    end = time.time()
    minutes_taken = (end-start)/60
    print("Total time taken: {} minutes".format(minutes_taken))
    results['overall_result'] = result
    results['minutes_taken'] = minutes_taken
    report_results.send_metric_to_influxdb('auto-scaler', results)
    return not result


if __name__ == "__main__":
    sys.exit(main())
