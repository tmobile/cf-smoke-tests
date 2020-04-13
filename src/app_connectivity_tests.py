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

from lib import report_results

try:
    apps_manager_url = os.environ['FOUNDATION_APPS_DOMAIN']
    app1_url = os.environ['APP1_HEALTH_CHECK_URL']
except KeyError as e:
    print(str(e))
    exit(1)


def main():
    result = True
    results = {}
    print("Starting App Connectivity Tests...")
    start = time.time()
    try:
        #All foundations deployment apps
        print("Testing apps manager health...")
        r = requests.get(apps_manager_url)
        results['apps_manager'] = (r.status_code == 200)
        if not results['apps_manager']:
            print('Apps manager health check failed!')

        print("Testing app1 health...")
        r = requests.get(app1_url)
        results['app1'] = (r.status_code == 200)
        if not results['app1']:
            print('app1 health check failed!')

        # Add more internal-apps health-check here
    except Exception as e:
        print(str(e))
        result = False

    print("Finished App Connectivity Tests...")
    print(json.dumps(results, indent=1))
    end = time.time()
    minutes_taken = (end - start) / 60
    print("Total time taken: {} minutes".format(minutes_taken))
    results['minutes_taken'] = minutes_taken
    report_results.send_metric_to_influxdb('app-connectivity', results)
    return not result

if __name__ == "__main__":
    sys.exit(main())
