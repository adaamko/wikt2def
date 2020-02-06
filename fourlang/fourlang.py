from collections import defaultdict
from .dependency_processor import DependencyProcessor
from .concept import Concept

import networkx as nx
import json
import logging
import os
import re
import sys
import traceback


class FourLang():
    dep_regex = re.compile("([a-z_-]*)\((.*?)-([0-9]*)'*, (.*?)-([0-9]*)'*\)")

    def __init__(self):
        self.G=nx.MultiDiGraph()

    def connect_edges(self, concept1, concept2, label):
        self.G.add_edge(concept1.unique_name(), concept2.unique_name(), color=label)

    def get_graph(self):
        return self.G

    def d_clean(self, string):
        s = string
        for c in '\\=@-,\'".!:;':
            s = s.replace(c, '_')
        s = s.replace('$', '_dollars')
        s = s.replace('%', '_percent')
        if s == '#':
            s = '_number'
        keywords = ("graph", "node", "strict", "edge")
        if re.match('^[0-9]', s) or s in keywords:
            s = "X" + s
        return s

    def get_edges(self):
        lines = []
        # lines.append('\tordering=out;')
        # sorting everything to make the process deterministic

        edge_lines = []
        for u, v, edata in self.G.edges(data=True):
            if 'color' in edata:
                d_node1 = self.d_clean(u)
                d_node2 = self.d_clean(v)

                lines.append((self.d_clean(d_node1).split("_")[0], self.d_clean(d_node2).split("_")[0], edata['color']))
        return lines

    def get_nodes(self):
        nodes_cleaned = []
        nodes = self.G.nodes(default=None)
        for node in nodes:
            cl = self.d_clean(node)
            nodes_cleaned.append(cl.split("_")[0])
        return nodes_cleaned

    def to_dot(self):
        lines = [u'digraph finite_state_machine {', '\tdpi=70;']
        # lines.append('\tordering=out;')
        # sorting everything to make the process deterministic
        self.d_clean("asd")
        node_lines = []
        for node, n_data in self.G.nodes(data=True):
            d_node = self.d_clean(node)
            printname = self.d_clean('_'.join(d_node.split('_')[:-1]))
            if 'expanded' in n_data and not n_data['expanded']:
                node_line = u'\t{0} [shape = circle, label = "{1}", \
                        style="filled"];'.format(
                                d_node, printname).replace('-', '_')
            else:
                node_line = u'\t{0} [shape = circle, label = "{1}"];'.format(
                        d_node, printname).replace('-', '_')
                node_lines.append(node_line)
        lines += sorted(node_lines)

        edge_lines = []
        for u, v, edata in self.G.edges(data=True):
            if 'color' in edata:
                d_node1 = self.d_clean(u)
                d_node2 = self.d_clean(v)
                edge_lines.append(
                        u'\t{0} -> {1} [ label = "{2}" ];'.format(
                            self.d_clean(d_node1), self.d_clean(d_node2),
                            edata['color']))

        lines += sorted(edge_lines)
        lines.append('}')
        return u'\n'.join(lines)
                        
