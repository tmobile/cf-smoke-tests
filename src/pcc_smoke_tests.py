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
    pcc_service_name = os.environ['PCC_SERVICE_NAME']
    pcc_service_plan = os.environ['PCC_SERVICE_PLAN']
    pcc_service_instance = os.environ['PCC_SERVICE_INSTANCE']
    pcc_service_key = os.environ['PCC_SERVICE_KEY']
    pcc_sample_app = os.environ['PCC_SAMPLE_APP']
    pcc_sample_app_path = os.path.join(os.getcwd(), "cf-smoke-tests", "sample_apps", pcc_sample_app)
    gemfire_product = os.environ['GEMFIRE_PRODUCT']
    gemfire_product_version = os.environ["GEMFIRE_VERSION"]
except KeyError as e:
    print(str(e))
    exit(1)


def extract_gemfire_tar():
    cmd = "tar -xzf {}-{}.tgz".format(gemfire_product, gemfire_product_version)
    if utils.run_cmd(cmd):
        os.environ['GEMFIRE_HOME'] = os.path.join(os.getcwd(), "{}-{}".format(gemfire_product, gemfire_product_version))
        if not os.listdir(os.environ['GEMFIRE_HOME']):
            return False
        os.environ['GFSH_CLI'] = os.path.join(os.environ['GEMFIRE_HOME'], 'bin', 'gfsh')
        return True
    else:
        return False


def gemfire_create_regions():
    if 'GFSH_CLI' not in os.environ or \
        'GEMFIRE_URL' not in os.environ or \
        'GEMFIRE_USER' not in os.environ or \
        'GEMFIRE_PASSWORD' not in os.environ:
        return False

    print('>>> Creating regions in gemfire cluster using gfsh cli...')
    connect_cmd = "\"connect --use-http --url={} --user={} --password={}\"".format(os.environ['GEMFIRE_URL'],
                                                                                   os.environ['GEMFIRE_USER'],
                                                                                   os.environ['GEMFIRE_PASSWORD'])
    create_test_region_cmd = "\"create region --name=test --type=PARTITION_REDUNDANT --redundant-copies=1\""
    create_partitioned_region_cmd = "\"create region --name=partitioned --type=PARTITION_REDUNDANT --redundant-copies=1\""
    create_replicated_region_cmd = "\"create region --name=replicated --type=REPLICATE\""

    cmd = "{} -e {} -e {} -e {} -e {}".format(os.environ['GFSH_CLI'],
                                              connect_cmd,
                                              create_test_region_cmd,
                                              create_partitioned_region_cmd,
                                              create_replicated_region_cmd)
    return utils.run_cmd(cmd, False)


def gemfire_write_helper(gfsh_cli, connect_cmd, region, key, value):
    write_cmd = "\"put --region=/{} --key={} --value='{}'\"".format(region, key, value)
    cmd = "{} -e {} -e {}".format(gfsh_cli, connect_cmd, write_cmd)
    if not utils.run_cmd(cmd, False):
        return False
    return True


def gemfire_write():
    if 'GFSH_CLI' not in os.environ or \
        'GEMFIRE_URL' not in os.environ or \
        'GEMFIRE_USER' not in os.environ or \
        'GEMFIRE_PASSWORD' not in os.environ:
        return False

    print('>>> Writing to gemfire cluster using gfsh cli...')
    connect_cmd = "\"connect --use-http --url={} --user={} --password={}\"".format(os.environ['GEMFIRE_URL'],
                                                                                   os.environ['GEMFIRE_USER'],
                                                                                   os.environ['GEMFIRE_PASSWORD'])

    write_results = []
    write_results.append(gemfire_write_helper(os.environ['GFSH_CLI'], connect_cmd, 'partitioned', 2, "two-partitioned"))
    write_results.append(gemfire_write_helper(os.environ['GFSH_CLI'], connect_cmd, 'partitioned', 3, "three-partitioned"))
    write_results.append(gemfire_write_helper(os.environ['GFSH_CLI'], connect_cmd, 'partitioned', 4, "four-partitioned"))
    write_results.append(gemfire_write_helper(os.environ['GFSH_CLI'], connect_cmd, 'replicated', 5, "five-replicated"))
    write_results.append(gemfire_write_helper(os.environ['GFSH_CLI'], connect_cmd, 'replicated', 6, "six-replicated"))
    write_results.append(gemfire_write_helper(os.environ['GFSH_CLI'], connect_cmd, 'replicated', 7, "seven-replicated"))
    if not all(write_results):
        return False
    return True


def gemfire_read_helper(gfsh_cli, connect_cmd, region):
    desc_cmd = "\"describe region --name={}\"".format(region)
    read_cmd = "\"query --query='select * from /{}'\"".format(region)
    cmd = "{} -e {} -e {} -e {}".format(gfsh_cli, connect_cmd, desc_cmd, read_cmd)
    return utils.run_cmd(cmd, False)


def gemfire_read():
    if 'GFSH_CLI' not in os.environ or \
        'GEMFIRE_URL' not in os.environ or \
        'GEMFIRE_USER' not in os.environ or \
        'GEMFIRE_PASSWORD' not in os.environ:
        return False

    print('>>> Reading from gemfire cluster using gfsh cli...')
    connect_cmd = "\"connect --use-http --url={} --user={} --password={}\"".format(os.environ['GEMFIRE_URL'],
                                                                                   os.environ['GEMFIRE_USER'],
                                                                                   os.environ['GEMFIRE_PASSWORD'])
    read_results = []
    read_results.append(gemfire_read_helper(os.environ['GFSH_CLI'], connect_cmd, "test"))
    read_results.append(gemfire_read_helper(os.environ['GFSH_CLI'], connect_cmd, "partitioned"))
    read_results.append(gemfire_read_helper(os.environ['GFSH_CLI'], connect_cmd, "replicated"))
    if not all(read_results):
        return False
    return True


def main():
    result = True
    results = {}
    print("Starting PCC smoke-test...")
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

        results['list_marketplace_service'] = common_tests.list_marketplace_service(pcc_service_name)
        if not results['list_marketplace_service']:
            raise Exception('list_marketplace_service failed')

        results['create_service'] = common_tests.create_service(pcc_service_name, pcc_service_plan, pcc_service_instance)
        if not results['create_service']:
            raise Exception('create_service failed')

        results['show_service_info'] = common_tests.show_service_info(pcc_service_instance)
        if not results['show_service_info']:
            raise Exception('show_service_info failed')

        results['create_service_key'] = common_tests.create_service_key(pcc_service_instance, pcc_service_key)
        if not results['create_service_key']:
            raise Exception('create_service_key failed')

        results['show_service_key_info'], service_key = common_tests.show_service_key_info(pcc_service_instance, pcc_service_key)
        if not results['show_service_key_info']:
            raise Exception('show_service_key_info failed')
        else:
            os.environ['GEMFIRE_URL'] = str(service_key['urls']['gfsh'])
            for user in service_key['users']:
                if user['username'].startswith('cluster_operator'):
                    os.environ['GEMFIRE_USER'] = str(user["username"])
                    os.environ['GEMFIRE_PASSWORD'] = str(user["password"])
                    break

        results['pivnet_login' ] = common_tests.pivnet_login()
        if not results['pivnet_login']:
            raise Exception('pivnet_login failed')

        results['pivnet_get_product_id'], product_id = common_tests.pivnet_get_product_id(gemfire_product, gemfire_product_version, 'Tar')
        if not results['pivnet_get_product_id']:
            raise Exception('pivnet_get_product_id failed')

        results['pivnet_accept_eula'] = common_tests.pivnet_accept_eula(gemfire_product, gemfire_product_version)
        if not results['pivnet_accept_eula']:
            raise Exception('pivnet_accept_eula failed')

        results['pivnet_download_product_files'] = common_tests.pivnet_download_product_files(gemfire_product, gemfire_product_version, product_id)
        if not results['pivnet_download_product_files']:
            raise Exception('pivnet_download_product_files failed')

        results['pivnet_logout'] = common_tests.pivnet_logout()
        if not results['pivnet_logout']:
            raise Exception('pivnet_logout failed')

        results['extract_gemfire_tar'] = extract_gemfire_tar()
        if not results['extract_gemfire_tar']:
            raise Exception('extract_gemfire_tar failed')

        results['gemfire_create_regions'] = gemfire_create_regions()
        if not results['gemfire_create_regions']:
            raise Exception('gemfire_create_regions failed')

        results['gemfire_write'] = gemfire_write()
        if not results['gemfire_write']:
            raise Exception('gemfire_write failed')

        print(">>> Updating the sample-app manifest...")
        cmd = "cd {} && sed -i -e \'s/service0/{}/g\' manifest.yml".format(pcc_sample_app_path, pcc_service_instance)
        utils.run_cmd(cmd)

        print(">>> Updating username, password and gemfire-version in sample-app config...")
        cmd = "cd {} && \
               sed -i -e \'s/SAMPLE_USERNAME/{}/g\' gradle.properties && \
               sed -i -e \'s/SAMPLE_PASSWORD/{}/g\' gradle.properties && \
               sed -i -e \'s/9.0.2/{}/g\' build.gradle".format(pcc_sample_app_path,
                                                               os.environ['SMOKE_USER'],
                                                               os.environ['SMOKE_PASSWORD'].replace("&", "\&"),
                                                               gemfire_product_version)
        utils.run_cmd(cmd, False, False)

        print(">>> Building the sample-app...")
        cmd = "cd {} && ./gradlew clean build".format(pcc_sample_app_path)
        utils.run_cmd(cmd)

        manifest_path = os.path.join(pcc_sample_app_path, 'manifest.yml')
        params = "{} -f {} -p {} --no-start".format(pcc_sample_app, manifest_path, pcc_sample_app_path)
        results['push_app'] = common_tests.push_app(params)
        if not results['push_app']:
            results['get_app_logs'] = common_tests.get_app_logs(pcc_sample_app)
            raise Exception('push_app failed')

        results['bind_service'] = common_tests.bind_service(pcc_sample_app, pcc_service_instance)
        if not results['bind_service']:
            raise Exception('bind_service failed')

        results['gemfire_read'] = gemfire_read()
        if not results['gemfire_read']:
            raise Exception('gemfire_read failed')

    except Exception as e:
        print(str(e))
        result = False
    finally:
        try:
            results['unbind_service'] = common_tests.unbind_service(pcc_sample_app, pcc_service_instance)
            if not results['unbind_service']:
                print('unbind_service failed')
        except Exception as e:
            print(str(e))
            result = False
        
        try:
            results['delete_service_key'] = common_tests.delete_service_key(pcc_service_instance, pcc_service_key)
            if not results['delete_service_key']:
                print('delete_service_key failed')
        except Exception as e:
            print(str(e))
            result = False

        try:
            results['delete_app'] = common_tests.delete_app(pcc_sample_app)
            if not results['delete_app']:
                print('delete_app failed')
        except Exception as e:
            print(str(e))
            result = False

        try:
            results['delete_service'] = common_tests.delete_service(pcc_service_instance)
            if not results['delete_service']:
                print('delete_service failed')
        except Exception as e:
            print(str(e))
            result = False

    if result and not all(value == True for value in results.values()):
        result = False
    print("Finished PCC smoke-test...")
    print(json.dumps(results, indent=1))
    print("Overall result: {}".format("Passed" if result else "Failed"))
    end = time.time()
    minutes_taken = (end-start)/60
    print("Total time taken: {} minutes".format(minutes_taken))
    results['overall_result'] = result
    results['minutes_taken'] = minutes_taken
    report_results.send_metric_to_influxdb('pcc', results)
    return not result


if __name__ == "__main__":
    sys.exit(main())
