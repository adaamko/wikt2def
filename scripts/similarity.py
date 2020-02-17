import re
import json
import requests
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import spacy


def call_elmo_service(premise, hypothesis, language, port=1666):
    data = json.dumps({"sentences": [hypothesis, premise]})
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    r = requests.post("http://127.0.0.1:{}/{}".format(port, language), data=data, headers=headers)
    return [np.asarray(e) for e in r.json()["embeddings"]]


class Similarity(object):
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")

    def clear_node(self, node):
        return re.sub(r'_[0-9]*', '', node)

    def asim_jac_words(self, def_premise, def_hypothesis):
        prem = self.nlp(def_premise)
        hyp = self.nlp(def_hypothesis)

        filtered_prem = []
        for token in prem:
            if not token.is_stop:
                filtered_prem.append(token.lemma_)

        filtered_hyp = []
        for token in hyp:
            if not token.is_stop:
                filtered_hyp.append(token.lemma_)

        filtered_prem = set(filtered_prem)
        filtered_hyp = set(filtered_hyp)

        sim = filtered_hyp & filtered_prem
        if not sim or len(filtered_hyp) == 0:
            return 0
        else:
            return float(len(sim)) / len(filtered_hyp)

    def asim_jac_edges(self, graph_premise, graph_hypothesis):
        hyp = set([(self.clear_node(s), self.clear_node(r), e['color']) for (s, r, e) in graph_hypothesis.G.edges(data=True)])
        pre = set([(self.clear_node(s), self.clear_node(r), e['color']) for (s, r, e) in graph_premise.G.edges(data=True)])
        sim = hyp & pre
        if not sim or len(hyp) == 0:
            return 0
        else:
            return float(len(sim)) / len(hyp)

    def asim_jac_nodes(self, graph_hypothesis, graph_premise):
        hyp = set([self.clear_node(node) for node in graph_hypothesis.G.nodes])
        pre = set([self.clear_node(node) for node in graph_premise.G.nodes])
        sim = hyp & pre
        if not sim or len(hyp) == 0:
            return 0
        else:
            return float(len(sim)) / len(hyp)

    def asim_jac_nodes_elmo(self, premise, hypothesis, graph_premise, graph_hypothesis, def_premise, def_hypothesis,
                            lang):
        embeddings = call_elmo_service(": ".join([premise, def_premise]), ": ".join([hypothesis, def_hypothesis]), lang)

        premise_words = {w: s for (w, s) in zip([premise] + def_premise.split(' '), embeddings[0])}
        hypothesis_words = {w: s for (w, s) in zip([hypothesis] + def_hypothesis.split(' '), embeddings[0])}

        pre = set([premise_words[self.clear_node(node)] for node in graph_premise.G.nodes])
        hyp = set([hypothesis_words[self.clear_node(node)] for node in graph_hypothesis.G.nodes])
        similarities = cosine_similarity(pre, hyp)
        best_sim = [max(word_sim) for word_sim in np.transpose(similarities)]
        return sum(best_sim) / len(best_sim)

    def asim_jac_bow_elmo(self, def_premise, def_hypothesis, lang):
        embeddings = call_elmo_service(def_premise, def_hypothesis, lang)
        similarities = cosine_similarity(embeddings[0], embeddings[1])
        best_sim = [max(word_sim) for word_sim in np.transpose(similarities)]
        return sum(best_sim) / len(best_sim)


#print(asim_jac_bow_elmo("Ich mag Hünde", "Ich mag meinen Hund", "de"))

