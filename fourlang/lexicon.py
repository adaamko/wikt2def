import os
from nltk.corpus import stopwords as nltk_stopwords

class Lexicon():
    
    def __init__(self, lang):
        self.lexicon = {}
        self.lang_map = {}
        base_fn = os.path.dirname(os.path.abspath(__file__))
        langnames_fn = os.path.join(base_fn, "langnames")
        definitions_fn = os.path.join(base_fn, "definitions/" + lang)

        with open(langnames_fn, "r") as f:
            for line in f:
                line = line.split("\t")
                self.lang_map[line[0]] = line[1].strip("\n")

        self.stopwords = set(nltk_stopwords.words(self.lang_map[lang]))

        with open(definitions_fn, "r") as f:
            for line in f:
                line = line.split("\t")
                if line[0].strip() not in self.lexicon:
                    self.lexicon[line[0].strip()] = line[2].strip().strip("\n")

    def expand(self, graph, dep_to_4lang, parser_wrapper):
        for node in graph.get_nodes():
            if node not in self.stopwords and node in self.lexicon:
                definition = self.lexicon[node]
                parse = parser_wrapper.parse_text(definition)
                deps = parse[0]
                corefs = parse[1]
                def_graph = dep_to_4lang.get_machines_from_deps_and_corefs(
                        deps, corefs)
                graph.merge_definition_graph(def_graph)



        