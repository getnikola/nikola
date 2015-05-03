#!/usr/bin/env python

import json
import subprocess

links = {}
data = subprocess.check_output(['links', '-dump', 'https://cdnjs.com/'])
for l in data.splitlines():
    l = l.strip()
    if not 'https' in l:
        continue
    name, url = [x.strip() for x in l.split('https:')]
    links[name] = url
    
json.dump(links,open('cdnjsdata.json', 'w'))

