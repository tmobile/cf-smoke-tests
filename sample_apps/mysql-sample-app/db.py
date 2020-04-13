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
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

app_env = json.loads(os.environ['VCAP_SERVICES'])
if 'p-mysql' in app_env:
    db_uri = app_env['p-mysql'][0]['credentials']['uri']
elif 'p.mysql' in app_env:
    db_uri = app_env['p.mysql'][0]['credentials']['uri']
else:
    sys.exit(1)

db_uri = db_uri[:db_uri.index('?reconnect=true')]
engine = create_engine(db_uri, echo=True, )
DB_Session = sessionmaker(bind=engine)
db_session = DB_Session()
Base = declarative_base()


def init_db():
    import models
    Base.metadata.create_all(bind=engine)


def drop_db():
    Base.metadata.drop_all(engine)


def initial_db():
    drop_db()
    init_db()


if __name__ == '__main__':
    init_db(engine)

