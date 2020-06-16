from fourlang.text_to_4lang import TextTo4lang
from fourlang.lexicon import Lexicon
from graphviz import Source
from scripts.parse_data import read, read_sherliic, build_graph
from scripts.similarity import Similarity
from tqdm import tqdm
from copy import deepcopy
from argparse import ArgumentParser
import os

parser = ArgumentParser(description = "")
parser.add_argument("-m", "--mode", help="Set data to use for running. Options: sherliic, en, de, it. For sherliic and en the ud_service should run with parameter en, for the german it should be de and for the italian it is it.", default="en", type=str, choices=["sherliic", "en", "it", "de"])


def synonym_graph(graph, graph_root, synonyms):
    syns = [graph]
    for synonym in synonyms:
        graph_copy = deepcopy(graph)
        for edge in graph_copy[0]:
            if edge[1][0] == graph_root:
                edge[1][0] = synonym
            if edge[2][0] == graph_root:
                edge[2][0] = synonym
        syns.append(graph_copy)
    return syns


def read_data(data):
    if data == "sherliic":
        dir_name = os.path.dirname(os.path.abspath(__file__))
        df = read_sherliic(os.path.join(dir_name, "../../sherliic/dev.csv"), os.path.join(dir_name, "../../sherliic/relation_index.tsv"), keep_context=True, just_ab=True)
        data_frame = build_graph(df)
    else:
        data_frame = read(data, graded=False)
    return data_frame


def calculate_output(mode):
    data_frame = read_data(mode)
    
    lang = mode if mode != "sherliic" else "en"
    text_to_4lang = TextTo4lang(lang=lang)
    lexicon = Lexicon(lang=lang)
    similarity = Similarity(with_embedding=False)
    blacklist_dict = {"en": ["in", "on", "of"], "de": ["auf", "in"], "it": ["nel", "su", "di"], "sherliic": []}
    
    with open("{}.txt".format(mode), "w") as f:
        for index in tqdm(range(len(data_frame))):
            premise = data_frame.premise[index]
            hypothesis = data_frame.hypothesis[index]
            score = data_frame.score[index]

            blacklist = blacklist_dict[mode]

            if mode == "sherliic":
                prem_expand = 2
                filt = False
                process_function = text_to_4lang.process_deps
                similarity_function = similarity.asim_jac_edges
                graph_premise = text_to_4lang.process_deps(premise, method="default")
                graph_hypothesis = text_to_4lang.process_deps(hypothesis, method="default")
                syn_premise = [premise]
                syn_hypothesis = [hypothesis]
                premise_root = graph_premise.root.split('_')[0]
                hypothesis_root = graph_hypothesis.root.split('_')[0]
                if premise_root in lexicon.wiktionary_synonyms:
                    syn_premise = synonym_graph(premise, premise_root, lexicon.wiktionary_synonyms[premise_root])
                if hypothesis_root in lexicon.wiktionary_synonyms:
                    syn_hypothesis = synonym_graph(hypothesis, hypothesis_root, lexicon.wiktionary_synonyms[hypothesis_root])
            else:
                prem_expand = 3
                filt = True
                process_function = text_to_4lang.process_text
                similarity_function = similarity.asim_jac_nodes
                syn_premise = [premise] + lexicon.wiktionary_synonyms[premise]
                syn_premise = [hypothesis] + lexicon.wiktionary_synonyms[hypothesis]
            best_match = 0
            for syn_prem in syn_premise:
                for syn_hyp in syn_hypothesis:
                    graph_premise = process_function(syn_prem, method="expand", depth=prem_expand, filt=filt, blacklist=blacklist, black_or_white="black")
                    graph_hypothesis = process_function(syn_hyp, method="expand", depth=1, filt=filt, blacklist=blacklist, black_or_white="black")
                    pred = similarity_function(graph_premise, graph_hypothesis)
                    if pred > best_match:
                        best_match = pred

            """Source(graph_premise.to_dot()).render('nodes_2_1_sherliic_wo_case/{}_{}_premise.gv'.format(
                "-".join(df.premise[index].split(" ")), "-".join(df.hypothesis[index].split(" "))))
            Source(graph_hypothesis.to_dot()).render('nodes_2_1_sherliic_wo_case/{}_{}_hypothesis.gv'.format(
                "-".join(df.premise[index].split(" ")), "-".join(df.hypothesis[index].split(" "))))"""
            f.write("{}\t{}\t{}\t{}\n".format(premise, hypothesis, best_match, score))


if __name__ == "__main__":
    args = parser.parse_args()
    calculate_output(args.mode)
