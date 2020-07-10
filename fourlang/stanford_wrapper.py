import logging
import re
import sys
import requests
import json
import networkx as nx
from .service.ud_parser import UdParser


class StanfordParser():

    def __init__(self, lang):
        #self.server = "http://127.0.0.1:" + str(port)
        self.parser = UdParser(lang)
        self.parse = {}

    def parse_text(self, text, word=None):
        deplist = ["acl:relcl", "aux", "aux:pass", "case", "cc", "cc:preconj", "compound", "compound:prt", "conj", "cop", "det", "det:predet", "discourse", "expl", "fixed", "flat",
                    "goeswith", "iobj" ",list", "mark", "nmod:npmod", "nmod:poss", "nmod:tmod", "nsubj:pass", "obl", "obl:tmod", "orphan", "parataxis", "punct", "reparandum", "vocative"]

        deps = self.parser.parse(text)
        #for i, prem in enumerate(deps[0]):
        #    if prem[0] in deplist:
        #        print("Sentence: " + text + "\t" + str(prem))

        corefs = []
        return deps["deps"], corefs, deps["doc"]

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
