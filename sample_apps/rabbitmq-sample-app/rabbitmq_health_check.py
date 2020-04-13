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
import pika

app = Flask(__name__)

#Getting Service Info
env_vars = os.getenv('VCAP_SERVICES')
rmq_service = str(os.getenv('RMQ_SERVICE', 'p-rabbitmq'))
service = json.loads(env_vars)[rmq_service][0]
amqp_url = service['credentials']['protocols']['amqp']['uri']


@app.route('/write', methods=['POST'])
def write_into_queue():
    try:
        data = request.data
        connection = pika.BlockingConnection(pika.URLParameters(amqp_url))
        channel = connection.channel()
        channel.queue_declare(queue='test_queue')
        channel.basic_publish(exchange='', routing_key='test_queue', body=data)
        connection.close()
    except Exception as e:
        print(str(e))
        return jsonify({'error': 'Failed to write the message into rabbitmq'}), 500

    return jsonify({'status': 'Successfully written the message into rabbitmq'}), 201


@app.route('/read', methods=['GET'])
def read_from_queue():
    try:
        connection = pika.BlockingConnection(pika.URLParameters(amqp_url))
        channel = connection.channel()
        channel.queue_declare(queue='test_queue')
        method_frame, _, body = channel.basic_get(queue='test_queue')
        if method_frame.NAME == 'Basic.GetEmpty':
            connection.close()
            body = ''
        else:
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)
            connection.close()
    except Exception as e:
        print(str(e))
        return jsonify({'error': 'Failed to read the message from rabbitmq'}), 500

    return jsonify({'message': str(body, 'utf-8')}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
