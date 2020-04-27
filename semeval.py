import copy
from nltk.corpus import wordnet as wn
from collections import defaultdict
from tqdm import tqdm
from scripts.parse_data import read
from graphviz import Source
from fourlang.lexicon import Lexicon
from fourlang.text_to_4lang import TextTo4lang
from networkx.readwrite import json_graph
import networkx as nx
import re
import inspect
import argparse

parser = argparse.ArgumentParser(description="")
parser.add_argument(
    "-l",
    "--lang",
    required=True,
    nargs="+",
    help="the language to run the script on",
    default="en")
parser.add_argument(
    "-t",
    "--type",
    required=True,
    nargs="+",
    help="choose between binary or graded",
    default="binary")


args = parser.parse_args()


dictionary = defaultdict(list)
with open("dictionaries/de_to_en", "r+") as f:
    for line in f:
        line = line.strip().split("\t")
        dictionary[line[1].lower()].append(line[3].lower())

fourlang_votes = []


def clear_node(node):
    """
    Clears the node from the 4lang id parts
    :param node: the text to clear
    :return: the cleared text
    """
    return re.sub(r'_[0-9][0-9]*', '', node)


def asim_jac_nodes(graph_premise, graph_hypothesis):
    prem = set(graph_premise.get_nodes())
    hyp = set(graph_hypothesis.get_nodes())
    prem = set([i.lower() for i in prem])
    hyp = set([i.lower() for i in hyp])
    sim = hyp & prem
    if not sim or len(hyp) == 0:
        return 0
    else:
        return float(len(sim)) / len(hyp)


def process_fourlang_votes(text_to_4lang, language, data_frame):
    fourlang_votes = []
    for i in tqdm(range(len(data_frame))):
        index = i
        premise = data_frame.premise[index]
        hypothesis = data_frame.hypothesis[index]
        if language == "en":
            graph_premise = text_to_4lang.process_text(
                premise, method="expand", depth=3, blacklist=[
                    "in", "of", "on"])  # legyen-e expand
            graph_hypothesis = text_to_4lang.process_text(
                hypothesis, method="expand", depth=1)
            graph_premise.filter_graph("part")
        elif language == "de":
            graph_premise = text_to_4lang.process_text(
                premise, method="expand", depth=3, blacklist=[
                    "in", "auf"])  # legyen-e expand
            graph_hypothesis = text_to_4lang.process_text(
                hypothesis, method="expand", depth=1)
        elif language == "it":
            graph_premise = text_to_4lang.process_text(
                premise, method="expand", depth=3, blacklist=[
                    "di", "su", "il"])  # legyen-e expand
            graph_hypothesis = text_to_4lang.process_text(
                hypothesis, method="expand", depth=1)
        pred = asim_jac_nodes(graph_premise, graph_hypothesis)
        if pred == 1.0:
            fourlang_votes.append(1)
        else:
            fourlang_votes.append(0)


def process_de(data_frame):
    preds = []
    for j in tqdm(range(len(data_frame))):
        index = j
        premise = data_frame_de_graded.premise[index]
        hypothesis = data_frame_de_graded.hypothesis[index]

        hyp_syn_names_all = []
        hyper_premise_names_all = []

        premises = []
        hypothesises = []

        if premise in dictionary:
            premise = dictionary[premise]
            premises += premise
        if hypothesis in dictionary:
            hypothesis = dictionary[hypothesis]
            hypothesises += hypothesis

        for premise in premises:

            premise_syns = wn.synsets(premise)
            """
            if len(premise_syns) > 0 and len(hyp_syns) > 0:
                en_premise = premise_syns[0].lemmas()[0].name()
                en_hyp = hyp_syns[0].lemmas()[0].name()
                fourlang_score = get_4lang_score(en_premise, en_hyp)
            else:
                fourlang_score = 0
            """

            for premise_syn in premise_syns:

                hyperpremise = set(
                    [i for i in premise_syn.closure(lambda s:s.hypernyms())])

                hyper_premise_lemmas = []
                for i in hyperpremise:
                    lemmas = i.lemmas()
                    for lemm in lemmas:
                        hyper_premise_lemmas.append(lemm)

                hyper_premise_names = set([i.name()
                                           for i in hyper_premise_lemmas])
                hyper_premise_names_all += list(hyper_premise_names)

        for hypothesis in hypothesises:
            hyp_syns = wn.synsets(hypothesis)
            for hyp_syn in hyp_syns:
                hyp_syn_lemmas = hyp_syn.lemmas()
                hyp_syn_names = set([i.name() for i in hyp_syn_lemmas])

                hyp_syn_names_all += list(hyp_syn_names)

        if (set(hyp_syn_names_all) & set(hyper_premise_names_all)
                ) or fourlang_votes[index] == '1':
            preds.append(1)
        else:
            preds.append(0)

    return preds


def process(language, data_frame):
    preds = []
    for j in tqdm(range(len(data_frame))):
        index = j
        premise = data_frame.premise[index]
        hypothesis = data_frame.hypothesis[index]
        score = data_frame.score[index]

        hyp_syn_names_all = []
        hyper_premise_names_all = []

        if language == "it":
            premise_syns = wn.synsets(premise, lang="ita")
            hyp_syns = wn.synsets(hypothesis, lang="ita")
        elif language == "en":
            premise_syns = wn.synsets(premise)
            hyp_syns = wn.synsets(hypothesis)

        for premise_syn in premise_syns:

            hyperpremise = set(
                [i for i in premise_syn.closure(lambda s:s.hypernyms())])

            hyper_premise_lemmas = []
            for i in hyperpremise:
                lemmas = i.lemmas()
                for lemm in lemmas:
                    hyper_premise_lemmas.append(lemm)

            hyper_premise_names = set([i.name() for i in hyper_premise_lemmas])
            hyper_premise_names_all += list(hyper_premise_names)

        for hyp_syn in hyp_syns:
            hyp_syn_lemmas = hyp_syn.lemmas()
            hyp_syn_names = set([i.name() for i in hyp_syn_lemmas])

            hyp_syn_names_all += list(hyp_syn_names)

        if (set(hyp_syn_names_all) & set(hyper_premise_names_all)
                ) or fourlang_votes[index] == 1:
            preds.append(1)
        else:
            if score == 1:
                print(premise + "\t" + hypothesis)
            preds.append(0)
    return preds


def main(language, data_type):
    graded = True if data_type == "graded" else False
    data_frame = read(language, graded=graded)
    if language == "en":
        text_to_4lang = TextTo4lang(lang="en", port=5005)
    elif language == "de":
        text_to_4lang = TextTo4lang(lang="de", port=5005)
    elif language == "it":
        text_to_4lang_it = TextTo4lang(lang="it", port=5007)
    else:
        raise Exception("Not supported language")

    fourlang_votes = process_fourlang_votes(
        text_to_4lang, language, data_frame)
    if language == "it" or language == "en":
        preds = process(language, data_frame)
    else:
        preds = process_de(data_frame)

    with open("output.txt", "w+") as f:
        for i, pred in enumerate(preds):
            premise = data_frame.premise[i]
            hypothesis = data_frame.hypothesis[i]
            f.write(
                str(premise) +
                " " +
                str(hypothesis) +
                " " +
                str(pred) +
                "\n")


if __name__ == '__main__':
    main(args.lang[0], args.type[0])
