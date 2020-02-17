import logging
import re
import sys
import requests
import json


class StanfordParser():
    
    def __init__(self, port=5005):
        self.server = "http://127.0.0.1:" + str(port) + "/parse"
        
    def parse_text(self, text):
        data = {'text':   text}
        data_json = json.dumps(data)
        payload = {'json_payload': data_json}
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        r = requests.post(self.server, data=data_json, headers=headers)

        deps = r.json()["deps"]
        corefs = []
        return deps, corefs
