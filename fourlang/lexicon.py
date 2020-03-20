import os
import networkx as nx
from nltk.corpus import stopwords as nltk_stopwords
from networkx import algorithms
import re
import logging
import copy


def nx_to_ud(graph):
    ud_list = []
    edges = [edge for edge in graph.edges(data=True)]
    for in_node, out_node, t in edges:
        in_node_split = in_node.split("_")
        if len(in_node_split) > 2:
            in_node_split = ["_".join(in_node_split[:-1]), in_node_split[-1]]
        out_node_split = out_node.split("_")
        if len(out_node_split) > 2:
            out_node_split = ["_".join(out_node_split[:-1]), out_node_split[-1]]
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
            sender = "_".join(dependency[1])
            receiver = "_".join(dependency[2])
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
        self.lexicon_list = {}
        self.lang_map = {}
        base_fn = os.path.dirname(os.path.abspath(__file__))
        langnames_fn = os.path.join(base_fn, "langnames")
        definitions_fn = os.path.join(base_fn, "definitions/" + lang)
        self.expanded = {}

        with open(langnames_fn, "r") as f:
            for line in f:
                line = line.split("\t")
                self.lang_map[line[0]] = line[1].strip("\n")

        self.stopwords = set(nltk_stopwords.words(self.lang_map[lang]))
        self.lang = lang

        with open(definitions_fn, "r") as f:
            for line in f:
                line = line.split("\t")
                if len(line[2].strip().strip("\n")) > 5:
                    word = line[0].strip()
                    defi = line[2].strip().strip("\n")
                    defi = re.sub(re.escape("#"), " ",  defi)
                    if line[0].strip() not in self.lexicon_list:
                        self.lexicon[word] = defi.strip()
                        self.lexicon_list[word] = []
                    if defi.strip() != word:
                        self.lexicon_list[word].append(defi.strip())

    def expand(self, graph, dep_to_4lang, parser_wrapper, depth=1, blacklist=[], filt=True):
        if depth == 0:
            return
        one_two_blacklist = ["A","a","b","B"]
        if filt:
            for adj in graph.G._adj.values():
                for a in adj.items():
                    if {'color': 2} in a[1].values():
                        new_blacklist_item = a[0]
                        for node in graph.G.nodes:
                            if algorithms.has_path(graph.G, new_blacklist_item, node):
                                blacklist_node = graph.d_clean(node)
                                if blacklist_node != graph.root:
                                    one_two_blacklist.append(blacklist_node.split('_')[0])
                        new_blacklist_item = graph.d_clean(new_blacklist_item)
                        if new_blacklist_item != graph.root:
                            one_two_blacklist.append(new_blacklist_item.split('_')[0])
       
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
                if node not in self.stopwords and node in self.lexicon and node not in one_two_blacklist:
                    if node in self.expanded:
                        def_graph = self.expanded[node]
                        graph.merge_definition_graph(def_graph, d_node)
                    else:
                        definition = self.lexicon[node]
                        if definition:
                            parse = parser_wrapper.parse_text(definition, node)
                            deps = filter_graph(parse[0], blacklist)
                            corefs = parse[1]
                            ud_G = ud_to_nx(deps)
                            #filter_ud(ud_G, blacklist)
                            deps = nx_to_ud(ud_G)
                            if len(deps[0]) > 0:
                                def_graph = dep_to_4lang.get_machines_from_deps_and_corefs(deps, corefs)
                                graph.merge_definition_graph(def_graph, d_node)
                                self.expanded[node] = def_graph

        self.expand(graph, dep_to_4lang, parser_wrapper, depth-1, blacklist, filt)
        
    def expand_with_every_def(self, graph, dep_to_4lang, parser_wrapper, depth=1, blacklist=[]):
        if depth <= 0:
            raise ValueError("Cannot expand with depth {}".format(depth))
        nodes = [node for node in graph.G.nodes(data=True)]
        if len(nodes) > 1:
            logging.debug("The graph is too big for multi-definition expansion.\nSimple expand used instead.")
            self.expand(graph, dep_to_4lang, parser_wrapper, depth)

        graphs = []
        d_node, node_data = nodes[0]
        node = graph.d_clean(d_node).split('_')[0]
        if node not in self.lexicon:
            node = node.lower()
        if node not in self.stopwords and node in self.lexicon_list:
            definitions = self.lexicon_list[node]
            for definition in definitions:
                if definition:
                    current_graph = copy.deepcopy(graph)
                    parse = parser_wrapper.parse_text(definition)
                    deps = filter_graph(parse[0], blacklist)
                    corefs = parse[1]
                    if len(deps[0]) > 0:
                        def_graph = dep_to_4lang.get_machines_from_deps_and_corefs(deps, corefs)
                        current_graph.merge_definition_graph(def_graph, d_node)
                        if node not in self.expanded:
                            self.expanded[node] = def_graph
                    graphs.append(current_graph)

        for i in range(len(graphs)):
            self.expand(graphs[i], dep_to_4lang, parser_wrapper, depth-1)

        return graphs
