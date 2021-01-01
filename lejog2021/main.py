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


# If `entrypoint` is not defined in app.yaml, App Engine will look for an app
# called `app` in `main.py`.
app = Flask(__name__)


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


# INITIALISATION METHOD ONLY USED TO PRE-LOAD DATASTORE
# distances = []
# points = []


# def distance_to_point(d):
#     global distances
#     global points
#     i = bisect.bisect_right(distances, d)
#     if i == 0:
#         point = [50.066277, -5.714242]
#     elif i == len(distances):
#         point = [58.6439, -3.02604]
#     else:
#         d1 = distances[i-1]
#         d2 = distances[i]
#         p1 = points[i-1]
#         p2 = points[i]
#         f = (d - d1) / (d2 - d1)
#         lat = (1 - f) * p1[0] + f * p2[0]
#         lon = (1 - f) * p1[1] + f * p2[1]
#         point = [lat, lon]
#     return point


@app.route('/')
def hello():
    """Return a page."""
    return render_template('index.html')


# INITIALISATION METHOD ONLY USED TO PRE-LOAD DATASTORE
# @app.route('/init')
# def init_datastore():

#     global distances
#     global points
#     with open('static/js/progress.json', 'r') as file:
#         progress = json.load(file)
#         distances = [p[0] for p in progress]
#         points = [(p[1], p[2]) for p in progress]

#     datastore_client = datastore.Client()
#     print(datastore_client)
#     for d in range(519600, 1111100, 100):
#         p = distance_to_point(d)

#         # One-time load datastore with look-up from distance to location
#         key = datastore_client.key('Progress', str(d))
#         entry = datastore.Entity(key=key, exclude_from_indexes=('point',))
#         entry.update({'point': p})
#         print(entry)
#         datastore_client.put(entry)
#         print("put done")

#     return render_template('index.html')


@app.route('/points', methods=['POST'])
def update_records():
    update = json.loads(request.data)
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
    walker[update['date']] = point
    walker['latest'] = point
    datastore_client.put(walker)

    return jsonify(walker)


@app.route('/points', methods=['GET'])
def get_records():
    return True


if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [END gae_python3_app]
# [END gae_python38_app]
