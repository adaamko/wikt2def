import os
import networkx as nx
from nltk.corpus import stopwords as nltk_stopwords
from networkx import algorithms
import re


def nx_to_ud(graph):
    ud_list = []
    edges = [edge for edge in graph.edges(data=True)]
    for in_node, out_node, t in edges:
        ud_list.append([t["color"], in_node.split("_"), out_node.split("_")])

    return [ud_list]


def ud_to_nx(ud):
    G = nx.MultiDiGraph()
    nodes = set()
    for dependency in ud[0]:
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


def filter_ud(graph):
    blacklist = ["in", "of", "on"]
    edges = [edge for edge in graph.edges(data=True)]
    cond_nodes = []
    for in_node, out_node, t in edges:
        if t["color"] == "case" and out_node.split("_")[0] in blacklist:
            for in_, out_, t_ in edges:
                if t_["color"] == "nmod" and (in_ == in_node or out_ == in_node):
                    cond_nodes.append(in_node)
            #cond_nodes.append(in_node)

    to_delete = []

    for cond_node in cond_nodes:
        for node in graph.nodes():
            if cond_node in graph and node in graph:
                if algorithms.has_path(graph, cond_node, node):
                    to_delete.append(node)

    for node in to_delete:
        if node in graph.nodes(default=None):
            graph.remove_node(node)


class Lexicon():

    def __init__(self, lang):
        self.lexicon = {}
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

        with open(definitions_fn, "r") as f:
            for line in f:
                line = line.split("\t")
                if line[0].strip() not in self.lexicon and len(line[2].strip().strip("\n")) > 5:
                    defi = line[2].strip().strip("\n")
                    defi = re.sub(re.escape("#"), " ",  defi)
                    self.lexicon[line[0].strip()] = defi.strip()

    def expand(self, graph, dep_to_4lang, parser_wrapper, depth=1):
        if depth == 0:
            return
        blacklist = []
        for adj in graph.G._adj.values():
            for a in adj.items():
                if {'color': 2} in a[1].values() or {'color': 1} in a[1].values():
                    new_blacklist_item = a[0]
                    blacklist.append(new_blacklist_item.split('_')[0])
                    for node in graph.G.nodes:
                        if algorithms.has_path(graph.G, new_blacklist_item, node):
                            blacklist.append(node.split('_')[0])
        nodes = [node for node in graph.G.nodes(data=True)]
        for d_node, node_data in nodes:
            if "expanded" not in node_data:
                node = graph.d_clean(d_node).split('_')[0]
                if node not in self.lexicon:
                    node = node.lower()
                if node not in self.stopwords and node in self.lexicon and node not in blacklist:
                    if node in self.expanded:
                        def_graph = self.expanded[node]
                        graph.merge_definition_graph(def_graph, d_node)
                    else:
                        definition = self.lexicon[node]
                        if definition:
                            parse = parser_wrapper.parse_text(definition, node)
                            deps = parse[0]
                            corefs = parse[1]
                            ud_G = ud_to_nx(deps)
                            filter_ud(ud_G)
                            deps = nx_to_ud(ud_G)
                            if len(deps[0]) > 0:
                                def_graph = dep_to_4lang.get_machines_from_deps_and_corefs(
                                    deps, corefs)
                                graph.merge_definition_graph(def_graph, d_node)
                                self.expanded[node] = def_graph

        self.expand(graph, dep_to_4lang, parser_wrapper, depth-1)
