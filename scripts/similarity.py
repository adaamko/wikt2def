import re
import spacy

class Similarity():
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
         
        sim = hyp & pre
        if not sim or len(hyp) == 0:
            return 0
        else:
            return float(len(sim)) / len(hyp)
        

    def asim_jac_edges(self, graph_hypothesis, graph_premise):
        hyp = set([(clear_node(s), clear_node(r), e['color']) for (s, r, e) in graph_hypothesis.G.edges(data=True)])
        pre = set([(clear_node(s), clear_node(r), e['color']) for (s, r, e) in graph_premise.G.edges(data=True)])
        sim = hyp & pre
        if not sim or len(hyp) == 0:
            return 0
        else:
            return float(len(sim)) / len(hyp)


    def asim_jac_nodes(self, graph_hypothesis, graph_premise):
        hyp = set([clear_node(node) for node in graph_hypothesis.G.nodes])
        pre = set([clear_node(node) for node in graph_premise.G.nodes])
        sim = hyp & pre
        if not sim or len(hyp) == 0:
            return 0
        else:
            return float(len(sim)) / len(hyp)
