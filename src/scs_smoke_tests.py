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
    config_server_service_name = os.environ['CONFIG_SERVER_SERVICE_NAME']
    config_server_service_plan = os.environ['CONFIG_SERVER_SERVICE_PLAN']
    config_server_service_instance = os.environ['CONFIG_SERVER_SERVICE_INSTANCE']
    circuit_breaker_service_name = os.environ['CIRCUIT_BREAKER_SERVICE_NAME']
    circuit_breaker_service_plan = os.environ['CIRCUIT_BREAKER_SERVICE_PLAN']
    circuit_breaker_service_instance = os.environ['CIRCUIT_BREAKER_SERVICE_INSTANCE']
    service_registry_service_name = os.environ['SERVICE_REGISTRY_SERVICE_NAME']
    service_registry_service_plan = os.environ['SERVICE_REGISTRY_SERVICE_PLAN']
    service_registry_service_instance = os.environ['SERVICE_REGISTRY_SERVICE_INSTANCE']
    mysql_service_name = os.environ['SCS_MYSQL_SERVICE_NAME']
    mysql_service_plan = os.environ['SCS_MYSQL_SERVICE_PLAN']
    mysql_service_instance = os.environ['SCS_MYSQL_SERVICE_INSTANCE']
    scs_sample_app = os.environ['SCS_SAMPLE_APP']
    scs_sample_app_path = os.path.join(os.getcwd(), "cf-smoke-tests", "sample_apps", scs_sample_app)
    scs_sample_app_uri = os.environ['SCS_SAMPLE_APP_URI']
    scs_sample_app_key = os.environ['SCS_SAMPLE_APP_KEY']
    fortune_ui_app = 'fortune-ui'
    fortune_ui_app_path = os.path.join(scs_sample_app_path, fortune_ui_app, 'manifest.yml')
    fortune_svc_app = 'fortune-service'
    fortune_svc_app_path = os.path.join(scs_sample_app_path, fortune_svc_app, 'manifest.yml')
except KeyError as e:
    print(str(e))
    exit(1)


def test_scs_app():
    results = {}
    results['fortune_ui.health'] = False
    results['fortune_svc.health'] = False
    results['fortune_ui.random'] = False
    try:
        print("Checking the health of Spring Cloud Services bound to fortune-teller app...")

        _ , ui_routes = utils.get_app_routes(fortune_ui_app)
        ui_health_url = "https://{}/health".format(ui_routes[0].strip())
        ui_random_url = "https://{}/random".format(ui_routes[0].strip())

        _ , svc_routes = utils.get_app_routes(fortune_svc_app)
        svc_health_url = "https://{}/health".format(svc_routes[0].strip())

        print(ui_health_url)
        resp = requests.get(ui_health_url)
        results['fortune_ui.health'] = (resp.status_code == 200)
        print("status: {},\ncontent: {}\n".format(resp.status_code, resp.content))

        print(svc_health_url)
        resp = requests.get(svc_health_url)
        results['fortune_svc.health'] = (resp.status_code == 200)
        print("status: {},\ncontent: {}\n".format(resp.status_code, resp.content))

        print(ui_random_url)
        resp = requests.get(ui_random_url)
        results['fortune_ui.random'] = (resp.status_code == 200)
        print("status: {},\ncontent: {}\n".format(resp.status_code, resp.content))

        print("Stoping fortune-service app...")
        common_tests.stop_app(fortune_svc_app)

        print(ui_random_url)
        resp = requests.get(ui_random_url)
        results['fortune_ui.random'] = results['fortune_ui.random'] and (resp.status_code == 200)
        print("status: {},\ncontent: {}\n".format(resp.status_code, resp.content))

        print("Starting fortune-service app...")
        if not common_tests.start_app(fortune_svc_app):
            results['fortune_svc.get_app_logs'] = common_tests.get_app_logs(fortune_svc_app)

        print(ui_random_url)
        resp = requests.get(ui_random_url)
        results['fortune_ui.random'] = results['fortune_ui.random'] and (resp.status_code == 200)
        print("status: {},\ncontent: {}\n".format(resp.status_code, resp.content))

    except Exception as e:
        print(str(e))
    return results


def main():
    result = True
    results = {}
    print("Starting SCS smoke-test...")
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

        config_server_config = {
            "git": {
                "uri": scs_sample_app_uri,
                "privateKey": scs_sample_app_key,
                "searchPaths": "sample_apps/scs-sample-app/configuration"
            }
        }
        results['config_server.create_service'] = common_tests.create_service(config_server_service_name,
                                                                              config_server_service_plan,
                                                                              config_server_service_instance,
                                                                              config_server_config)
        if not results['config_server.create_service']:
            raise Exception('create_service failed for config_server')

        results['service_registry.create_service'] = common_tests.create_service(service_registry_service_name,
                                                                                 service_registry_service_plan,
                                                                                 service_registry_service_instance)
        if not results['service_registry.create_service']:
            raise Exception('create_service failed for service_registry')

        results['circuit_breaker.create_service'] = common_tests.create_service(circuit_breaker_service_name,
                                                                                circuit_breaker_service_plan,
                                                                                circuit_breaker_service_instance)
        if not results['circuit_breaker.create_service']:
            raise Exception('create_service failed for circuit_breaker')

        results['mysql.create_service'] = common_tests.create_service(mysql_service_name,
                                                                      mysql_service_plan,
                                                                      mysql_service_instance)
        if not results['mysql.create_service']:
            raise Exception('create_service failed for mysql')

        results['config_server.show_service_info'] = common_tests.show_service_info(config_server_service_instance)
        if not results['config_server.show_service_info']:
            raise Exception('show_service_info failed for config_server')

        results['service_registry.show_service_info'] = common_tests.show_service_info(service_registry_service_instance)
        if not results['service_registry.show_service_info']:
            raise Exception('show_service_info failed for service_registry')

        results['circuit_breaker.show_service_info'] = common_tests.show_service_info(circuit_breaker_service_instance)
        if not results['circuit_breaker.show_service_info']:
            raise Exception('show_service_info failed for circuit_breaker')

        params = "{} -f {} --no-start".format(fortune_ui_app, fortune_ui_app_path)
        results['fortune_ui.push_app'] = common_tests.push_app(params)
        if not results['fortune_ui.push_app']:
            raise Exception('push_app failed for fortune_ui_app')

        params = "{} -f {} --no-start".format(fortune_svc_app, fortune_svc_app_path)
        results['fortune_svc.push_app'] = common_tests.push_app(params)
        if not results['fortune_svc.push_app']:
            raise Exception('push_app failed for fortune_svc_app')

        results['config_server.fortune_ui.bind_service'] = common_tests.bind_service(fortune_ui_app, config_server_service_instance)
        if not results['config_server.fortune_ui.bind_service']:
            raise Exception('bind_service failed for config_server - fortune_ui_app')

        results['service_registry.fortune_ui.bind_service'] = common_tests.bind_service(fortune_ui_app, service_registry_service_instance)
        if not results['service_registry.fortune_ui.bind_service']:
            raise Exception('bind_service failed for service_registry - fortune_ui_app')

        results['circuit_breaker.fortune_ui.bind_service'] = common_tests.bind_service(fortune_ui_app, circuit_breaker_service_instance)
        if not results['circuit_breaker.fortune_ui.bind_service']:
            raise Exception('bind_service failed for circuit_breaker - fortune_ui_app')

        results['config_server.fortune_svc.bind_service'] = common_tests.bind_service(fortune_svc_app, config_server_service_instance)
        if not results['config_server.fortune_svc.bind_service']:
            raise Exception('bind_service failed for config_server - fortune_svc_app')

        results['service_registry.fortune_svc.bind_service'] = common_tests.bind_service(fortune_svc_app, service_registry_service_instance)
        if not results['service_registry.fortune_svc.bind_service']:
            raise Exception('bind_service failed for service_registry - fortune_svc_app')

        results['circuit_breaker.fortune_svc.bind_service'] = common_tests.bind_service(fortune_svc_app, circuit_breaker_service_instance)
        if not results['circuit_breaker.fortune_svc.bind_service']:
            raise Exception('bind_service failed for circuit_breaker - fortune_svc_app')

        results['fortune_ui.start_app'] = common_tests.start_app(fortune_ui_app)
        if not results['fortune_ui.start_app']:
            results['fortune_ui.get_app_logs'] = common_tests.get_app_logs(fortune_ui_app)
            raise Exception('start_app failed for fortune_ui_app')

        results['fortune_svc.start_app'] = common_tests.start_app(fortune_svc_app)
        if not results['fortune_svc.start_app']:
            results['fortune_svc.get_app_logs'] = common_tests.get_app_logs(fortune_svc_app)
            raise Exception('start_app failed for fortune_svc_app')

        results.update(test_scs_app())
        if not results['fortune_ui.health']:
            raise Exception('health-check failed for fortune_ui_app')
        if not results['fortune_ui.random']:
            raise Exception('config-check failed for fortune_ui_app')
        if not results['fortune_svc.health']:
            raise Exception('health-check failed for fortune_svc_app')

    except Exception as e:
        print(str(e))
        result = False
    finally:
        try:
            results['config_server.fortune_ui.unbind_service'] = common_tests.unbind_service(fortune_ui_app, config_server_service_instance)
            if not results['config_server.fortune_ui.unbind_service']:
                print('unbind_service failed for config_server - fortune_ui_app')
        except Exception as e:
            print(str(e))
            result = False

        try:
            results['service_registry.fortune_ui.unbind_service'] = common_tests.unbind_service(fortune_ui_app, service_registry_service_instance)
            if not results['service_registry.fortune_ui.unbind_service']:
                print('unbind_service failed for service_registry - fortune_ui_app')
        except Exception as e:
            print(str(e))
            result = False

        try:
            results['circuit_breaker.fortune_ui.unbind_service'] = common_tests.unbind_service(fortune_ui_app, circuit_breaker_service_instance)
            if not results['circuit_breaker.fortune_ui.unbind_service']:
                print('unbind_service failed for circuit_breaker - fortune_ui_app')
        except Exception as e:
            print(str(e))
            result = False

        try:
            results['config_server.fortune_svc.unbind_service'] = common_tests.unbind_service(fortune_svc_app, config_server_service_instance)
            if not results['config_server.fortune_svc.unbind_service']:
                print('unbind_service failed for config_server - fortune_svc_app')
        except Exception as e:
            print(str(e))
            result = False

        try:
            results['service_registry.fortune_svc.unbind_service'] = common_tests.unbind_service(fortune_svc_app, service_registry_service_instance)
            if not results['service_registry.fortune_svc.unbind_service']:
                print('unbind_service failed for service_registry - fortune_svc_app')
        except Exception as e:
            print(str(e))
            result = False

        try:
            results['circuit_breaker.fortune_svc.unbind_service'] = common_tests.unbind_service(fortune_svc_app, circuit_breaker_service_instance)
            if not results['circuit_breaker.fortune_svc.unbind_service']:
                print('unbind_service failed for circuit_breaker - fortune_svc_app')
        except Exception as e:
            print(str(e))
            result = False

        try:
            results['fortune_ui.delete_app'] = common_tests.delete_app(fortune_ui_app)
            if not results['fortune_ui.delete_app']:
                print('delete_app failed for fortune_ui_app')
        except Exception as e:
            print(str(e))
            result = False

        try:
            results['fortune_svc.delete_app'] = common_tests.delete_app(fortune_svc_app)
            if not results['fortune_svc.delete_app']:
                print('delete_app failed for fortune_svc_app')
        except Exception as e:
            print(str(e))
            result = False

        try:
            results['mysql.delete_service'] = common_tests.delete_service(mysql_service_instance)
            if not results['mysql.delete_service']:
                print('delete_service failed for mysql')
        except Exception as e:
            print(str(e))
            result = False

        try:
            results['config_server.delete_service'] = common_tests.delete_service(config_server_service_instance)
            if not results['config_server.delete_service']:
                print('delete_service failed for config_server')
        except Exception as e:
            print(str(e))
            result = False

        try:
            results['service_registry.delete_service'] = common_tests.delete_service(service_registry_service_instance)
            if not results['service_registry.delete_service']:
                print('delete_service failed for service_registry')
        except Exception as e:
            print(str(e))
            result = False

        try:
            results['circuit_breaker.delete_service'] = common_tests.delete_service(circuit_breaker_service_instance)
            if not results['circuit_breaker.delete_service']:
                print('delete_service failed for circuit_breaker')
        except Exception as e:
            print(str(e))
            result = False

    if result and not all(value == True for value in results.values()):
        result = False
    print("Finished SCS smoke-test...")
    print(json.dumps(results, indent=1))
    print("Overall result: {}".format("Passed" if result else "Failed"))
    end = time.time()
    minutes_taken = (end-start)/60
    print("Total time taken: {} minutes".format(minutes_taken))
    results['overall_result'] = result
    results['minutes_taken'] = minutes_taken
    report_results.send_metric_to_influxdb('scs', results)
    return not result


if __name__ == "__main__":
    sys.exit(main())
