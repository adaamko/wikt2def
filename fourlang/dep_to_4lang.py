from collections import defaultdict
from .dependency_processor import DependencyProcessor
from .operators import AppendOperator, AppendToNewBinaryOperator
from .fourlang import FourLang
from .concept import Concept

import json
import logging
import os
import re
import sys
import traceback

class DepTo4lang():
    dep_regex = re.compile("([a-z_-]*)\((.*?)-([0-9]*)'*, (.*?)-([0-9]*)'*\)")

    def __init__(self):
        base_fn = os.path.dirname(os.path.abspath(__file__))
        dep_map_fn = os.path.join(base_fn, "dep_to_4lang.txt")
        self.read_dep_map(dep_map_fn)
        self.dependency_processor = DependencyProcessor()
        self.undefined = set()
    
    def read_dep_map(self, dep_map_fn):
        self.dependencies = defaultdict(list)
        with open(dep_map_fn) as f:
            for line in f:
                l = line.strip()
                if not l or l.startswith('#'):
                    continue
                dep = Dependency.create_from_line(l)
                self.dependencies[dep.name].append(dep)
    
    def apply_dep(self, dep, concept1, concept2, graph):
        dep_type = dep['type']
        msd1 = dep['gov'].get('msd')
        msd2 = dep['dep'].get('msd')
        if dep_type not in self.dependencies:
            if dep_type not in self.undefined:
                self.undefined.add(dep_type)
                logging.warning(
                    'skipping dependency not in dep_to_4lang map: {0}'.format(
                        dep_type))
            return False
        for dep in self.dependencies[dep_type]:
            dep.apply(msd1, msd2, concept1, concept2, graph)

    def get_machines_from_deps_and_corefs(self, dep_lists, corefs):
        graph = FourLang()
        dep_lists = map(
                self.dependency_processor.process_stanford_dependencies, dep_lists)
        coref_index = defaultdict(dict)
        for (word, sen_no), mentions in corefs:
            for m_word, m_sen_no in mentions:
                coref_index[m_word][m_sen_no-1] = word

        mapped_dependencies = {}
        for i, deps in enumerate(dep_lists):
            try:
                for dep in deps:
                    word1 = dep['gov']['word']
                    word2 = dep['dep']['word']
                    
                    lemma1 = coref_index[word1].get(i, word1)
                    lemma2 = coref_index[word2].get(i, word2)

                    for lemma in (lemma1, lemma2):
                        if lemma not in mapped_dependencies:
                            mapped_dependencies[lemma] = Concept(lemma)

                    self.apply_dep(
                        dep, mapped_dependencies[lemma1], mapped_dependencies[lemma2], graph)
            except:
                logging.error(u"failure on dep: {0}({1}, {2})".format(
                    dep, lemma1, lemma2))
                traceback.print_exc()
                raise Exception("adding dependencies failed")

        return graph

class Dependency():
    def __init__(self, name, patt1, patt2, operators=[]):
        self.name = name
        self.patt1 = re.compile(patt1) if patt1 else None
        self.patt2 = re.compile(patt2) if patt2 else None
        self.operators = operators

    @staticmethod
    def create_from_line(line):
        rel, reverse = None, False
        # logging.debug('parsing line: {}'.format(line))
        fields = line.split('\t')
        if len(fields) == 2:
            dep, edges = fields
        elif len(fields) == 3:
            dep, edges, rel = fields
            if rel[0] == '!':
                rel = rel[1:]
                reverse = True
        else:
            raise Exception('lines must have 2 or 3 fields: {}'.format(
                fields))

        if ',' in dep:
            dep, patt1, patt2 = dep.split(',')
        else:
            patt1, patt2 = None, None

        edge1, edge2 = map(lambda s: int(s) if s not in ('-', '?') else None,
                           edges.split(','))

        if (dep.startswith('prep_') or
                dep.startswith('prepc_')) and rel is None:
            rel = dep.split('_', 1)[1].upper()

        # Universal Dependencies
        if ((dep.startswith('acl:') and not dep.startswith('acl:relcl')) or
                dep.startswith('advcl:') or
                dep.startswith('nmod:')) and rel is None:
            rel = dep.split(':', 1)[1].upper()

        return Dependency(
            dep, patt1, patt2, Dependency.get_standard_operators(
                edge1, edge2, rel, reverse))

    @staticmethod
    def get_standard_operators(edge1, edge2, rel, reverse):
        operators = []
        if edge1 is not None:  # it can be zero, don't check for truth value!
            operators.append(AppendOperator(0, 1, part=edge1))
        if edge2 is not None:
            operators.append(AppendOperator(1, 0, part=edge2))
        if rel:
            operators.append(
                AppendToNewBinaryOperator(rel.lower(), 0, 1, reverse=reverse))

        return operators

    def match(self, msd1, msd2):
        for patt, msd in ((self.patt1, msd1), (self.patt2, msd2)):
            if patt is not None and msd is not None and not patt.match(msd):
                return False
        return True

    def apply(self, msd1, msd2, concept1, concept2, graph):
        logging.debug(
            'trying {0} on {1} and {2}...'.format(self.name, msd1, msd2))
        if self.match(msd1, msd2):
            logging.debug('MATCH!')
            if concept1.printname == "ROOT":
                graph.add_root(concept2)
            for operator in self.operators:
                operator.act((concept1, concept2), graph)

def main():
    pass

if __name__ == "__main__":
    main()
