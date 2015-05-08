#!/usr/bin/env python

import json

from natsort import versorted
import requests

packages = requests.get('http://cdnjs.com/packages.json').json()['packages']

data = {}

for p in packages:
    try:
        name = p['name']
        version = versorted([v['version'] for v in p['assets']])[-1]
        data[name] = version
    except:
        print "can't parse: ", name
        continue

json.dump(data, open('cdnjsdata.json', 'wb'))
