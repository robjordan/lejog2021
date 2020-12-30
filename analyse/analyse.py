import gpxpy
import gpxpy.gpx
import bisect
import json
import sys


gpx_file = open('merged.gpx', 'r')

gpx = gpxpy.parse(gpx_file)

prev_point = None
track_len = 0.0
distances = []
points = []
FACTOR = (0.621372*1787.981/1843.370)

for track in gpx.tracks:
    for segment in track.segments:
        for point in segment.points:
            if prev_point:
                delta = FACTOR * point.distance_2d(prev_point) / 1000.0
                track_len = track_len + delta
                distances.append(track_len)
                points.append((track_len, point.latitude, point.longitude))

            prev_point = point

print("total track length: ", track_len, "miles")
print("mem(distances):", sys.getsizeof(distances))
print("mem(points):", sys.getsizeof(points))

with open('points.json', 'w') as f:
    json.dump(points, f)

for d in range(100, 1111, 100):
    i = bisect.bisect_right(distances, d)
    print("mile: {0}, distance: {1}, next point: {2}".format(
        d, distances[i], points[i]))

print("interpolated positions")
for d in range(100, 1111, 100):
    i = bisect.bisect_right(distances, d)
    if i > 0:
        d1 = distances[i-1]
        d2 = distances[i]
        p1 = points[i-1]
        p2 = points[i]
        print("miles: {}, adjacent p1: {}, p2: {}".format(d, p1, p2))
        f = (d - d1) / (d2 - d1)
        lat = (1 - f) * p1[1] + f * p2[1]
        lon = (1 - f) * p1[2] + f * p2[2]
        print("interpolated point: {}".format((lat, lon)))
