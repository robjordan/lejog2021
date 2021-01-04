# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START gae_python38_app]
# [START gae_python3_app]
import json
from flask import Flask, request, jsonify, render_template
# import bisect
from google.cloud import datastore
from flask_cors import CORS


# If `entrypoint` is not defined in app.yaml, App Engine will look for an app
# called `app` in `main.py`.
app = Flask(__name__)
CORS(app)


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route('/')
def hello():
    """Return a page."""
    return render_template('index.html')


@app.route('/update', methods=['POST'])
def update_records():
    update = json.loads(request.data)
    print(update)
    datastore_client = datastore.Client()

    # map mileage to location
    millimiles = int(round(float(update['mileage']), 1) * 1000)
    mileage_key = datastore_client.key('Progress', str(millimiles))
    point = datastore_client.get(mileage_key)
    if point is None:
        raise InvalidUsage(
            'Mileage out of range' + update['mileage'],
            status_code=410)

    # the request should contain name, date, mileage
    name_key = datastore_client.key('Walkers', update['name'])
    walker = datastore_client.get(name_key)

    if walker is None:
        # first time entry for this walker
        walker = datastore.Entity(key=name_key)

    # update an existing walker
    walker['latest'] = point
    walker['latest']['mileage'] = update['mileage']
    walker['latest']['date'] = update['date']
    walker[update['date']] = point
    datastore_client.put(walker)

    return get_records()


@app.route('/latest', methods=['GET'])
def get_records():
    datastore_client = datastore.Client()
    query = datastore_client.query(kind="Walkers")
    full_list = list(query.fetch())
    # sift out all the dated entries to leave only the latest
    results = []
    for walker in full_list:
        results.append(
            {
                "name": walker.key.name,
                "point": walker['latest']['point'],
                "mileage": walker['latest']['mileage'],
                "date": walker['latest']['date']
            }
        )
    response = jsonify(results)
    return response


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END gae_python3_app]
# [END gae_python38_app]
