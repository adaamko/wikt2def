import argparse
from scripts.similarity import Similarity
from fourlang.text_to_4lang import TextTo4lang
from fourlang.lexicon import Lexicon
from scripts.parse_data import read
import pandas as pd
import subprocess
import sys
import os
import requests
import time


class Monolingual:
    def __init__(self, lang):
        self.lang = lang

    def main(self, graded):
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
                             "../results/{}/{}/asim_jac_edge_elmo.txt".format(graded_text, self.lang)), "w"),
            "elmo_similarity": open(
                os.path.join(os.path.dirname(__file__),
                             "../results/{}/{}/elmo_similarity.txt".format(graded_text, self.lang)), "w")
        }

        for index, row in data.iterrows():
            premise = row.premise
            hypothesis = row.hypothesis

            graph_premise = self.text_to_4lang.process_text(premise, True)
            graph_hypothesis = self.text_to_4lang.process_text(hypothesis, True)
            def_premise = ""
            def_hypothesis = ""
            lemma_premise = self.text_to_4lang.parser_wrapper.lemmatize_word(premise)
            lemma_hypothesis = self.text_to_4lang.parser_wrapper.lemmatize_word(hypothesis)
            if premise in self.lexicon.lexicon:
                def_premise = self.lexicon.lexicon[premise]
                if lemma_premise in self.lexicon.lexicon and self.lexicon.lexicon[lemma_premise] != self.lexicon.lexicon[premise]:
                    def_premise = " . ".join([def_premise, self.lexicon.lexicon[lemma_premise]])
            elif lemma_premise in self.lexicon.lexicon:
                def_premise = self.lexicon.lexicon[lemma_premise]

            if hypothesis in self.lexicon.lexicon:
                def_hypothesis = self.lexicon.lexicon[hypothesis]
                if lemma_hypothesis in self.lexicon.lexicon and self.lexicon.lexicon[lemma_hypothesis] != self.lexicon.lexicon[hypothesis]:
                    def_hypothesis = " . ".join([def_hypothesis, self.lexicon.lexicon[lemma_hypothesis]])
            elif lemma_premise in self.lexicon.lexicon:
                def_hypothesis = self.lexicon.lexicon[lemma_hypothesis]
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
                results["elmo_similarity"].write(" ".join(
                    [premise, hypothesis, str(self.similarity.word_elmo(premise, hypothesis))])+"\n")
            except Exception as e:
                self.pid_elmo.terminate()
                self.pid_ud.terminate()
                raise e
        self.pid_elmo.terminate()
        self.pid_ud.terminate()

    def binarize(self, threshold=0.5):
        results = {
            "asim_jac_word": open(
                os.path.join(os.path.dirname(__file__),
                             "../results/binary/{}/asim_jac_bow.txt".format(self.lang)), "r"),
            "asim_jac_node": open(
                os.path.join(os.path.dirname(__file__),
                             "../results/binary/{}/asim_jac_node.txt".format(self.lang)), "r"),
            "asim_jac_edge": open(
                os.path.join(os.path.dirname(__file__),
                             "../results/binary/{}/asim_jac_edge.txt".format(self.lang)), "r"),
            "asim_jac_bow_elmo": open(
                os.path.join(os.path.dirname(__file__),
                             "../results/binary/{}/asim_jac_bow_elmo.txt".format(self.lang)), "r"),
            "asim_jac_node_elmo": open(
                os.path.join(os.path.dirname(__file__),
                             "../results/binary/{}/asim_jac_node_elmo.txt".format(self.lang)), "r"),
            "asim_jac_edge_elmo": open(
                os.path.join(os.path.dirname(__file__),
                             "../results/binary/{}/asim_jac_edge_elmo.txt".format(self.lang)), "r"),
            "elmo_similarity": open(
                os.path.join(os.path.dirname(__file__),
                             "../results/binary/{}/elmo_similarity.txt".format(self.lang)), "r"),
        }
        result_bin = {
            "asim_jac_word": open(
                os.path.join(os.path.dirname(__file__),
                             "../results/binary/{}/asim_jac_bow_bin.txt".format(self.lang)), "w"),
            "asim_jac_node": open(
                os.path.join(os.path.dirname(__file__),
                             "../results/binary/{}/asim_jac_node_bin.txt".format(self.lang)), "w"),
            "asim_jac_edge": open(
                os.path.join(os.path.dirname(__file__),
                             "../results/binary/{}/asim_jac_edge_bin.txt".format(self.lang)), "w"),
            "asim_jac_bow_elmo": open(
                os.path.join(os.path.dirname(__file__),
                             "../results/binary/{}/asim_jac_bow_elmo_bin.txt".format(self.lang)), "w"),
            "asim_jac_node_elmo": open(
                os.path.join(os.path.dirname(__file__),
                             "../results/binary/{}/asim_jac_node_elmo_bin.txt".format(self.lang)), "w"),
            "asim_jac_edge_elmo": open(
                os.path.join(os.path.dirname(__file__),
                             "../results/binary/{}/asim_jac_edge_elmo_bin.txt".format(self.lang)), "w"),
            "elmo_similarity": open(
                os.path.join(os.path.dirname(__file__),
                             "../results/binary/{}/elmo_similarity_bin.txt".format(self.lang)), "w"),
        }
        for key in results:
            data = pd.read_csv(results[key], delimiter=" ", header=None, names=["premise", "hypothesis", "score"])
            data.score = (data.score >= threshold)*1
            data.to_csv(result_bin[key], sep=" ", header=None, index=None)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Service to generate embeddings in a given language")
    parser.add_argument("-l", "--lang", required=True, help="set the language")
    args = parser.parse_args()
    mono = Monolingual(lang=args.lang)
    #mono.main(graded=False)
    mono.binarize()
