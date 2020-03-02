import logging
import re
import sys
import requests
import json
import networkx as nx


class StanfordParser():
    
    def __init__(self, port=5005):
        self.server = "http://127.0.0.1:" + str(port)
        self.parse = {}
        
    def parse_text(self, text, word=None):
        if word and word in self.parse:
            deps = self.parse[word]
        else:
            data = {'text': text}
            data_json = json.dumps(data)
            headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
            r = requests.post(self.server + "/parse", data=data_json, headers=headers)

            deps = r.json()["deps"]
            if word:
                self.parse[word] = deps

        corefs = []
        return deps, corefs

    def load_from_dict(self):
        with open("def_parses", "r") as f:
            self.parse = json.load(f)

    def save_dict(self):
        with open("def_parses", "w+") as f:
            dict_json = json.dumps(self.parse)
            f.write(dict_json)

    def lemmatize_text(self, text):
        data = {'text': text}
        data_json = json.dumps(data)
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        r = requests.post(self.server + "/lemmatize", data=data_json, headers=headers)

        r_json = r.json()
        lemmas = r_json["lemmas"]
        words = r_json["words"]
        return lemmas, words

    def lemmatize_word(self, word):
        data = {'word': word}
        data_json = json.dumps(data)
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        r = requests.post(self.server + "/lemmatize_word", data=data_json, headers=headers)
        return r.json()["lemma"]
