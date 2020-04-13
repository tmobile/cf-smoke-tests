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
import os
import sys
import time
import yaml

from  lib import utils

def main():
    result = True
    try:
        params = {}
        envs_dir = os.path.join(os.getcwd(), 'cf-smoke-tests', 'environments')
        global_params_file = os.path.join(envs_dir, 'global-pipeline-vars.yml')
        params = yaml.full_load(open(global_params_file, 'r'))
        dirs = os.listdir(envs_dir)
        for d in dirs:
            foundation_dir = os.path.join(envs_dir, d)
            if os.path.isdir(foundation_dir):
                params_file = os.path.join(foundation_dir, 'pipeline-vars.yml')
                params.update(yaml.full_load(open(params_file, 'r')))
                print("Deploying smoke-test-pipline for foundation {}".format(params['FOUNDATION']))
                login_cmd = "fly --target ci-{} login --concourse-url {} -k --username {} --password {} --team-name {}".format(params['FOUNDATION'],
                                                                                                                               params['CONCOURSE_URL'],
                                                                                                                               params['CONCOURSE_USERNAME'],
                                                                                                                               os.environ['CONCOURSE_PASSWORD_FOR_{}'.format(params['FOUNDATION'])],
                                                                                                                               params['FOUNDATION'])
                if not utils.run_cmd(login_cmd, False):
                    print("Fly login failed for {}".format(params['FOUNDATION']))
                    continue
                cmd = "fly --target ci-{} login --concourse-url {} -k --username {} --password {} --team-name {}".format(params['FOUNDATION'],
                                                                                                                               params['CONCOURSE_URL'],
                                                                                                                               params['CONCOURSE_USERNAME'],
                                                                                                                               "[Redacted Password]",
                                                                                                                               params['FOUNDATION'])
                print(cmd)

                sync_cmd = "fly -t ci-{} sync".format(params['FOUNDATION'])
                if not utils.run_cmd(sync_cmd):
                    print("Fly sync failed for {}".format(params['FOUNDATION']))
                    continue

                smoke_test_pipeline = os.path.join(os.getcwd(), 'cf-smoke-tests', 'ci', 'pipelines', 'pipeline.yml')
                set_pipeline_cmd = "fly --target ci-{} set-pipeline -c {} -p {} -l {} -l {} --non-interactive".format(params['FOUNDATION'],
                                                                                                                      smoke_test_pipeline,
                                                                                                                      params['PIPELINE_NAME'],
                                                                                                                      global_params_file,
                                                                                                                      params_file)
                if not utils.run_cmd(set_pipeline_cmd):
                    print("Fly set-pipeline failed for {}".format(params['FOUNDATION']))
                    continue

                unpause_pipeline_cmd = "fly --target ci-{} unpause-pipeline -p {}".format(params['FOUNDATION'],
                                                                                          params['PIPELINE_NAME'])
                if not utils.run_cmd(unpause_pipeline_cmd):
                    print("Fly unpause-pipeline failed for {}".format(params['FOUNDATION']))
                    continue
    except Exception as e:
        print(str(e))
        result = False

    return not result


if __name__ == "__main__":
    sys.exit(main())
