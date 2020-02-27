import pandas as pd
from graphviz import Source


def read_output(file_path, threshold=1.0):
    df = pd.read_csv(file_path, delimiter="\t", header=None, names=["premise", "hypothesis", "predicted", "gold"])
    for row in df.iterrows():
        p = row[1].premise.strip(']').strip('[').split(", ")
        premise = [i.strip('\'') for i in p]
        h = row[1].hypothesis.strip(']').strip('[').split(", ")
        hypothesis = [i.strip('\'') for i in h]
        predicted = float(row[1].predicted)
        gold = float(row[1].gold)
        if (predicted >= threshold)*1 != gold and gold == 0.0:
            print("premise: {}\thypothesis: {}\tpredicted: {}\tgold: {}\n".format(premise, hypothesis, predicted, gold))


def compare_graphs(graph_premise, graph_hypothesis):
    hyp_nodes = set(graph_hypothesis.get_nodes())
    prem_nodes = set(graph_premise.get_nodes())
    marked_nodes = hyp_nodes & prem_nodes
    dot_graph_premise = graph_premise.to_dot(marked_nodes)
    dot_graph_hypothesis = graph_hypothesis.to_dot(marked_nodes)
    return Source(dot_graph_premise), Source(dot_graph_hypothesis)


read_output("../nodes_3.txt")
