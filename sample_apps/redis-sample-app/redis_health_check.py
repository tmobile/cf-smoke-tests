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
from flask import Flask, request, jsonify
import json
import os
import redis

app = Flask(__name__)

#Getting Service Info
env_vars = os.getenv('VCAP_SERVICES')
redis_service = str(os.getenv('REDIS_SERVICE', 'p-redis'))
service = json.loads(env_vars)[redis_service][0]
redis_host = service['credentials']['host']
redis_port = service['credentials']['port']
redis_password = service['credentials']['password']
cache = redis.StrictRedis(host=redis_host, port=redis_port, password=redis_password, decode_responses=True)

@app.route('/write', methods=['POST'])
def write_into_queue():
    try:
        data = json.loads(request.data)
        for key, value in data.items():
            cache.set(key, value, ex=86400)
    except Exception as e:
        print(str(e))
        return jsonify({'error': 'Failed to write the message into redis, {}'.format(str(e))}), 500

    return jsonify({'status': 'Successfully written the message into redis'}), 201


@app.route('/read/<key>', methods=['GET'])
def read_from_queue(key):
    try:
        value = cache.get(key)
    except Exception as e:
        print(str(e))
        return jsonify({'error': 'Failed to read the message from redis. {}'.format(str(e))}), 500

    return jsonify({key: value}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
