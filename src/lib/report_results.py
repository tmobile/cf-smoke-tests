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
import time


def send_metric_to_es(smoke_test_source, results):
    try:
        ES_INDEX = "cf_smoke_tests.{}".format(time.strftime("%Y.%m", time.localtime()))
        foundation = os.environ['FOUNDATION']
        es_url = "http://elasticsearch-cluster-url:9200/{}/_doc/".format(ES_INDEX)
        _timestamp = time.time()
        for metric, value in results.items():
            full_metric_name = "{}.{}".format(smoke_test_source, metric)
            metric_data = {
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(_timestamp)),
                "foundation": foundation,
                "metric": full_metric_name,
                "value": value if metric.lower() == 'minutes_taken' else int(value)
            }
            resp = requests.post(es_url, headers={"Content-type": "application/json"}, data=json.dumps(metric_data))
            print("Posting metric to elasticsearch: {}, status: {}, content: {}\n".format(full_metric_name, resp.status_code, resp.content))
    except Exception as e:
        print(str(e))


def send_metric_to_splunk(smoke_test_source, results):
    try:
        SPLUNK_METRICS_ENDPOINT = "https://splunk-url:8088/services/collector/event"
        foundation = os.environ['FOUNDATION']
        splunk_token = os.environ['SPLUNK_TOKEN']
        splunk_channel = os.environ['SPLUNK_CHANNEL']
        for metric, value in results.items():
            full_metric_name = "cf_smoke_tests.{}.{}".format(smoke_test_source, metric)
            metric_data = {
                "time": time.time(),
                "event": "metric",
                "fields": {
                    "metric_name": full_metric_name,
                    "_value": value if metric.lower() == 'minutes_taken' else int(value),
                    "foundation": foundation
                }
            }
            resp = requests.post(SPLUNK_METRICS_ENDPOINT, 
                                 headers={
                                          "Content-type": "application/json",
                                          "Authorization": "Splunk {}".format(splunk_token),
                                          "X-Splunk-Request-Channel": splunk_channel
                                 },
                                 data=json.dumps(metric_data))
            print("Posting metric to Splunk: {}, status: {}, content: {}\n".format(full_metric_name, resp.status_code, resp.content))
    except Exception as e:
        print(str(e))


def send_metric_to_influxdb(smoke_test_source, results):
    try:
        foundation = os.environ['FOUNDATION']
        INFLUXDB_METRICS_ENDPOINT = "https://influxdb-url/write?precision=s"
        concourse_url = "{}/teams/{}/pipelines/{}/jobs/{}/builds/{}".format(os.environ['ATC_EXTERNAL_URL'],
                                                                            os.environ['BUILD_TEAM_NAME'],
                                                                            os.environ['BUILD_PIPELINE_NAME'],
                                                                            os.environ['BUILD_JOB_NAME'],
                                                                            os.environ['BUILD_NAME'])
        for metric, status in results.items():
            full_metric_name = "cf_smoke_tests.{}.{}".format(smoke_test_source, metric)
            metric_data = "{},foundation={},metric_source={},concourse_url={} value={}".format(full_metric_name, foundation, smoke_test_source, concourse_url, int(status))
            resp = requests.post(INFLUXDB_METRICS_ENDPOINT, headers={"Content-type": "application/x-www-form-urlencoded"}, data=metric_data)
            print("Posting metric to influxdb: {}, status: {}, content: {}\n".format(full_metric_name, resp.status_code, resp.content))
    except Exception as e:
        print(str(e))
