import re
import json
import os
import requests
import numpy as np
import copy
from sklearn.metrics.pairwise import cosine_similarity
import spacy
from collections import defaultdict
from networkx import algorithms
from fourlang.stanford_wrapper import StanfordParser
from fourlang.fourlang import FourLang
from .parse_data import load_vec
from .utils import get_distance


class Similarity(object):
    def __init__(self, lang="en", with_embedding=True):
        self.lang = lang
        self.language_models = {"en": "en_core_web_sm", "it": "it_core_news_sm", "de": "de_core_news_sm"}
        self.cross_lingual_path = "/home/adaamko/data/DMR/"
        self.nlp = spacy.load(self.language_models[self.lang])
        self.stanford_parser = StanfordParser()
        self.fourlang_expressions = ["has", "at", "npmod"]
        if with_embedding:
            fourlang_embeddings = self.call_elmo_service(self.fourlang_expressions)
            self.fourlang_expression_embeddings = {expr: emb[0] for (expr, emb) in
                                                   zip(self.fourlang_expressions, fourlang_embeddings)}

    def clear_node(self, node):
        """
        Clears the node from the 4lang id parts
        :param node: the text to clear
        :return: the cleared text
        """
        return re.sub(r'_[0-9][0-9]*', '', node)

    def init_cross_lingual_embeddings(self, src_lang, tgt_lang):
        """
        Initialize cross-lingual embeddings
        :param src_lang: the language of the premise
        :param tgt_lang: the language of the hypothesis
        :return: None
        """
        src_path = '/home/adaamko/data/DMR/wiki.multi.' + src_lang + '.vec'
        tgt_path = '/home/adaamko/data/DMR/wiki.multi.' + tgt_lang + '.vec'
        nmax = 250000  # maximum number of word embeddings to load

        self.src_embeddings, self.src_id2word, self.src_word2id = load_vec(src_path, nmax)
        self.tgt_embeddings, self.tgt_id2word, self.tgt_word2id = load_vec(tgt_path, nmax)

        self.src_word2id = {v: k for k, v in self.src_id2word.items()}
        self.tgt_word2id = {v: k for k, v in self.tgt_id2word.items()}
        self.nlp_src_lang = spacy.load(self.language_models[src_lang])
        self.nlp_tgt_lang = spacy.load(self.language_models[tgt_lang])

    def init_dictionaries(self, src_lang, tgt_lang):
        """
        Initialize dictionaries
        :param src_lang: the language of the premise
        :param tgt_lang: the language of the hypothesis
        :return: None
        """
        path = "../dictionaries/" + src_lang + "_dictionary"
        dictionary_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)

        dictionary = defaultdict(list)
        with open(dictionary_path, "r+") as f:
            for line in f:
                line = line.strip().split("\t")
                if line[0] == src_lang and line[2] == tgt_lang:
                    dictionary[line[1].lower()].append(line[3].lower())

        self.nlp_src_lang = spacy.load(self.language_models[src_lang])
        self.nlp_tgt_lang = spacy.load(self.language_models[tgt_lang])
        self.dictionary = dictionary

    def call_elmo_service(self, sentences, port=1666):
        """
        Calls the already running elmo service
        :param sentences: the sentences we want to get the embeddings for
        :param port: the port of the service
        :return: list of embeddings
        """
        data = json.dumps({"sentences": sentences})
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        r = requests.post("http://127.0.0.1:{}/{}".format(port, self.lang), data=data, headers=headers)
        return [np.asarray(e) for e in r.json()["embeddings"]]

    def get_elmo_embeddings(self, premise, hypothesis, port=1666):
        """
        Calls the call_elmo_service with the parameters
        :param premise: the premise sentence
        :param hypothesis: the hypothesis sentence
        :param port: the port of the service
        :return: list of embeddings
        """
        return self.call_elmo_service([premise, hypothesis], port=port)

    def get_embedding_dictionary(self, token_lemmas, embeddings, first_word):
        """
        Gets the dictionary of the lemmas and the corresponding embeddings baseg on existing lemmas and embeddings
        :param token_lemmas: the lemmas in the sentence
        :param embeddings: the embedding of the sentence
        :param first_word: the first (not lemmatized) word of the sentence
        :return: the dictionary of the lemma-to-token relations
        """
        word_dict = self.fourlang_expression_embeddings.copy()
        word_dict[first_word] = embeddings[0]
        for (words, embedding) in zip(token_lemmas, embeddings):
            for w in words:
                word_dict[w] = embedding
        return word_dict

    def get_elmo_nodes(self, premise, def_premise, hypothesis, def_hypothesis):
        """
        Gets the dictionary of the lemmas and the corresponding embeggings for the premise and hypothesis
        :param premise: the premise word
        :param def_premise: the definition of the premise
        :param hypothesis: the hypothesis word
        :param def_hypothesis: the definition of the hypothesis
        :return: the embedding dictionary of the premise and hypothesis
        """
        premise_token_lemmas, premise_token_words = self.stanford_parser.lemmatize_text(": ".join([premise, def_premise]))
        hypothesis_token_lemmas, hypothesis_token_words = self.stanford_parser.lemmatize_text(": ".join([hypothesis, def_hypothesis]))

        premise_full_def = " ".join(premise_token_words)
        hypothesis_full_def = " ".join(hypothesis_token_words)

        embeddings = self.get_elmo_embeddings(premise_full_def, hypothesis_full_def)

        premise_words = self.get_embedding_dictionary(premise_token_lemmas, embeddings[0], premise)
        hypothesis_words = self.get_embedding_dictionary(hypothesis_token_lemmas, embeddings[1], hypothesis)
        return premise_words, hypothesis_words

    def get_elmo_edges(self, graph, words):
        """
        Create the list of edges containing the triplet of the two node embedding and the edge type
        :param graph: the graph of the definition
        :param words: the dictionary of pre-generated embeddings
        :return: the list of edges
        """
        edges = []
        for (source, receiver, edge) in graph.G.edges(data=True):
            cleared_source = self.clear_node(source)
            cleared_receiver = self.clear_node(receiver)
            if cleared_source not in words:
                print([k for k in words.keys()])
                print([self.clear_node(k) for k in graph.G.nodes])
                s = self.call_elmo_service([cleared_source])[0][0]
            else:
                s = words[cleared_source]
            if cleared_receiver not in words:
                print([k for k in words.keys()])
                print([self.clear_node(k) for k in graph.G.nodes])
                r = self.call_elmo_service([cleared_receiver])[0][0]
            else:
                r = words[cleared_receiver]
            edges.append((s, r, edge['color']))
        return edges

    def cross_lingual_dictionary_bag(self, def_premise, def_hypothesis, premise_src=True):
        """
        Cross-lingual bag of words approach
        :param def_premise: the definition of the premise
        :param def_hypothesis: the definition of the hypothesis
        :param premise_src: whether or not to keep the ordering of the premise and hypothesis
        :return: the best score
        """
        if premise_src:
            prem =  self.nlp_src_lang(def_premise)
            hyp = self.nlp_tgt_lang(def_hypothesis)
        else:
            hyp =  self.nlp_src_lang(def_premise)
            prem = self.nlp_tgt_lang(def_hypothesis)    

        filtered_prem = []
        for token in prem:
            if not token.is_stop and not token.is_punct:
                filtered_prem.append(token.lemma_)

        filtered_hyp = []
        for token in hyp:
            if not token.is_stop and not token.is_punct:
                filtered_hyp.append(token.lemma_)
                
        dic_elements = []
        for word in filtered_prem:        
            if not self.dictionary[word]:
                dic_elements.append(word)
            for el in self.dictionary[word]:
                dic_elements.append(el)

        filtered_prem = set(dic_elements)
        filtered_hyp = set(filtered_hyp)

        sim = filtered_hyp & filtered_prem
        if not sim or len(filtered_hyp) == 0:
            return 0
        else:
            return float(len(sim)) / len(filtered_hyp)

    def cross_lingual_dictionary_4lang(self, graph_premise, graph_hypothesis, premise_src=True):
        """
        Asymmetric Jaccard similarity between the lowercase nodes of the definition graphs
        :param graph_premise: the definition graph of the premise
        :param graph_hypothesis: the definition graph of the hypothesis
        :param premise_src: whether or not to keep the ordering of the premise and hypothesis
        :return: the score
        """
        if premise_src:
            prem = set([self.clear_node(node).lower() for node in graph_premise.G.nodes])
            hyp = set([self.clear_node(node).lower() for node in graph_hypothesis.G.nodes])
        else:
            hyp = set([self.clear_node(node).lower() for node in graph_premise.G.nodes])
            prem = set([self.clear_node(node).lower() for node in graph_hypothesis.G.nodes])  

        dic_elements = []
        for word in prem:        
            if not self.dictionary[word]:
                dic_elements.append(word)
            for el in self.dictionary[word]:
                dic_elements.append(el)

        filtered_prem = set(dic_elements)
        filtered_hyp = set(hyp)

        sim = filtered_hyp & filtered_prem
        if not sim or len(filtered_hyp) == 0:
            return 0
        else:
            return float(len(sim)) / len(filtered_hyp)
        
    def muse_min_distance_4lang(self, graph_premise, graph_hypothesis, premise_src=True):
        """
        Asymmetric cross-lingual Jaccard similarity between the nodes of the definition graphs
        :param graph_premise: the definition graph of the premise
        :param graph_hypothesis: the definition graph of the hypothesis
        :param premise_src: whether or not to keep the ordering of the premise and hypothesis
        :return: the score
        """
        if premise_src:
            prem = set([self.clear_node(node).lower() for node in graph_premise.G.nodes])
            hyp = set([self.clear_node(node).lower() for node in graph_hypothesis.G.nodes])
        else:
            hyp = set([self.clear_node(node).lower() for node in graph_premise.G.nodes])
            prem = set([self.clear_node(node).lower() for node in graph_hypothesis.G.nodes])    
        
        max_score = 0
        for prem_word in prem:
            for hyp_word in hyp:
                try:
                    distance = get_distance(prem_word, hyp_word, self.src_embeddings, self.tgt_embeddings, self.src_word2id, self.tgt_word2id)
                except KeyError:
                    distance = 0
                if distance > max_score:
                    max_score = distance
        return max_score

    def compute_min_distance_scores(self, def_premise, def_hypothesis, premise_src=True):
        """
        Compute the cross-lingual minimum distance between words of the definition sentences
        :param def_premise: the definition of the premise
        :param def_hypothesis: the definition of the hypothesis
        :param premise_src: whether or not to keep the ordering of the premise and hypothesis
        :return: the best achievable score
        """
        if premise_src:
            prem =  self.nlp_src_lang(def_premise)
            hyp = self.nlp_tgt_lang(def_hypothesis)
        else:
            hyp =  self.nlp_src_lang(def_premise)
            prem = self.nlp_tgt_lang(def_hypothesis)

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
                    distance = get_distance(prem_word, hyp_word, self.src_embeddings, self.tgt_embeddings, self.src_word2id, self.tgt_word2id)
                except KeyError:
                    distance = 0
                if distance > max_score:
                    max_score = distance
        return max_score

    def asim_jac_words(self, def_premise, def_hypothesis):
        """
        Asymmetric Jaccard similarity between the words of the definitions
        :param def_premise: the definition of the premise
        :param def_hypothesis: the definition of the hypothesis
        :return: the ratio of overlap per the length of the hypothesis definition
        """
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
        """
        Asymmetric Jaccard similarity between the edges of the definition graphs
        :param graph_premise: the definition graph of the premise
        :param graph_hypothesis: the definition graph of the hypothesis
        :return: the ratio of overlapping edges per the length of the hypothesis definition
        """
        prem = set([(self.clear_node(s), self.clear_node(r), e['color']) for (s, r, e) in graph_premise.G.edges(data=True)])
        hyp = [(self.clear_node(s), self.clear_node(r), e['color']) for (s, r, e) in graph_hypothesis.G.edges(data=True)]
        hyp_cleared = []
        for triplet in hyp:
            if triplet[0] != "A" and triplet[0] != "B" and triplet[1] != "A" and triplet[1] != "B":
                hyp_cleared.append(triplet)
        hyp = set(hyp_cleared)
        sim = hyp & prem
        if not sim or len(hyp) == 0:
            return 0
        return len(sim)/len(hyp)

    def multi_def_best_match(self, graph_premises, graph_hypothesises, similarity_function, return_graphs=False):
        """
        Find the best matching premise and hypothesis
        :param graph_premises: the definition graph of the premise
        :param graph_hypothesises: the definition graph of the hypothesis
        :param similarity_function: the similarity function to use
        :param return_graphs: whether to return the graphs
        :return: the score and the best graph pair
        """
        if len(graph_premises) > 0 and len(graph_hypothesises) > 0:
            best_pair = (graph_premises[0], graph_hypothesises[0])
            best_match = 0
            for graph_premise in graph_premises:
                for graph_hypothesis in graph_hypothesises:
                    match = similarity_function(graph_premise, graph_hypothesis)
                    if match > best_match:
                        best_match = match
                        best_pair = (graph_premise, graph_hypothesis)
                    if best_match == 1.0:
                        break
                if best_match == 1.0:
                    break
            if return_graphs:
                return best_match, best_pair
            return best_match
        elif return_graphs:
            if len(graph_premises) > 0:
                return 0, (graph_premises[0], FourLang())
            elif len(graph_hypothesises) > 0:
                return 0, (FourLang(), graph_hypothesises[0])
            else:
                return 0, (FourLang(), FourLang())
        return 0

    def asim_jac_nodes(self, graph_premise, graph_hypothesis):
        """
        Asymmetric Jaccard similarity between the nodes of the definition graphs
        :param graph_premise: the definition graph of the premise
        :param graph_hypothesis: the definition graph of the hypothesis
        :return: the ratio of overlapping nodes per the length of the hypothesis definition
        """
        prem = set([self.clear_node(node) for node in graph_premise.G.nodes])
        hyp = set([self.clear_node(node) for node in graph_hypothesis.G.nodes])
        sim = hyp & prem
        if not sim or len(hyp) == 0:
            return 0
        return len(sim)/len(hyp)

    def asim_jac_nodes_graded(self, graph_premise, graph_hypothesis):
        """
        Asymmetric Jaccard similarity between the nodes of the definition graphs
        :param graph_premise: the definition graph of the premise
        :param graph_hypothesis: the definition graph of the hypothesis
        :return: the ratio of overlapping nodes per the length of the hypothesis definition
        """
        prem = [(node, self.clear_node(node)) for node in graph_premise.G.nodes]
        hyp = [(node, self.clear_node(node)) for node in graph_hypothesis.G.nodes]
        sim = 0
        for hyp_node in hyp:
            if hyp_node[1] in [p[1] for p in prem]:
                try:
                    shortest_path = algorithms.shortest_path(graph_premise.G, graph_premise.root, prem[[p[1] for p in prem].index(hyp_node[1])][0])
                    print("ok")
                    hypothesis_path = algorithms.shortest_path(graph_hypothesis.G, graph_hypothesis.root, hyp_node[0])
                    if shortest_path in [0, 1]:
                        sim += max(hypothesis_path, 2)
                    elif hypothesis_path == 0:
                        sim += 1
                    else:
                        sim += hypothesis_path / (shortest_path - 1)
                except Exception as e:
                    sim += 0.5
        if sim == 0 or len(hyp) == 0:
            print(sim)
            return 0
        else:
            return float(sim) / float(len(hyp))

    def asim_jac_nodes_with_backup(self, graph_premise, graph_hypothesis):
        """
        Asymmetric Jaccard similarity between the nodes of the definition graphs, if the score is not 1 it calculates
        the asymmetric Jaccard similarity between the edges without the hypothesis root node
        :param graph_premise: the definition graph of the premise
        :param graph_hypothesis: the definition graph of the hypothesis
        :return: the ratio of overlapping nodes per the length of the hypothesis definition
        """
        node_score = self.asim_jac_nodes(graph_premise, graph_hypothesis)
        edge_score = 0
        if 0.0 < node_score < 1.0:
            root = graph_hypothesis.d_clean(graph_hypothesis.root).split("_")[0]
            if root in graph_premise.get_nodes():
                root_id = [node for node in graph_premise.G.nodes() if self.clear_node(node) == root][0]
                graph_premise_only_zero = copy.deepcopy(graph_premise)

                delete_list = []

                for edge in graph_premise_only_zero.G.adj.items():
                    for output_node in edge[1].items():
                        inner_delete_list = []
                        for edge_type in output_node[1].items():
                            if edge_type[1]["color"]:
                                inner_delete_list.append(edge_type[0])
                        for inner_del in inner_delete_list:
                            del output_node[1]._atlas[inner_del]
                        if len(output_node[1]) < 1:
                            delete_list.append(output_node[0])
                    for to_del in delete_list:
                        if to_del in edge[1]._atlas:
                            del edge[1]._atlas[to_del]
                try:
                    if algorithms.has_path(graph_premise_only_zero.G, graph_premise.root, root_id):
                        return 1.0
                except Exception as e:
                    print("Error occured:", e)
            graph_hypothesis_wo_root = copy.deepcopy(graph_hypothesis)
            graph_hypothesis_wo_root.G.remove_node(graph_hypothesis_wo_root.root)
            #edge_score = self.asim_jac_edges(graph_premise, graph_hypothesis_wo_root)
            return self.asim_jac_edges(graph_premise, graph_hypothesis_wo_root)
        #return max([node_score, edge_score])
        return node_score

    def asim_jac_nodes_elmo(self, premise, hypothesis, graph_premise, graph_hypothesis, def_premise, def_hypothesis):
        """
        Asymmetric Jaccard similarity between the node embeddings of the definition graphs
        :param premise: the premise word
        :param hypothesis: the hypothesis word
        :param graph_premise: the definition graph of the premise
        :param graph_hypothesis: the definition graph of the hypothesis
        :param def_premise: the definition of the premise
        :param def_hypothesis: the definition of the hypothesis
        :return: the ratio of best node matches per the length of the hypothesis definition
        """
        premise_words, hypothesis_words = self.get_elmo_nodes(premise, def_premise, hypothesis, def_hypothesis)

        prem = []
        for node in graph_premise.G.nodes:
            cleared_node = self.clear_node(node)
            if cleared_node not in premise_words:
                prem.append(self.call_elmo_service([cleared_node])[0][0])
            else:
                prem.append(premise_words[cleared_node])
        hyp = []
        for node in graph_hypothesis.G.nodes:
            cleared_node = self.clear_node(node)
            if cleared_node not in hypothesis_words:
                hyp.append(self.call_elmo_service([cleared_node])[0][0])
            else:
                hyp.append(hypothesis_words[cleared_node])
        similarities = cosine_similarity(prem, hyp)
        best_sim = [max(word_sim) for word_sim in np.transpose(similarities)]
        return sum(best_sim) / len(best_sim)

    def asim_jac_edges_elmo(self, premise, hypothesis, graph_premise, graph_hypothesis, def_premise, def_hypothesis):
        """
        Asymmetric Jaccard similarity between the edges based on the node embeddings of the definition graphs
        :param premise: the premise word
        :param hypothesis: the hypothesis word
        :param graph_premise: the definition graph of the premise
        :param graph_hypothesis: the definition graph of the hypothesis
        :param def_premise: the definition of the premise
        :param def_hypothesis: the definition of the hypothesis
        :return: the ratio of best edge matches per the length of the hypothesis definition
        """
        premise_words, hypothesis_words = self.get_elmo_nodes(premise, def_premise, hypothesis, def_hypothesis)

        prem = self.get_elmo_edges(graph_premise, premise_words)
        hyp = self.get_elmo_edges(graph_hypothesis, hypothesis_words)
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
        """
        Asymmetric Jaccard similarity between the word embeddings of the definitions
        :param def_premise: the definition of the premise
        :param def_hypothesis: the definition of the hypothesis
        :return: the ratio of overlap per the length of the hypothesis definition
        """
        embeddings = self.get_elmo_embeddings(def_premise, def_hypothesis)
        similarities = cosine_similarity(embeddings[0], embeddings[1])
        best_sim = [max(word_sim) for word_sim in np.transpose(similarities)]
        return sum(best_sim) / len(best_sim)

    def word_elmo(self, premise, hypothesis):
        """
        The cosine similarity of the words
        :param premise: the premise word
        :param hypothesis: the hypothesis word
        :return: the cosine similarity score
        """
        embeddings = self.get_elmo_embeddings(premise, hypothesis)
        similarity = cosine_similarity(embeddings[0], embeddings[1])[0][0]
        return similarity
