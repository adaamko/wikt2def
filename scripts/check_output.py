import pandas as pd
from graphviz import Source
from fourlang.text_to_4lang import TextTo4lang
from fourlang.lexicon import Lexicon


def read_output(file_path, threshold=1.0):
    print("premise\tdef premise\tpremise edges\thypothesis\tdef hypothesis\thypothesis edges\tpredicted\tgold")
    df = pd.read_csv(file_path, delimiter=" ", header=None, names=["premise", "hypothesis", "predicted", "gold"])
    for row in df.iterrows():
        premise = row[1].premise
        hypothesis = row[1].hypothesis
        predicted = float(row[1].predicted)
        gold = float(row[1].gold)
        if (predicted >= threshold)*1 != gold and gold == 0.0:
            def_premise = premise
            def_hypothesis = hypothesis
            if premise in lexicon.lexicon:
                def_premise = lexicon.lexicon[premise]
            if hypothesis in lexicon.lexicon:
                def_hypothesis = lexicon.lexicon[hypothesis]
            premise_edges = text_to_4lang_en.process_text(premise, True, 3)
            hypothesis_edges = text_to_4lang_en.process_text(hypothesis, True, 1)
            print("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
                premise, def_premise, premise_edges.get_edges(),
                hypothesis, def_hypothesis, hypothesis_edges.get_edges(), predicted, gold))


def compare_graphs(graph_premise, graph_hypothesis):
    hyp_nodes = set(graph_hypothesis.get_nodes())
    prem_nodes = set(graph_premise.get_nodes())
    marked_nodes = hyp_nodes & prem_nodes
    dot_graph_premise = graph_premise.to_dot(marked_nodes)
    dot_graph_hypothesis = graph_hypothesis.to_dot(marked_nodes)
    return Source(dot_graph_premise), Source(dot_graph_hypothesis)


lexicon = Lexicon(lang='en')
text_to_4lang_en = TextTo4lang(lang="en", port=5005)
