import json
import logging
import os
import re
import sys
import argparse
import numpy as np

from fourlang.stanford_wrapper import StanfordParser
from fourlang.lexicon import Lexicon
from fourlang.utils import dep_to_dot
from fourlang.fourlang import FourLang
from networkx.readwrite import json_graph

from tuw_nlp.grammar.ud_fl import UD_Fourlang
from tuw_nlp.graph.utils import read_alto_output

__LOGLEVEL__ = 'INFO'
__MACHINE_LOGLEVEL__ = 'INFO'


class TextTo4lang():
    square_regex = re.compile("\[.*?\]")

    def __init__(self, lang, serverless=True, port=5005):
        self.parser_wrapper = StanfordParser(lang, serverless, port)
        self.lexicon = Lexicon(lang)
        self.ud_fl = UD_Fourlang()
        self.irtg_parse = {}

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

    def process_graph(self, graph, method="expand", depth=1, blacklist=[], filt=True, multi_definition=False, black_or_white="white", apply_from_depth=None):
        if method == "expand":
            self.lexicon.expand(graph, irtg_parser=self.process_text_with_IRTG,
                                depth=depth, blacklist=blacklist, filt=filt, black_or_white=black_or_white, apply_from_depth=apply_from_depth)
        elif method == "substitute":
            self.lexicon.substitute(graph,
                                    depth=depth, blacklist=blacklist, filt=filt, black_or_white=black_or_white, apply_from_depth=apply_from_depth, irtg_parser=self.process_text_with_IRTG, rarity=rarity)

        return graph

    def get_ud_parse(self, text):
        logging.info("parsing text...")
        preproc_sens = []
        preproc_line = self.preprocess_text(str(text).strip())
        preproc_sens.append(preproc_line)
        parse = self.parser_wrapper.parse_text("\n".join(preproc_sens))
        deps = parse[0]
        dot_deps = dep_to_dot(deps)

        return dot_deps

    def parse_irtg(self, text):
        fl = None
        if text in self.irtg_parse:
            fl = self.irtg_parse[text]
        else:
            try:
                sen = self.parser_wrapper.parse_text_for_irtg(text)
                fl = self.ud_fl.parse(sen, 'ud', 'fourlang', 'amr-sgraph-src')
                self.irtg_parse[text] = fl
            except IndexError as e:
                print(e)

        return fl

    def process_text_with_IRTG(self, text):
        fl = self.parse_irtg(text)

        output, root = None, None
        if fl:
            output, root = read_alto_output(fl)
        graph = FourLang()

        if output and root:
            graph.G = output
            graph.root = root

        return graph

    def process_text(self, text, method="default", depth=1, blacklist=[], filt=True, multi_definition=False, black_or_white="white", apply_from_depth=None, rarity=False):
        logging.info("parsing text...")

        graph = self.process_text_with_IRTG(text)

        if method == "expand":
            if multi_definition:
                self.lexicon.expand_with_every_def(graph, irtg_parser=self.process_text_with_IRTG,
                                                   depth=depth, blacklist=blacklist, filt=filt, black_or_white=black_or_white, apply_from_depth=apply_from_depth)
            else:
                self.lexicon.expand(graph, irtg_parser=self.process_text_with_IRTG,
                                    depth=depth, blacklist=blacklist, filt=filt, black_or_white=black_or_white, apply_from_depth=apply_from_depth)
        elif method == "substitute":
            self.lexicon.substitute(
                graph, irtg_parser=self.process_text_with_IRTG, depth=depth, blacklist=blacklist, filt=filt, black_or_white=black_or_white, apply_from_depth=apply_from_depth, substituted=[])

        return graph


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
