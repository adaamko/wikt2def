import logging
import re
import sys
import requests
import json
import networkx as nx
from .service.ud_parser import UdParser


class StanfordParser():

    def __init__(self, lang, serverless=True, port=5005):
        self.server = "http://127.0.0.1:" + str(port)

        self.serverless = serverless
        if serverless:
            self.parser = UdParser(lang)
        self.parse = {}

    def parse_text(self, text, word=None):
        deplist = ["acl:relcl", "aux", "aux:pass", "case", "cc", "cc:preconj", "compound", "compound:prt", "conj", "cop", "det", "det:predet", "discourse", "expl", "fixed", "flat",
                   "goeswith", "iobj" ",list", "mark", "nmod:npmod", "nmod:poss", "nmod:tmod", "nsubj:pass", "obl", "obl:tmod", "orphan", "parataxis", "punct", "reparandum", "vocative"]

        if not self.serverless:
            data = {'text': text}
            data_json = json.dumps(data)
            headers = {'Content-type': 'application/json',
                       'Accept': 'text/plain'}
            r = requests.post(self.server + "/parse",
                              data=data_json, headers=headers)
            deplist = ["acl:relcl", "aux", "aux:pass", "case", "cc", "cc:preconj", "compound", "compound:prt", "conj", "cop", "det", "det:predet", "discourse", "expl", "fixed", "flat",
                       "goeswith", "iobj" ",list", "mark", "nmod:npmod", "nmod:poss", "nmod:tmod", "nsubj:pass", "obl", "obl:tmod", "orphan", "parataxis", "punct", "reparandum", "vocative"]

            deps = r.json()["deps"]

        else:
            deps = self.parser.parse(text)

        corefs = []
        return deps["deps"], corefs, deps["doc"]

    def parse_text_for_irtg(self, text):
        return self.parser.parse_for_irtg(text)

    def load_from_dict(self):
        with open("def_parses", "r") as f:
            self.parse = json.load(f)

    def save_dict(self):
        with open("def_parses", "w+") as f:
            dict_json = json.dumps(self.parse)
            f.write(dict_json)

    def lemmatize_text(self, text):
        result = self.parser.lemmatize_text(text)
        lemmas = result["lemmas"]
        words = result["words"]
        return lemmas, words

    def lemmatize_word(self, word):
        lemma = self.parser.lemmatize_word(word)["lemma"]
        return lemma
