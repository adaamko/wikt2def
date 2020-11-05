import copy
import json
import logging
import os
import pickle
import re
from collections import defaultdict
from statistics import mean
from fourlang.fourlang import FourLang

import networkx as nx
from networkx import algorithms
from nltk.corpus import stopwords as nltk_stopwords
from nltk.corpus import wordnet as wn


def nx_to_ud(graph):
    ud_list = []
    edges = [edge for edge in graph.edges(data=True)]
    for in_node, out_node, t in edges:
        in_node_split = in_node.split("_")
        if len(in_node_split) > 2:
            in_node_split = ["_".join(in_node_split[:-1]), in_node_split[-1]]
        out_node_split = out_node.split("_")
        if len(out_node_split) > 2:
            out_node_split = [
                "_".join(out_node_split[:-1]), out_node_split[-1]]
        ud_list.append([t["color"], in_node_split, out_node_split])

    return [ud_list]


def ud_to_nx(ud):
    G = nx.MultiDiGraph()
    nodes = set()
    iter_ud = ud if len(ud[0]) < 3 else [ud[0]]
    #iter_ud = [ud[0]]
    for dep in iter_ud:
        for dependency in dep:
            t = dependency[0]
            sender = "_".join([str(i) for i in dependency[1]])
            receiver = "_".join([str(i) for i in dependency[2]])
            if sender not in nodes:
                G.add_node(sender)
                nodes.add(sender)
            if receiver not in nodes:
                G.add_node(receiver)
                nodes.add(receiver)
            G.add_edge(sender, receiver, color=t)
    return G


def filter_ud(graph, blacklist):
    not_words = ["no", "not", "nicht", "kein"]
    edges = [edge for edge in graph.edges(data=True)]
    cond_nodes = []
    for in_node, out_node, t in edges:
        if t["color"] == "case" and out_node.split("_")[0] in blacklist:
            for in_, out_, t_ in edges:
                if t_["color"] == "nmod" and (in_ == in_node or out_ == in_node):
                    cond_nodes.append(in_node)
        if in_node.split("_")[0] in not_words or out_node.split("_")[0] in not_words:
            cond_nodes.append(in_node)

    to_delete = []

    for cond_node in cond_nodes:
        for node in graph.nodes():
            if cond_node in graph and node in graph:
                if algorithms.has_path(graph, cond_node, node):
                    to_delete.append(node)

    for node in to_delete:
        if node in graph.nodes(default=None):
            graph.remove_node(node)


def filter_graph(deps, blacklist):
    ud_G = ud_to_nx(deps)
    filter_ud(ud_G, blacklist)
    return nx_to_ud(ud_G)


class Lexicon:

    def __init__(self, lang):
        self.lexicon = {}
        self.synset_lexicon = defaultdict(lambda: defaultdict(list))
        self.wiktionary_synonyms = defaultdict(list)
        self.lexicon_list = {}
        self.lang_map = {}
        base_fn = os.path.dirname(os.path.abspath(__file__))
        langnames_fn = os.path.join(base_fn, "langnames")
        definitions_fn = os.path.join(base_fn, "definitions", lang)
        longman_fn = os.path.join(
            base_fn, "definitions", "longman_firsts.json")

        self.fourlang_definitions = set()
        with open(os.path.join(base_fn, "1383"), "r") as f:
            for line in f:
                line = line.split("\t")[0]
                self.fourlang_definitions.add(line)

        if os.path.exists(os.path.join("synonyms", lang)):
            synonyms_fn = os.path.join(base_fn, "synonyms", lang)
            with open(synonyms_fn) as f:
                for line in f:
                    line = line.split("\t")
                    if line[0] not in self.wiktionary_synonyms:
                        self.wiktionary_synonyms[line[0]] = []
                    self.wiktionary_synonyms[line[0].strip()].append(
                        line[1].strip("\n"))

        self.expanded = {}
        self.expanded_with_every_def = defaultdict(list)
        self.reduced = {}

        self.freq_words = {}
        freq_fn = os.path.join(base_fn, "umbc_webbase.unigram_freq.min50")
        if os.path.exists(freq_fn):
            with open(freq_fn, "r+") as f:
                for line in f:
                    line = line.strip().split()
                    if len(line) > 1:
                        self.freq_words[line[1]] = int(line[0])
        if self.freq_words:
            self.freq_mean = mean(list(self.freq_words.values()))

        with open(langnames_fn, "r") as f:
            for line in f:
                line = line.split("\t")
                self.lang_map[line[0]] = line[1].strip("\n")

        self.stopwords = set(nltk_stopwords.words(self.lang_map[lang]))
        self.lang = lang

        self.longman_definitions = {}
        if os.path.exists(longman_fn):
            with open(longman_fn, "r+") as f:
                self.longman_definitions = json.loads(f.read())

        with open(definitions_fn, "r") as f:
            for line in f:
                line = line.split("\t")
                if len(line[2].strip().strip("\n")) > 5:
                    word = line[0].strip()

                    if lang == "it":
                        synsets = wn.synsets(word, lang="ita")
                    elif lang == "en":
                        synsets = wn.synsets(word, lang="eng")
                    elif lang == "de":
                        synsets = []
                    else:
                        synsets = wn.synsets(word, lang=lang)

                    lemmas = []
                    for i in synsets:
                        if i.pos() not in self.synset_lexicon[word]:
                            if lang == "it":
                                lemmas += i.lemmas(lang="ita")
                            else:
                                lemmas += i.lemmas()
                            self.synset_lexicon[word][i.pos()] = [lemma.name(
                            ) for lemma in lemmas if lemma.name() != word]

                    defi = line[2].strip().strip("\n")
                    defi = self.parse_definition(defi)
                    if line[0].strip() not in self.lexicon:
                        self.lexicon[word] = defi.strip()
                        self.lexicon_list[word] = []
                    if defi.strip() != word:
                        def_splitted = defi.strip().split(";")
                        for def_split in def_splitted:
                            if (def_split not in self.lexicon_list[word]) and len(self.lexicon_list[word]) < 12:
                                self.lexicon_list[word].append(def_split)

    def parse_definition(self, defi):
        defi = re.sub(re.escape("#"), " ",  defi).strip()

        defi = re.sub(r"^A type of", "",  defi)
        defi = re.sub(r"^Something that", "",  defi)
        defi = re.sub(r"^Relating to", "",  defi)
        defi = re.sub(r"^Someone who", "",  defi)
        defi = re.sub(r"^Of or", "",  defi)
        defi = re.sub(r"^Any of", "",  defi)
        defi = re.sub(r"^The act of", "",  defi)
        defi = re.sub(r"^A group of", "",  defi)
        defi = re.sub(r"^The part of", "",  defi)
        defi = re.sub(r"^One of the", "",  defi)
        defi = re.sub(r"^Used to", "",  defi)
        defi = re.sub(r"^An attempt to", "",  defi)

        defi = re.sub(r"^intransitive", "",  defi)
        defi = re.sub(r"^ditransitive", "",  defi)
        defi = re.sub(r"^ambitransitive", "",  defi)
        defi = re.sub(r"^transitive", "",  defi)
        defi = re.sub(r"^uncountable", "",  defi)
        defi = re.sub(r"^countable", "",  defi)
        defi = re.sub(r"^pulative ", "",  defi)
        defi = re.sub(r"^\. ", "",  defi)
        defi_words = defi.split(" ")
        first_words = defi_words[0].split(',')
        if len(first_words) > 1 and re.sub("\'s", "", first_words[0].lower()) == \
                re.sub("\'s", "", first_words[1].lower()):
            defi = " ".join([first_words[1]] + defi_words[1:])
        return defi

    def append_zero_paths(self, graph):
        edges = []
        for edge in graph.G.edges(data=True):
            X = edge[0]
            Y = edge[1]
            color = edge[2]['color']

            nodes_to_append = whitelisting(graph, Y)

            for node in nodes_to_append:
                edges.append((X, node, color))

            nodes_to_append = whitelisting(graph, X)
            for node in nodes_to_append:
                node_edges = graph.G.edges(node, data=True)
                for n in node_edges:
                    n_color = n[2]["color"]
                    edges.append((X, n[1], n_color))

        edges = list(set(edges))
        for edge in edges:
            graph.G.add_edge(edge[0], edge[1], color=edge[2])

    def whitelisting(self, graph, from_node=None):
        if not from_node:
            from_node = graph.root
        whitelist = []
        zero_graph = copy.deepcopy(graph)
        delete_list = []
        for edge in zero_graph.G.adj.items():
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

        for node in zero_graph.G.nodes():
            if algorithms.has_path(zero_graph.G, from_node, node):
                if node != from_node:
                    whitelist.append(node)

        return whitelist

    def blacklisting(self, graph):
        one_two_blacklist = ["A", "a", "b", "B"]
        for adj in graph.G._adj.values():
            # print(adj)
            for a in adj.items():
                #print(f"adj: {a[1]}")
                if {'color': 2} in a[1].values():
                    new_blacklist_item = a[0]
                    for node in graph.G.nodes:
                        if algorithms.has_path(graph.G, new_blacklist_item, node):
                            blacklist_node = graph.d_clean(node)
                            if blacklist_node != graph.root:
                                one_two_blacklist.append(
                                    blacklist_node.split('_')[0])
                    new_blacklist_item = graph.d_clean(new_blacklist_item)
                    if new_blacklist_item != graph.root:
                        one_two_blacklist.append(
                            new_blacklist_item.split('_')[0])
        return one_two_blacklist

    def substitute(self, graph, irtg_parser, depth=1, blacklist=[], filt=True, black_or_white="white", apply_from_depth=None, substituted=[]):
        if depth == 0:
            return
        
        if apply_from_depth == None:
            apply_from_depth = depth

        if depth == 0:
            return
        static_blacklist = ["a", "A", "b", "B"]
        if black_or_white.lower() == "white":
            whitelist = self.whitelisting(graph)
        elif black_or_white.lower() == "black":
            one_two_blacklist = self.blacklisting(graph)

        nodes = [node for node in graph.G.nodes(data=True)]
        for d_node, node_data in nodes:
            if "substituted" not in node_data:
                node = graph.d_clean(d_node).split('_')[0]
                if node not in self.lexicon:
                    node = node.lower()
                if self.lang == "de":
                    node = node.capitalize()
                    if node not in self.lexicon:
                        node = node.lower()
                node_ok = not filt
                if (black_or_white.lower() == "white" and d_node in whitelist) or (depth > apply_from_depth):
                    node_ok = True
                elif (black_or_white.lower() == "black" and node not in one_two_blacklist) or (depth > apply_from_depth):
                    node_ok = True

                if node not in self.stopwords and node in self.lexicon and node not in self.fourlang_definitions and node_ok and node not in static_blacklist and node not in substituted:
                    if node in self.reduced:
                        def_graph = self.reduced[node]
                        graph.merge_definition_graph(
                            def_graph, d_node, substitute=True)
                    else:                      
                        definition = self.lexicon[node]
                        if definition:

                            def_graph = irtg_parser(definition)
                            if len(def_graph.get_nodes()) > 0:
                                graph.merge_definition_graph(
                                    def_graph, d_node, substitute=True)
                                substituted.append(node)
                                self.reduced[node] = def_graph

        for d_node, node_data in graph.G.nodes(data=True):
            node = graph.d_clean(d_node).split('_')[0]
            if node in self.fourlang_definitions:
                nx.set_node_attributes(graph.G, {d_node: {'fourlang': True}})
        self.substitute(graph, irtg_parser,
                        depth-1, blacklist, filt, black_or_white, apply_from_depth)

    def expand(self, graph, irtg_parser, depth=1, blacklist=[], filt=True, black_or_white="white", apply_from_depth=None):
        if depth == 0:
            return
        
        if apply_from_depth == None:
            apply_from_depth = depth

        static_blacklist = ["a", "A", "b", "B"]

        if black_or_white.lower() == "white":
            whitelist = self.whitelisting(graph)
        elif black_or_white.lower() == "black":
            one_two_blacklist = self.blacklisting(graph)

        nodes = [node for node in graph.G.nodes(data=True)]
        for d_node, node_data in nodes:
            if "expanded" not in node_data:
                node = graph.d_clean(d_node).split('_')[0]
                if node not in self.lexicon:
                    node = node.lower()
                if self.lang == "de":
                    node = node.capitalize()
                    if node not in self.lexicon:
                        node = node.lower()
                node_ok = not filt
                if (black_or_white.lower() == "white" and d_node in whitelist) or (depth > apply_from_depth):
                    node_ok = True
                elif (black_or_white.lower() == "black" and node not in one_two_blacklist) or (depth > apply_from_depth):
                    node_ok = True
                if node not in self.stopwords and node in self.lexicon and node_ok and node not in static_blacklist:
                    if node in self.expanded:
                        def_graph = self.expanded[node]
                        graph.merge_definition_graph(def_graph, d_node)
                    else:
                        definition = self.lexicon[node]
                        if definition:
                            def_graph = irtg_parser(definition)
                            if len(def_graph.get_nodes()) > 0:
                                graph.merge_definition_graph(
                                    def_graph, d_node)
                                self.expanded[node] = def_graph

        self.expand(graph, irtg_parser,
                    depth-1, blacklist, filt, black_or_white, apply_from_depth)

    def expand_with_every_def(self, graph, irtg_parser, depth=1, blacklist=[], filt=True, black_or_white="white", apply_from_depth=None):
        if depth == 0:
            return
        
        if apply_from_depth == None:
            apply_from_depth = depth

        static_blacklist = ["a", "A", "b", "B"]

        if black_or_white.lower() == "white":
            whitelist = self.whitelisting(graph)
        elif black_or_white.lower() == "black":
            one_two_blacklist = self.blacklisting(graph)

        nodes = [node for node in graph.G.nodes(data=True)]
        for d_node, node_data in nodes:
            if "expanded" not in node_data:
                node = graph.d_clean(d_node).split('_')[0]
                if node not in self.lexicon:
                    node = node.lower()
                if self.lang == "de":
                    node = node.capitalize()
                    if node not in self.lexicon:
                        node = node.lower()
                node_ok = not filt
                if (black_or_white.lower() == "white" and d_node in whitelist) or (depth > apply_from_depth):
                    node_ok = True
                elif (black_or_white.lower() == "black" and node not in one_two_blacklist) or (depth > apply_from_depth):
                    node_ok = True
                if node not in self.stopwords and node in self.lexicon_list and node_ok and node not in static_blacklist:
                    if node in self.expanded_with_every_def:
                        def_graph = self.expanded_with_every_def[node]
                        for g in def_graph:
                            graph.merge_definition_graph(g, d_node)
                    else:
                        definitions = self.lexicon_list[node]
                        if definitions:
                            concrete_definitions = definitions.copy() if not graph.expanded else [
                                definitions[0]]
                            for definition in concrete_definitions:
                                irtg_graph = irtg_parser(definition)
                                if len(irtg_graph.get_nodes()) > 0:
                                    graph.merge_definition_graph(
                                        irtg_graph, d_node)
                                    self.expanded_with_every_def[node].append(
                                        irtg_graph)

        graph.expanded = True
        self.expand_with_every_def(graph, irtg_parser,
                                   depth-1, blacklist, filt, black_or_white, apply_from_depth)

    def save_expanded(self, path):
        with open(path, 'wb') as handle:
            pickle.dump(self.expanded, handle,
                        protocol=pickle.HIGHEST_PROTOCOL)

    def load_expanded(self, path):
        with open(path, 'rb') as handle:
            self.expanded = pickle.load(handle)
