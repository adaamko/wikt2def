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
from networkx import algorithms


class FourLang():
    dep_regex = re.compile("([a-z_-]*)\((.*?)-([0-9]*)'*, (.*?)-([0-9]*)'*\)")

    def __init__(self):
        self.G=nx.MultiDiGraph()
        self.root = None

    def add_node(self, concept):
        if concept.printname != "ROOT":
            self.G.add_node(concept.unique_name())

    def add_root(self, concept):
        self.root = concept.unique_name()
        self.G.add_node(concept.unique_name())

    def connect_edges(self, concept1, concept2, label):
        self.G.add_edge(concept1.unique_name(), concept2.unique_name(), color=label)

    def get_graph(self):
        return self.G

    def filter_graph(self, condition):
        nodes = self.G.nodes(default=None)
        cond_nodes = []
        to_delete = []
        for node in nodes:
            cl = self.d_clean(node)
            if condition == cl.split("_")[0]:
                cond_nodes.append(node)
        
        for cond_node in cond_nodes:
            for node in nodes:
                if cond_node in self.G and node in self.G:
                    if algorithms.has_path(self.G, cond_node, node):
                        to_delete.append(node)

        for node in to_delete:
            if node in self.G.nodes(default=None):
                self.G.remove_node(node)

    def merge_definition_graph(self, graph, node):
        graph_root = graph.root
        attrs = {node: {'expanded': True}}
        #graph.G = nx.relabel_nodes(graph.G, {graph_root: self.root})
        self.G.add_edge(node, graph_root, color=0)
        F = nx.compose(self.G, graph.G)
        self.G = F
        nx.set_node_attributes(self.G, attrs)

    def d_clean(self, string):
        s = string
        for c in '\\=@-,\'".!:;<>/{}[]()#':
            s = s.replace(c, '_')
        s = s.replace('$', '_dollars')
        s = s.replace('%', '_percent')
        s = s.replace('|', ' ')
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

    def to_dot(self, marked_nodes=set()):
        lines = [u'digraph finite_state_machine {', '\tdpi=70;']
        # lines.append('\tordering=out;')
        # sorting everything to make the process deterministic
        self.d_clean("asd")
        node_lines = []
        for node, n_data in self.G.nodes(data=True):
            d_node = self.d_clean(node)
            printname = self.d_clean('_'.join(d_node.split('_')[:-1]))
            if 'expanded' in n_data and n_data['expanded'] and printname in marked_nodes:
                node_line = u'\t{0} [shape = circle, label = "{1}", \
                        style=filled, fillcolor=purple];'.format(
                    d_node, printname).replace('-', '_')
            elif 'expanded' in n_data and n_data['expanded']:
                node_line = u'\t{0} [shape = circle, label = "{1}", \
                        style="filled"];'.format(
                    d_node, printname).replace('-', '_')
            elif printname in marked_nodes:
                node_line = u'\t{0} [shape = circle, label = "{1}", style=filled, fillcolor=lightblue];'.format(
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
