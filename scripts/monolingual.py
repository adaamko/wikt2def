import argparse
from scripts.similarity import Similarity
from fourlang.text_to_4lang import TextTo4lang
from fourlang.lexicon import Lexicon
from scripts.parse_data import read
import subprocess
import sys
import os
import requests
import time


class Monolingual:
    def __init__(self, lang):
        self.lang = lang

        # Start services
        self.pid_elmo = subprocess.Popen("{} {} -p 1666".format(
            sys.executable, os.path.join(os.path.dirname(__file__), "elmo_service.py")).split(' '))
        self.pid_ud = subprocess.Popen("{} {} -p 5005 -l {}".format(
            sys.executable, os.path.join(os.path.dirname(__file__), "../fourlang/service/ud_service.py"), lang).split(' '))
        ud_server_up = False
        while not ud_server_up:
            try:
                requests.head("http://127.0.0.1:5005")
                ud_server_up = True
            except requests.exceptions.ConnectionError:
                time.sleep(5)

        # Create objects
        self.similarity = Similarity(self.lang)
        self.text_to_4lang = TextTo4lang(self.lang)
        self.lexicon = Lexicon(self.lang)

    def main(self, graded):
        graded_text = "graded" if graded else "binary"
        data = read(self.lang, graded=graded)

        # Initialize similarity lists
        if not os.path.exists(os.path.join(os.path.dirname(__file__), "../results/{}/{}".format(graded_text, self.lang))):
            os.makedirs(os.path.join(os.path.dirname(__file__), "../results/{}/{}".format(graded_text, self.lang)))
        results = {
            "asim_jac_word": open(
                os.path.join(os.path.dirname(__file__),
                             "../results/{}/{}/asim_jac_bow.txt".format(graded_text, self.lang)), "w"),
            "asim_jac_node": open(
                os.path.join(os.path.dirname(__file__),
                             "../results/{}/{}/asim_jac_node.txt".format(graded_text, self.lang)), "w"),
            "asim_jac_edge": open(
                os.path.join(os.path.dirname(__file__),
                             "../results/{}/{}/asim_jac_edge.txt".format(graded_text, self.lang)), "w"),
            "asim_jac_bow_elmo": open(
                os.path.join(os.path.dirname(__file__),
                             "../results/{}/{}/asim_jac_bow_elmo.txt".format(graded_text, self.lang)), "w"),
            "asim_jac_node_elmo": open(
                os.path.join(os.path.dirname(__file__),
                             "../results/{}/{}/asim_jac_node_elmo.txt".format(graded_text, self.lang)), "w"),
            "asim_jac_edge_elmo": open(
                os.path.join(os.path.dirname(__file__),
                             "../results/{}/{}/asim_jac_edge_elmo.txt".format(graded_text, self.lang)), "w")
        }

        for index, row in data.iterrows():
            premise = row.premise
            hypothesis = row.hypothesis

            graph_premise = self.text_to_4lang.process_text(premise, True)
            graph_hypothesis = self.text_to_4lang.process_text(hypothesis, True)
            def_premise = ""
            def_hypothesis = ""
            if premise in self.lexicon.lexicon:
                def_premise = self.lexicon.lexicon[premise]
            if hypothesis in self.lexicon.lexicon:
                def_hypothesis = self.lexicon.lexicon[hypothesis]
            try:
                results["asim_jac_word"].write(" ".join(
                    [premise, hypothesis, str(self.similarity.asim_jac_words(def_premise, def_hypothesis))])+"\n")
                results["asim_jac_node"].write(" ".join(
                    [premise, hypothesis, str(self.similarity.asim_jac_nodes(graph_premise, graph_hypothesis))])+"\n")
                results["asim_jac_edge"].write(" ".join(
                    [premise, hypothesis, str(self.similarity.asim_jac_edges(graph_premise, graph_hypothesis))])+"\n")
                results["asim_jac_bow_elmo"].write(" ".join(
                    [premise, hypothesis, str(self.similarity.asim_jac_bow_elmo(def_premise, def_hypothesis))])+"\n")
                results["asim_jac_node_elmo"].write(" ".join(
                    [premise, hypothesis, str(self.similarity.asim_jac_nodes_elmo(premise, hypothesis,
                                                                                  graph_premise, graph_hypothesis,
                                                                                  def_premise, def_hypothesis))])+"\n")
                results["asim_jac_edge_elmo"].write(" ".join(
                    [premise, hypothesis, str(self.similarity.asim_jac_edges_elmo(premise, hypothesis,
                                                                                  graph_premise, graph_hypothesis,
                                                                                  def_premise, def_hypothesis))])+"\n")
            except Exception as e:
                self.pid_elmo.terminate()
                self.pid_ud.terminate()
                raise e
        self.pid_elmo.terminate()
        self.pid_ud.terminate()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Service to generate embeddings in a given language")
    parser.add_argument("-l", "--lang", required=True, help="set the language")
    args = parser.parse_args()
    mono = Monolingual(lang=args.lang)
    mono.main(graded=False)
