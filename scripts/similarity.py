import re
import json
import requests
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import spacy
from fourlang.stanford_wrapper import StanfordParser
from .parse_data import load_vec
from .utils import get_distance

class Similarity(object):
    def __init__(self, lang="en"):
        self.lang = lang
        self.language_models = {"en": "en_core_web_sm", "it": "it_core_news_sm", "de": "de_core_news_sm"}
        self.cross_lingual_path = "/home/adaamko/data/DMR/"
        self.nlp = spacy.load(self.language_models[self.lang])
        self.stanford_parser = StanfordParser()
        self.fourlang_expressions = ["has", "at", "npmod"]
        fourlang_embeddings = self.call_elmo_service(self.fourlang_expressions)
        self.fourlang_expression_embeddings = {expr: emb[0] for (expr, emb) in
                                               zip(self.fourlang_expressions, fourlang_embeddings)}

    def clear_node(self, node):
        return re.sub(r'_[0-9]*', '', node)

    def init_cross_lingual_embeddings(self, src_lang, tgt_lang):
        src_path = '/home/adaamko/data/DMR/wiki.multi.' + src_lang + '.vec'
        tgt_path = '/home/adaamko/data/DMR/wiki.multi.' + tgt_lang + '.vec'
        nmax = 250000  # maximum number of word embeddings to load

        self.src_embeddings, self.src_id2word, self.src_word2id = load_vec(src_path, nmax)
        self.tgt_embeddings, self.tgt_id2word, self.tgt_word2id = load_vec(tgt_path, nmax)

        self.src_word2id = {v: k for k, v in self.src_id2word.items()}
        self.tgt_word2id = {v: k for k, v in self.tgt_id2word.items()}
        self.nlp_src_lang = spacy.load(self.language_models[src_lang])
        self.nlp_tgt_lang = spacy.load(self.language_models[tgt_lang])

    def call_elmo_service(self, sentences, port=1666):
        data = json.dumps({"sentences": sentences})
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        r = requests.post("http://127.0.0.1:{}/{}".format(port, self.lang), data=data, headers=headers)
        return [np.asarray(e) for e in r.json()["embeddings"]]

    def get_elmo_embeddings(self, premise, hypothesis, port=1666):
        return self.call_elmo_service([premise, hypothesis], port=port)

    def get_embedding_dictionary(self, token_lemmas, embeddings):
        word_dict = self.fourlang_expression_embeddings.copy()
        for (words, embedding) in zip(token_lemmas, embeddings):
            for w in words:
                word_dict[w] = embedding
        return word_dict

    def get_elmo_nodes(self, premise, def_premise, hypothesis, def_hypothesis):
        if len(def_premise) == 0:
            premise_token_lemmas, premise_token_words = [], []
        else:
            premise_token_lemmas, premise_token_words = self.stanford_parser.lemmatize_text(def_premise)
        if len(def_hypothesis) == 0:
            hypothesis_token_lemmas, hypothesis_token_words = [], []
        else:
            hypothesis_token_lemmas, hypothesis_token_words = self.stanford_parser.lemmatize_text(def_hypothesis)

        premise_full_def = " ".join([premise, ":"] + premise_token_words)
        hypothesis_full_def = " ".join([hypothesis, ":"] + hypothesis_token_words)

        embeddings = self.get_elmo_embeddings(premise_full_def, hypothesis_full_def)

        premise_words = self.get_embedding_dictionary([[premise], []] + premise_token_lemmas, embeddings[0])
        hypothesis_words = self.get_embedding_dictionary([[hypothesis], []] + hypothesis_token_lemmas, embeddings[1])
        return premise_words, hypothesis_words

    def compute_min_distance_scores(self, def_premise, def_hypothesis):
        prem =  self.nlp_src_lang(def_premise)
        hyp = self.nlp_tgt_lang(def_hypothesis)   

        filtered_prem = []
        for token in prem:
            if not token.is_stop and not token.is_punct:
                filtered_prem.append(token.lemma_)

        filtered_hyp = []
        for token in hyp:
            if not token.is_stop and not token.is_punct:
                filtered_hyp.append(token.lemma_)

        filtered_prem = set(filtered_prem)
        filtered_hyp = set(filtered_hyp)
        
        max_score = 0
        for prem_word in filtered_prem:
            for hyp_word in filtered_hyp:
                try:
                    distance = get_distance(prem_word, hyp_word, self.src_embeddings, self.tgt_embeddings)
                except KeyError:
                    distance = 0
                if distance > max_score:
                    max_score = distance
        return max_score

    def asim_jac_words(self, def_premise, def_hypothesis):
        prem = self.nlp(def_premise)
        hyp = self.nlp(def_hypothesis)

        filtered_prem = []
        for token in prem:
            if not token.is_stop and not token.is_punct:
                filtered_prem.append(token.lemma_)

        filtered_hyp = []
        for token in hyp:
            if not token.is_stop and not token.is_punct:
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

        try:
            prem = np.asarray([premise_words[self.clear_node(node)] for node in graph_premise.G.nodes])
        except Exception as e:
            print(premise)
            print(def_premise)
            print([k for k in premise_words.keys()])
            print([self.clear_node(k) for k in graph_premise.G.nodes])
            raise e
        try:
            hyp = np.asarray([hypothesis_words[self.clear_node(node)] for node in graph_hypothesis.G.nodes])
        except Exception as e:
            print(hypothesis)
            print(def_hypothesis)
            print([k for k in hypothesis_words.keys()])
            print([self.clear_node(k) for k in graph_hypothesis.G.nodes])
            raise e

        try:
            similarities = cosine_similarity(prem, hyp)
        except ValueError as e:
            raise e
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
            sim += max(scores + [0])
        return sum(sim) / len(hyp)

    def asim_jac_bow_elmo(self, def_premise, def_hypothesis):
        embeddings = self.get_elmo_embeddings(def_premise, def_hypothesis)
        similarities = cosine_similarity(embeddings[0], embeddings[1])
        best_sim = [max(word_sim) for word_sim in np.transpose(similarities)]
        return sum(best_sim) / len(best_sim)
