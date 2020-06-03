import argparse
import copy
import inspect
import math
import re
from collections import defaultdict

import networkx as nx
from graphviz import Source
from networkx.readwrite import json_graph
from nltk.corpus import wordnet as wn
from sklearn.metrics import precision_recall_fscore_support as pr
from sklearn.metrics import confusion_matrix as cm
from tqdm import tqdm

from fourlang.lexicon import Lexicon
from fourlang.text_to_4lang import TextTo4lang
from scripts.parse_data import build_graph, read_sherliic


def clear_node(node):
    """
    Clears the node from the 4lang id parts
    :param node: the text to clear
    :return: the cleared text
    """
    return re.sub(r'_[0-9][0-9]*', '', node)


def asim_jac_edges(graph_premise, graph_hypothesis):
    """
    Asymmetric Jaccard similarity between the edges of the definition graphs
    :param graph_premise: the definition graph of the premise
    :param graph_hypothesis: the definition graph of the hypothesis
    :return: the ratio of overlapping edges per the length of the hypothesis definition
    """
    prem = set([(clear_node(s), clear_node(r), e['color'])
                for (s, r, e) in graph_premise.G.edges(data=True)])
    hyp = set([(clear_node(s), clear_node(r), e['color'])
               for (s, r, e) in graph_hypothesis.G.edges(data=True)])

    hyp_cleared = []
    for triplet in hyp:
        if triplet[0] != "A" and triplet[0] != "B" and triplet[1] != "A" and triplet[1] != "B":
            hyp_cleared.append(triplet)

    hyp = set(hyp_cleared)
    sim = hyp & prem
    if not sim or len(hyp) == 0:
        return 0
    else:
        # return float(len(sim)) / math.sqrt(len(hyp))
        # return len(sim)
        return float(len(sim)) / len(hyp)


def connect_synsets(text_to_4lang, graph, synset_type, combine):
    synsets_wordnet = []
    synsets_v = text_to_4lang.get_synsets(graph.root.split("_")[0])
    synsets_n = text_to_4lang.get_synsets(
            graph.root.split("_")[0], pos="n")
    if synsets_v:
        synsets_top = []
        if len(synsets_v) > 5:
            synsets_top = synsets_v[:5]
        else:
            synsets_top = synsets_v
        synsets_wordnet += synsets_top

    if synsets_n:
        synsets_top = []
        if len(synsets_n) > 5:
            synsets_top = synsets_n[:5]
        else:
            synsets_top = synsets_n
        synsets_wordnet += synsets_top

    wiktionary_synsets = text_to_4lang.lexicon.wiktionary_synonyms[graph.root.split("_")[0]]

    if synset_type == "wordnet" and combine == "SINGLE":
        graph.connect_synsets(synsets_wordnet)
    elif synset_type == "wiktionary" and combine == "SINGLE":
        graph.connect_synsets(wiktionary_synsets)
    elif combine == "OR":
        synsets = list(set(synsets_wordnet).union(set(wiktionary_synsets)))
        graph.connect_synsets(synsets)
    elif combine == "AND":
        synsets = list(set(synsets_wordnet).intersection(set(wiktionary_synsets)))
        graph.connect_synsets(synsets)


def process(text_to_4lang, data_frame, synonyms, depth, threshold, combine, blacklist):
    preds = []
    guesses = []
    for i in tqdm(range(len(data_frame))):
        index = i
        premise = data_frame["premise"][index]
        hypothesis = data_frame["hypothesis"][index]
        score = data_frame.score[index]
        graph_premise = text_to_4lang.process_deps(premise, method="expand", depth=0, blacklist=blacklist, filt=False, black_or_white="")
        connect_synsets(text_to_4lang, graph_premise, synonyms, combine)
        graph_premise = text_to_4lang.process_graph(graph_premise, method="expand", depth=depth, blacklist=blacklist, filt=False, black_or_white="")

        graph_hypothesis = text_to_4lang.process_deps(hypothesis, method="expand", depth=1, blacklist=blacklist, filt=False, black_or_white="")
        pred = asim_jac_edges(graph_premise, graph_hypothesis)
        guesses.append(pred)
        if pred >= threshold:
            preds.append(1)
        else:
            preds.append(0)

    return preds


def run(synonyms, depth, threshold, combine, dataset="dev", blacklist=["in","of","on"]):
    print("Initializng modules...")
    text_to_4lang = TextTo4lang(lang="en")
    data = read_sherliic(
        "data/" + dataset  +".csv", ud_path="data/relation_index.tsv", keep_context=True)
    data_frame = build_graph(data)
    data['premise_text'] = data["prem_argleft"] + " " + \
        data["premise"] + " " + data["prem_argright"]
    data['hyp_text'] = data["hypo_argleft"] + " " + \
        data["hypothesis"] + " " + data["hypo_argright"]
    preds = process(text_to_4lang, data_frame, synonyms, depth, threshold, combine, blacklist)

    bPrecis, bRecall, bFscore, bSupport = pr(data_frame.score.tolist(), preds)

    print("Precision: " + str(bPrecis[1]))
    print("Recall: " + str(bRecall[1]))
    print("Fscore: " + str(bFscore[1]))

    tn, fp, fn, tp = cm(data_frame.score.tolist(), preds).ravel()
    print("Scores")
    print("TN: " + str(tn))
    print("FP: " + str(fp))
    print("FN: " + str(fn))
    print("TP: " + str(tp))

    with open("sherlic_output.txt", "w+") as f:
        for i, pred in enumerate(preds):
            premise = data.premise_text[i]
            hypothesis = data.hyp_text[i]
            f.write(
                str(premise) +
                " " +
                str(hypothesis) +
                " " +
                str(pred) +
                "\n")
