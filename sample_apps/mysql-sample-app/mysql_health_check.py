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
import json

from flask import Flask, make_response, request, jsonify

from db import db_session, initial_db
from models import User

app = Flask(__name__)
KEY_SIZE = 32
SECRET_KEY = os.urandom(KEY_SIZE)
app.config['SECRET_KEY'] = SECRET_KEY


@app.route('/')
def index():
    return make_response('This is a simple mysql health check app!', 200)


@app.route('/user', methods=['GET'])
def get_user():
    usr = db_session.query(User).first()
    usr_d = {}
    if usr:
        usr_d['id'] = vars(usr)['id']
        usr_d['name'] = vars(usr)['name']
        usr_d['email'] = vars(usr)['email']

    return make_response(jsonify(usr_d), 200)


@app.route('/users', methods=['GET'])
def get_users():
    usrs = db_session.query(User).all()
    usrs_list = []
    for usr in usrs:
        u = {}
        u['id'] = vars(usr)['id']
        u['name'] = vars(usr)['name']
        u['email'] = vars(usr)['email']
        usrs_list.append(u)

    return make_response(jsonify(usrs_list), 200)


@app.route('/user', methods=['POST'])
def add_user():
    u = User('PCF-Guy', 'pcf.guy@xyz.com')
    db_session.add(u)
    db_session.commit()
    user_id = db_session.query(User.id).order_by(User.id.desc()).first()[0]
    return make_response('The user-id for new user is ' + str(user_id), 201)


@app.route('/user', methods=['DELETE'])
def delete_user():
    _args = request.args.to_dict()
    if 'id' in _args:
        usr = db_session.query(User).filter_by(id=_args['id']).first()
    elif 'name' in _args:
        usr = db_session.query(User).filter_by(name=_args['name']).first()
    elif 'email' in _args:
        usr = db_session.query(User).filter_by(email=_args['email']).first()

    if usr:
        db_session.delete(usr)
        db_session.commit()
    return make_response('User deleted!', 200)


@app.route('/user', methods=['PUT'])
def update_user():
    _args = request.args.to_dict()
    if 'id' in _args:
        usr = db_session.query(User).filter_by(id=int(_args['id'])).first()
        if usr:
            if 'name' in _args:
                usr.name = _args['name']
            if 'email' in _args:
                usr.email = _args['email']
            db_session.commit()
    return make_response('User updated!', 200)


port = os.getenv('PORT', '5000')
if __name__ == "__main__":
    initial_db()
    app.run(host='0.0.0.0', port=int(port))
