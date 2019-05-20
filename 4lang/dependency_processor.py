from collections import defaultdict
from copy import deepcopy
import logging
import re

class Dependencies():
    dep_regex = re.compile("(.*?)\((.*?)-([0-9]*)'*, (.*?)-([0-9]*)'*\)")

    @staticmethod
    def parse_dependency(string):
        dep_match = Dependencies.dep_regex.match(string)
        if not dep_match:
            raise Exception('cannot parse dependency: {0}'.format(string))
        dep, word1, id1, word2, id2 = dep_match.groups()
        return dep, (word1, id1), (word2, id2)

    @staticmethod
    def create_from_strings(dep_strings):
        dep_list = map(Dependencies.parse_dependency, dep_strings)
        return Dependencies(dep_list)

    @staticmethod
    def create_from_new_deps(new_deps):
        deps = [(
            d['type'], (d['gov']['word'], d['gov']['id']),
            (d['dep']['word'], d['dep']['id'])) for d in new_deps]
        return Dependencies(deps)

    def __init__(self, dep_list):
        self.dep_list = dep_list
        self.index_dependencies(dep_list)

    def index_dependencies(self, deps):
        self.index = defaultdict(lambda: (defaultdict(set), defaultdict(set)))
        deps = [(dep, tuple(w1), tuple(w2)) for dep, w1, w2 in deps]
        for triple in deps:
            print(triple)
            self.add(triple)

    def remove(self, triple):
        dep = triple[0]
        word1 = triple[1]
        word2 = triple[2]
        self.index[word1][0][dep].remove(word2)
        self.index[word2][1][dep].remove(word1)

    def add(self, triple):
        dep = triple[0]
        word1 = triple[1]
        word2 = triple[2]
        self.index[word1][0][dep].add(word2)
        self.index[word2][1][dep].add(word1)

    def get_dep_list(self, exclude=[]):
        dep_list = []
        for word1, (dependants, _) in self.index.items():
            for dep, words in dependants.items():
                if any(dep.startswith(patt) for patt in exclude):
                    continue
                for word2 in words:
                    dep_list.append((dep, word1, word2))
        return dep_list

    def get_root(self):
        root_words = self.index[(u'ROOT', u'0')][0]['root']
        if len(root_words) != 1:
            logging.warning('no unique root element: {0}'.format(root_words))
            return None
        return iter(root_words).next()

    def merge(self, word1, word2, exclude=[]):
        for dep, w1, w2 in self.get_dep_list(exclude=exclude):
            if w1 in (word1, word2) and w2 in (word1, word2):
                pass
            elif w1 == word1:
                self.add((dep, word2, w2))
            elif w1 == word2:
                self.add((dep, word1, w2))
            elif w2 == word1:
                self.add((dep, w1, word2))
            elif w2 == word2:
                self.add((dep, w1, word1))
            else:
                pass


class NewDependencies():

    @staticmethod
    def create_from_old_deps(old_deps):
        deps = []
        for d_type, gov, dep in old_deps.get_dep_list():
            deps.append({
                "type": d_type,
                "gov": {
                    "word": gov[0],
                    "id": gov[1]},
                "dep": {
                    "word": dep[0],
                    "id": dep[1]}})
        return NewDependencies(deps)

    def __init__(self, deps):
        self.deps = deps
        self.indexed = False
        self.index()

    def index(self):
        self.tok_index = defaultdict(lambda: [None, [], []])
        self.dep_index = defaultdict(list)
        for d in self.deps:
            self.tok_index[d['gov']['id']][0] = d['gov']
            self.tok_index[d['dep']['id']][0] = d['dep']
            self.tok_index[d['gov']['id']][1].append(d)
            self.tok_index[d['dep']['id']][2].append(d)
            self.dep_index[d['type']].append(d)

        self.indexed = True

    def add(self, d_type, gov, dep):
        self.deps.append({"type": d_type, "gov": gov, "dep": dep})
        self.indexed = False

    def remove_tok(self, i):
        self.deps = [
            d for d in self.deps
            if d['gov']['id'] != i and d['dep']['id'] != i]
        self.indexed = False

    def remove_type(self, d_type):
        self.deps = [d for d in self.deps if d['type'] != d_type]
        self.indexed = False


class DependencyProcessor():
    copulars = set([
        "'s", 'are', 'be', 'been', 'being', 'is', 's', 'was', 'were'])

    def process_coordination_stanford(self, deps):
        print(deps.index.items())
        for word1, word_deps in deepcopy(list(deps.index.items())):
            for i in (0, 1):
                for dep, words in word_deps[i].items():
                    if dep.startswith('conj_'):
                        for word2 in words:
                            deps.merge(word1, word2, exclude=['conj_'])
                    elif dep.startswith('conj:'):
                        for word2 in words:
                            deps.merge(word1, word2, exclude=['conj:'])
        return deps

    def process_rcmods(self, deps):
        return deps

    def process_negation(self, deps):
        for dep in deps.get_dep_list():
            dtype, w1, w2 = dep
            if dtype == 'neg' and w2[0] != 'not':
                deps.remove(dep)
                deps.add((dtype, w1, ('not', w2[1])))
        return deps

    def remove_copulars(self, deps):
        for dep, word1, word2 in deps.get_dep_list():
            if (word1[0] in DependencyProcessor.copulars or
                    word2[0] in DependencyProcessor.copulars):
                deps.remove((dep, word1, word2))

        return deps

    def process_copulars(self, deps):
        copulars = [(word, w_id) for word, w_id in deps.index
                    if word in DependencyProcessor.copulars]
        new_deps = []
        processed = False
        for cop in copulars:
            if 'nsubj' in deps.index[cop][0]:
                for dep, words in deps.index[cop][0].items():
                    if dep.startswith('prep_'):
                        for word2 in words:
                            new_deps += [
                                (dep, word3, word2)
                                for word3 in deps.index[cop][0]['nsubj']]
            if 'rcmod' in deps.index[cop][1]:
                for dep, words in deps.index[cop][0].items():
                    if dep.startswith('prep_'):
                        for word2 in words:
                            new_deps += [
                                (dep, word3, word2)
                                for word3 in deps.index[cop][1]['rcmod']]
        for new_dep in new_deps:
            processed = True
            deps.add(new_dep)

        if processed:  # TODO
            deps = self.remove_copulars(deps)
        return deps

    def process_stanford_dependencies(self, dep_strings):
        try: 
            deps = Dependencies.create_from_strings(dep_strings)
        except TypeError:
            try:
                deps = Dependencies.create_from_new_deps(dep_strings)
            except:
                deps = Dependencies(dep_strings)

        deps = self.process_copulars(deps)
        deps = self.process_rcmods(deps)
        deps = self.process_negation(deps)
        deps = self.process_coordination_stanford(deps)

        return NewDependencies.create_from_old_deps(deps).deps
