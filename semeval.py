import copy
import inspect
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
from scripts.parse_data import read

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


def process_fourlang_votes(text_to_4lang, language, data_frame, synonyms, filtering, depth, threshold, blacklist, combine):
    fourlang_votes = []
    for i in tqdm(range(len(data_frame))):
        index = i
        premise = data_frame.premise[index]
        hypothesis = data_frame.hypothesis[index]
        graph_premise = text_to_4lang.process_text(premise, method="expand", depth=0, blacklist=blacklist, black_or_white=filtering)
        connect_synsets(text_to_4lang, graph_premise, synonyms, combine)

        graph_premise = text_to_4lang.process_graph(graph_premise, method="expand", depth=depth, blacklist=blacklist, black_or_white=filtering)

        graph_hypothesis = text_to_4lang.process_text(hypothesis, method="expand", depth=1)
        graph_premise.filter_graph("part")
        pred = asim_jac_nodes(graph_premise, graph_hypothesis)
        if pred >= threshold:
            fourlang_votes.append(1)
        else:
            fourlang_votes.append(0)
    return fourlang_votes


def process_de(data_frame, fourlang_votes):
    preds = []
    for j in tqdm(range(len(data_frame))):
        index = j
        premise = data_frame.premise[index]
        hypothesis = data_frame.hypothesis[index]

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
            ) or fourlang_votes[index] == 1:
            preds.append(1)
        else:
            preds.append(0)

    return preds


def process(language, data_frame, fourlang_votes):
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
        if (set(hyp_syn_names_all) & set(hyper_premise_names_all)) or fourlang_votes[index] == 1:
            preds.append(1)
        else:
            if score == 1:
                print(premise + "\t" + hypothesis)
            preds.append(0)
    return preds


def run(synonyms, filtering, depth, threshold, language, data_type, votes, blacklist, port, combine, wordnet_only = False):
    print("Initializng modules...")
    graded = True if data_type == "graded" else False
    data_frame = read(language, graded=graded)
    supported_languages = ["en", "it", "de"]
    if language not in supported_languages:
        raise Exception("Not supported language")
    text_to_4lang = TextTo4lang(lang=language, port=port)

    if not wordnet_only:
        fourlang_votes = process_fourlang_votes(
            text_to_4lang, language, data_frame, synonyms, filtering, depth, threshold, blacklist, combine)
    else:
        fourlang_votes = len(data_frame) * [0]
    if votes:
        if language == "it" or language == "en":
            preds = process(language, data_frame, fourlang_votes)
        else:
            preds = process_de(data_frame, fourlang_votes)
    else:
        preds = fourlang_votes

    bPrecis, bRecall, bFscore, bSupport = pr(data_frame.score.tolist(), fourlang_votes)

    print("4lang")
    print("Precision: " + str(bPrecis[1]))
    print("Recall: " + str(bRecall[1]))
    print("Fscore: " + str(bFscore[1]))

    tn, fp, fn, tp = cm(data_frame.score.tolist(), fourlang_votes).ravel()
    print("Scores")
    print("TN: " + str(tn))
    print("FP: " + str(fp))
    print("FN: " + str(fn))
    print("TP: " + str(tp))

   
    bPrecis, bRecall, bFscore, bSupport = pr(data_frame.score.tolist(), preds)

    print("Voting")
    print("Precision: " + str(bPrecis[1]))
    print("Recall: " + str(bRecall[1]))
    print("Fscore: " + str(bFscore[1]))

    tn, fp, fn, tp = cm(data_frame.score.tolist(), preds).ravel()
    print("Scores")
    print("TN: " + str(tn))
    print("FP: " + str(fp))
    print("FN: " + str(fn))
    print("TP: " + str(tp))

    with open("semeval_output.txt", "w+") as f:
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
