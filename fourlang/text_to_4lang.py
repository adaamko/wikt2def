import json
import logging
import os
import re
import sys
import argparse
import numpy as np

from .dep_to_4lang import DepTo4lang
from .stanford_wrapper import StanfordParser
from .lexicon import Lexicon
from networkx.readwrite import json_graph

__LOGLEVEL__ = 'INFO'
__MACHINE_LOGLEVEL__ = 'INFO'


class TextTo4lang():
    square_regex = re.compile("\[.*?\]")

    def __init__(self, lang):
        self.parser_wrapper = StanfordParser(lang)
        self.dep_to_4lang = DepTo4lang()
        self.lexicon = Lexicon(lang)

    def get_definition(self, word):
        if word in self.lexicon.lexicon:
            return self.lexicon.lexicon[word]
        else:
            return None
    
    def get_longman_definition(self, word):
        if word in self.lexicon.longman_definitions:
            return self.lexicon.longman_definitions[word]["senses"][0]["definition"]["sen"]
        else:
            return None

    def get_synsets(self, word, pos="v"):
        if word in self.lexicon.synset_lexicon and pos in self.lexicon.synset_lexicon[word]:
            return self.lexicon.synset_lexicon[word][pos]
        else:
            return None

    def preprocess_text(self, text):
        t = text.strip()
        t = TextTo4lang.square_regex.sub('', t)
        t = t.replace(u"=", u"_eq_")
        t = t.replace(u"\xc2\xa0", u" ")
        t = t.replace(u"\xa0", u" ")
        t = t.strip()
        return t

    def process_graph(self, graph, method="expand", depth=1, blacklist=[], filt=True, multi_definition=False, black_or_white="white", rarity=False):
        if method == "expand":
            if multi_definition:
                return self.lexicon.expand_with_every_def(graph, self.dep_to_4lang, self.parser_wrapper, depth=depth,
                                                          blacklist=blacklist, filt=filt, black_or_white=black_or_white)
            else:
                self.lexicon.expand(graph, self.dep_to_4lang, self.parser_wrapper,
                                    depth=depth, blacklist=blacklist, filt=filt, black_or_white=black_or_white, rarity=rarity)
        elif method == "substitute":
            self.lexicon.substitute(graph, self.dep_to_4lang, self.parser_wrapper,
                                    depth=depth, blacklist=blacklist, filt=filt, black_or_white=black_or_white, rarity=rarity)

        return graph


    def process_deps(self, deps,  method="default", depth=1, blacklist=[], filt=True, multi_definition=False, black_or_white="white", rarity=False):
        corefs = []
        if "root" not in [d[0] for d in deps[0]]:
            unique, counts = np.unique(np.array([d[1] for d in deps[0]]), axis=0, return_counts=True)
            index = np.argmax(counts)
            deps[0].append(["root", ["ROOT", -1], unique[index].tolist()])
        graph = self.dep_to_4lang.get_machines_from_deps_and_corefs(
            deps, corefs)

        if method == "expand":
            if multi_definition:
                return self.lexicon.expand_with_every_def(graph, self.dep_to_4lang, self.parser_wrapper, depth=depth,
                                                          blacklist=blacklist, filt=filt, black_or_white=black_or_white, rarity=rarity)
            else:
                self.lexicon.expand(graph, self.dep_to_4lang, self.parser_wrapper,
                                    depth=depth, blacklist=blacklist, filt=filt, black_or_white=black_or_white, rarity=rarity)
        elif method == "substitute":
            self.lexicon.substitute(graph, self.dep_to_4lang, self.parser_wrapper,
                                    depth=depth, blacklist=blacklist, filt=filt, black_or_white=black_or_white, rarity=rarity)

        return graph

    def process_text(self, text, method="default", depth=1, blacklist=[], filt=True, multi_definition=False, black_or_white="white", rarity=False):
        logging.info("parsing text...")
        preproc_sens = []
        preproc_line = self.preprocess_text(str(text).strip())
        preproc_sens.append(preproc_line)
        parse = self.parser_wrapper.parse_text("\n".join(preproc_sens))
        deps = parse[0]
        corefs = parse[1]

        graph = self.dep_to_4lang.get_machines_from_deps_and_corefs(
            deps, corefs)

        if method == "expand":
            if multi_definition:
                return self.lexicon.expand_with_every_def(graph, self.dep_to_4lang, self.parser_wrapper, depth=depth,
                                                          blacklist=blacklist, filt=filt, black_or_white=black_or_white, rarity=rarity)
            else:
                self.lexicon.expand(graph, self.dep_to_4lang, self.parser_wrapper,
                                    depth=depth, blacklist=blacklist, filt=filt, black_or_white=black_or_white, rarity=rarity)
        elif method == "substitute":
            self.lexicon.substitute(
                graph, self.dep_to_4lang, self.parser_wrapper, depth=depth, blacklist=blacklist, filt=filt, black_or_white=black_or_white,rarity=rarity)

        return graph

    def process_file(self, fn, out_fn):
        graphs = None
        if not os.path.exists(fn):
            logging.info('file not exists: {0}, not parsing'.format(fn))
        elif not os.path.exists(out_fn):
            logging.info(
                'out directory not exists: {0}, not parsing'.format(out_fn))
        else:
            deps_fn = self.parse_file(fn, out_fn)
            graphs = self.process_deps_complex(deps_fn)

        return graphs

    def parse_file(self, fn, out_fn):
        logging.info("parsing file: {0}".format(fn))
        preproc_sens = []

        with open(fn, "r", encoding="utf-8") as f:
            for line in f:
                if not line:
                    continue
                preproc_line = self.preprocess_text(line.strip())
                preproc_sens.append(preproc_line)

        parse = self.parser_wrapper.parse_text("\n".join(preproc_sens))
        deps = parse[0]
        corefs = parse[1]
        deps_fn = os.path.join(out_fn, "dependencies.json")
        with open(deps_fn, 'w') as out_f:
            out_f.write("{0}\n".format(json.dumps({
                "deps": deps,
                "corefs": corefs})))
        logging.info("parsed {0} sentences".format(len(deps)))

        return deps_fn

    def process_deps_complex(self, fn):
        sen_graphs = []
        for line in open(fn):
            data = json.loads(line)
            deps, corefs = data['deps'], data['corefs']
            logging.info("processing sentences...")
            graph = self.dep_to_4lang.get_machines_from_deps_and_corefs(
                deps, corefs)
            self.dep_to_4lang.lexicon.expand(graph)

            sen_graphs.append(graph)

        return sen_graphs


def main(input_file, output_dir):
    logging.basicConfig(
        level=__LOGLEVEL__,
        format="%(asctime)s : " +
        "%(module)s (%(lineno)s) - %(levelname)s - %(message)s")
    text_to_4lang = TextTo4lang()
    graphs = text_to_4lang.process_file(input_file, output_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("-i", "--inputfile", required=True,
                        nargs="+", help="the file to process")
    parser.add_argument("-o", "--outputdir", required=True,
                        nargs="+", help="the output directory to write the graphs")

    args = parser.parse_args()
    main(args.inputfile[0], args.outputdir[0])
