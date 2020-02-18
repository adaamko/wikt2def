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
import numpy as np


def binary(lang):
    # Start the services
    pid_elmo = subprocess.Popen("{} {} -p 1666".format(
        sys.executable, os.path.join(os.path.dirname(__file__), "elmo_service.py")).split(' '))
    pid_ud = subprocess.Popen("{} {} -p 5005 -l {}".format(
        sys.executable, os.path.join(os.path.dirname(__file__), "../fourlang/service/ud_service.py"), lang).split(' '))
    ud_server_up = False
    while not ud_server_up:
        try:
            requests.head("http://127.0.0.1:5005")
            ud_server_up = True
        except requests.exceptions.ConnectionError:
            time.sleep(5)

    # Initialize objects
    similarity = Similarity(lang)
    text_to_4lang = TextTo4lang(lang)
    lexicon = Lexicon(lang)

    # Initialize similarity lists
    results = {
        "asim_jac_word": open(os.path.join(os.path.dirname(__file__),
                                           "../results/{}/asim_jac_bow.txt".format(lang)), "w"),
        "asim_jac_node": open(os.path.join(os.path.dirname(__file__),
                                           "../results/{}/asim_jac_node.txt".format(lang)), "w"),
        "asim_jac_edge": open(os.path.join(os.path.dirname(__file__),
                                           "../results/{}/asim_jac_edge.txt".format(lang)), "w"),
        "asim_jac_bow_elmo": open(os.path.join(os.path.dirname(__file__),
                                               "../results/{}/asim_jac_bow_elmo.txt".format(lang)), "w"),
        "asim_jac_node_elmo": open(os.path.join(os.path.dirname(__file__),
                                                "../results/{}/asim_jac_node_elmo.txt".format(lang)), "w"),
        "asim_jac_edge_elmo": open(os.path.join(os.path.dirname(__file__),
                                                "../results/{}/asim_jac_edge_elmo.txt".format(lang)), "w")
    }

    # Read the data
    monolingual_data = read(lang, graded=False)

    for index, row in monolingual_data.iterrows():
        premise = row.premise
        hypothesis = row.hypothesis

        graph_premise = text_to_4lang.process_text(premise, True)
        graph_hypothesis = text_to_4lang.process_text(hypothesis, True)
        def_premise = ""
        def_hypothesis = ""
        if premise in lexicon.lexicon:
            def_premise = lexicon.lexicon[premise]
        if hypothesis in lexicon.lexicon:
            def_hypothesis = lexicon.lexicon[hypothesis]
        results["asim_jac_word"].write(" ".join(
            [premise, hypothesis, str(int(np.round(similarity.asim_jac_words(def_premise, def_hypothesis))))])+"\n")
        results["asim_jac_node"].write(" ".join(
            [premise, hypothesis, str(int(np.round(similarity.asim_jac_nodes(graph_premise, graph_hypothesis))))])+"\n")
        results["asim_jac_edge"].write(" ".join(
            [premise, hypothesis, str(int(np.round(similarity.asim_jac_edges(graph_premise, graph_hypothesis))))])+"\n")
        results["asim_jac_bow_elmo"].write(" ".join(
            [premise, hypothesis, str(int(np.round(similarity.asim_jac_bow_elmo(def_premise, def_hypothesis))))])+"\n")
        results["asim_jac_node_elmo"].write(" ".join(
            [premise, hypothesis, str(int(np.round(similarity.asim_jac_nodes_elmo(premise, hypothesis,
                                                                                  graph_premise, graph_hypothesis,
                                                                                  def_premise, def_hypothesis))))])+"\n")
        results["asim_jac_edge_elmo"].write(" ".join(
            [premise, hypothesis, str(int(np.round(similarity.asim_jac_edges_elmo(premise, hypothesis,
                                                                                  graph_premise, graph_hypothesis,
                                                                                  def_premise, def_hypothesis))))])+"\n")
    pid_elmo.terminate()
    pid_ud.terminate()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Service to generate embeddings in a given language")
    parser.add_argument("-l", "--lang", required=True, help="set the language")
    args = parser.parse_args()
    binary(args.lang)
