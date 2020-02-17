import re
import json
import requests
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def clear_node(node):
    return re.sub(r'_[0-9]*', '', node)


def asim_jac_edges(graph_premise, graph_hypothesis):
    hyp = set([(clear_node(s), clear_node(r), e['color']) for (s, r, e) in graph_hypothesis.G.edges(data=True)])
    pre = set([(clear_node(s), clear_node(r), e['color']) for (s, r, e) in graph_premise.G.edges(data=True)])
    sim = hyp & pre
    if not sim or len(hyp) == 0:
        return 0
    else:
        return float(len(sim)) / len(hyp)


def asim_jac_nodes(graph_premise, graph_hypothesis):
    hyp = set([clear_node(node) for node in graph_hypothesis.G.nodes])
    pre = set([clear_node(node) for node in graph_premise.G.nodes])
    sim = hyp & pre
    if not sim or len(hyp) == 0:
        return 0
    else:
        return float(len(sim)) / len(hyp)


def call_elmo_service(premise, hypothesis, language, port=1666):
    data = json.dumps({"sentences": [hypothesis, premise]})
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    r = requests.post("http://127.0.0.1:{}/{}".format(port, language), data=data, headers=headers)
    return [np.asarray(e) for e in r.json()["embeddings"]]


def asim_jac_nodes_elmo(premise, hypothesis, graph_premise, graph_hypothesis, def_premise, def_hypothesis, lang):
    print(": ".join([premise, def_premise]), ": ".join([hypothesis, def_hypothesis]))
    embeddings = call_elmo_service(": ".join([premise, def_premise]), ": ".join([hypothesis, def_hypothesis]), lang)
    premise_words = {w: s for (w, s) in zip([premise] + def_premise.split(' '), embeddings[0])}
    hypothesis_words = {w: s for (w, s) in zip([hypothesis] + def_hypothesis.split(' '), embeddings[0])}
    pre = set([premise_words[clear_node(node)] for node in graph_premise.G.nodes])
    hyp = set([hypothesis_words[clear_node(node)] for node in graph_hypothesis.G.nodes])
    similarities = cosine_similarity(pre, hyp)
    best_sim = [max(word_sim) for word_sim in np.transpose(similarities)]
    return sum(best_sim) / len(best_sim)


def asim_jac_bow_elmo(def_premise, def_hypothesis, lang):
    embeddings = call_elmo_service(def_premise, def_hypothesis, lang)
    similarities = cosine_similarity(embeddings[0], embeddings[1])
    best_sim = [max(word_sim) for word_sim in np.transpose(similarities)]
    return sum(best_sim) / len(best_sim)


#print(asim_jac_bow_elmo("Ich mag Hünde", "Ich mag meinen Hund", "de"))
