import logging
import re
import sys
import requests
import json


class StanfordParser():
    
    def __init__(self, port=5005):
        self.server = "http://127.0.0.1:" + str(port)
        
    def parse_text(self, text):
        data = {'text': text}
        data_json = json.dumps(data)
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        r = requests.post(self.server + "/parse", data=data_json, headers=headers)

        deps = r.json()["deps"]
        corefs = []
        return deps, corefs

    def lemmatize_text(self, text):
        data = {'text': text}
        data_json = json.dumps(data)
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        r = requests.post(self.server + "/lemmatize", data=data_json, headers=headers)

        lemmas = r.json()["lemmas"]
        return lemmas
