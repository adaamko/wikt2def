import re
import json
import requests
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import spacy
from fourlang.stanford_wrapper import StanfordParser


class Similarity(object):
    def __init__(self, lang="en"):
        self.lang = lang
        language_models = {"en": "en_core_web_sm", "it": "it_core_news_sm", "de": "de_core_news_sm"}
        self.nlp = spacy.load(language_models[self.lang])
        self.stanford_parser = StanfordParser()

    def clear_node(self, node):
        return re.sub(r'_[0-9]*', '', node)

    def call_elmo_service(self, premise, hypothesis, port=1666):
        data = json.dumps({"sentences": [premise, hypothesis]})
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        r = requests.post("http://127.0.0.1:{}/{}".format(port, self.lang), data=data, headers=headers)
        return [np.asarray(e) for e in r.json()["embeddings"]]

    def get_elmo_nodes(self, premise, def_premise, hypothesis, def_hypothesis):
        premise_full_def = ": ".join([premise, def_premise])
        hypothesis_full_def = ": ".join([hypothesis, def_hypothesis])
        embeddings = self.call_elmo_service(premise_full_def, hypothesis_full_def)

        premise_tokens = self.stanford_parser.lemmatize_text(premise_full_def)
        hypothesis_tokens = self.stanford_parser.lemmatize_text(hypothesis_full_def)

        premise_words = {w: s for (w, s) in zip(premise_tokens, embeddings[0])}
        hypothesis_words = {w: s for (w, s) in zip(hypothesis_tokens, embeddings[1])}
        return premise_words, hypothesis_words

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
        prem = set([(self.clear_node(s), self.clear_node(r), e['color']) for (s, r, e) in graph_premise.G.edges(data=True)])
        hyp = set([(self.clear_node(s), self.clear_node(r), e['color']) for (s, r, e) in graph_hypothesis.G.edges(data=True)])
        sim = hyp & prem
        if not sim or len(hyp) == 0:
            return 0
        else:
            return float(len(sim)) / len(hyp)

    def asim_jac_nodes(self, graph_hypothesis, graph_premise):
        prem = set([self.clear_node(node) for node in graph_premise.G.nodes])
        hyp = set([self.clear_node(node) for node in graph_hypothesis.G.nodes])
        sim = hyp & prem
        if not sim or len(hyp) == 0:
            return 0
        else:
            return float(len(sim)) / len(hyp)

    def asim_jac_nodes_elmo(self, premise, hypothesis, graph_premise, graph_hypothesis, def_premise, def_hypothesis):
        premise_words, hypothesis_words = self.get_elmo_nodes(premise, def_premise, hypothesis, def_hypothesis)

        prem = np.asarray([premise_words[self.clear_node(node)] for node in graph_premise.G.nodes])
        hyp = np.asarray([hypothesis_words[self.clear_node(node)] for node in graph_hypothesis.G.nodes])

        similarities = cosine_similarity(prem, hyp)
        best_sim = [max(word_sim) for word_sim in np.transpose(similarities)]
        return sum(best_sim) / len(best_sim)

    def asim_jac_edges_elmo(self, premise, hypothesis, graph_premise, graph_hypothesis, def_premise, def_hypothesis):
        premise_words, hypothesis_words = self.get_elmo_nodes(premise, def_premise, hypothesis, def_hypothesis)

        prem = [(premise_words[self.clear_node(s)], premise_words[self.clear_node(r)], e['color']) for
                          (s, r, e) in graph_premise.G.edges(data=True)]
        hyp = [(hypothesis_words[self.clear_node(s)], hypothesis_words[self.clear_node(r)], e['color']) for
                          (s, r, e) in graph_hypothesis.G.edges(data=True)]
        if len(hyp) == 0 or len(prem) == 0:
            return 0
        sim = 0
        for hyp_edge in hyp:
            scores = []
            for prem_edge in prem:
                if hyp_edge[2] == prem_edge[2]:
                    scores.append((cosine_similarity([np.asarray(hyp_edge[0])], [np.asarray(prem_edge[0])])[0] +
                                   cosine_similarity([np.asarray(hyp_edge[1])], [np.asarray(prem_edge[1])])[0]) / 2)
            sim += max(scores)
        return sum(sim) / len(hyp)

    def asim_jac_bow_elmo(self, def_premise, def_hypothesis):
        embeddings = self.call_elmo_service(def_premise, def_hypothesis)
        similarities = cosine_similarity(embeddings[0], embeddings[1])
        best_sim = [max(word_sim) for word_sim in np.transpose(similarities)]
        return sum(best_sim) / len(best_sim)
